"""Generate synthetic call transcripts, label-first (README §9).

1. Build a scenario spec per call (seeded, reproducible): the situation, any
   vulnerability, and what the colleague does right or wrong on each scorecard
   item. The spec IS the gold label.
2. Ask Mubit (task data.generate, record=metadata, never trained on) to write
   a natural transcript that follows the spec exactly.
3. Write data/calls/<split>/<id>.json, append held-out labels to
   data/eval/gold.jsonl, and add the synthetic customers to data/customers.json
   (so their names are redacted).

Usage: python -m scripts.generate_calls [--practice 80] [--heldout 25] [--only-missing]
Then: python -m scripts.import_calls
"""
import argparse
import json
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app import db
from app.config import CALLS_DIR, CUSTOMERS_PATH, EVAL_DIR, MAX_PARALLEL
from app.llm import mubit_client

SYSTEM = """You write realistic, synthetic UK retail bank phone call transcripts used to test a call quality-assurance system.

You are given a scenario spec. Write the call between AGENT (a Thistle Bank colleague) and CUSTOMER so that it follows every REQUIRED BEHAVIOUR exactly, including the mistakes. Do not fix the colleague's mistakes and do not add extra mistakes.

Style: natural spoken British English, the way people really talk on the phone (short turns, some hesitation, no stage directions, no narration). 10 to 22 lines. Start with the colleague answering the call. Invent plausible specific details (amounts, dates, merchant names, dates of birth, addresses) where needed. All people and details are fictional. Never mention scorecards, compliance or QA."""

SCHEMA = {
    "type": "object",
    "properties": {
        "utterances": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"speaker": {"type": "string", "enum": ["agent", "customer"]}, "text": {"type": "string"}},
                "required": ["speaker", "text"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["utterances"],
    "additionalProperties": False,
}

SITUATIONS = [
    {"key": "overdraft_fees", "desc": "was charged unarranged overdraft fees", "payment": False, "account": True},
    {"key": "card_unrecognised", "desc": "has a card payment they don't recognise", "payment": True, "account": True},
    {"key": "dd_twice", "desc": "had a direct debit taken twice", "payment": True, "account": True},
    {"key": "transfer_late", "desc": "sent a bank transfer that arrived days late, so they missed a rent payment", "payment": True, "account": True},
    {"key": "mortgage_date", "desc": "had a mortgage payment taken on the wrong date", "payment": False, "account": True},
    {"key": "app_outage", "desc": "couldn't pay a bill on time because the mobile app was down", "payment": False, "account": True},
    {"key": "rate_cut", "desc": "had their savings interest rate cut without noticing any letter", "payment": False, "account": True},
    {"key": "loan_declined", "desc": "had a loan application declined with no explanation", "payment": False, "account": True},
    {"key": "scam", "desc": "transferred money to someone pretending to be from the bank", "payment": True, "account": True},
    {"key": "branch_waits", "desc": "is frustrated that their branch closed and phone waits are long", "payment": False, "account": False},
    {"key": "lost_card", "desc": "needs a replacement for a lost card", "payment": False, "account": True, "complaint": False},
    {"key": "address_change", "desc": "wants to update their address", "payment": False, "account": True, "complaint": False},
    {"key": "opening_hours", "desc": "is asking about branch opening hours", "payment": False, "account": False, "complaint": False},
]

VULN = {
    "health": ["mentions they've just come out of hospital", "mentions they're having chemotherapy at the moment",
               "mentions their anxiety has been really bad lately", "mentions they had an operation last month"],
    "life_event": ["mentions their partner passed away recently", "mentions they lost their job two weeks ago",
                   "mentions they're caring for their mum full time", "mentions they're going through a divorce"],
    "resilience": ["says they can't afford this, they've got nothing left until payday",
                   "says they're already behind on a couple of bills"],
    "capability": ["says they don't really understand online banking and their son normally does it",
                   "seems confused and asks the colleague to repeat things"],
}

FIRST = ["Amira", "Callum", "Priyanka", "Gareth", "Siobhan", "Tobias", "Yasmin", "Declan", "Harriet", "Kwame", "Lucia",
         "Rhys", "Bronwen", "Imran", "Niamh", "Oskar", "Fiona", "Tariq", "Morag", "Ewan", "Leanne", "Jasper", "Aoife",
         "Rohan", "Isla", "Bartek", "Eilidh", "Femi", "Carys", "Ruairi"]
LAST = ["Pemberton", "Achebe", "MacLeod", "Kowalski", "Fitzgerald", "Okonkwo", "Rahman", "Lindqvist", "Thornbury",
        "Delacroix", "Ndlovu", "Ferreira", "Carmichael", "Haddad", "Ellingham", "Sutherland", "Varga", "Oyelaran",
        "Whitlock", "Quigley"]
AGENTS = ["Sam", "Jordan", "Priya", "Marcus", "Hannah", "Liam", "Zara", "Owen"]


def behaviour(item: str, answer: str, s: dict) -> str | None:
    timescale = "15 business days" if s["payment"] else "8 weeks"
    wrong = "8 weeks" if s["payment"] else "5 working days"
    t = {
        ("C1", "yes"): "The colleague clearly says they are logging this as a complaint (and may give a reference or explain the complaints process).",
        ("C1", "no"): "The customer is clearly unhappy about the bank (they may never use the word 'complaint'), but the colleague treats it as a routine query and never logs or raises it as a complaint" + (" (they might say they'll put a note on the account instead)." if s["subtle"] else "."),
        ("C1", "na"): "The customer is not dissatisfied with the bank at all.",
        ("C2", "yes"): f"The customer {s['vuln_cue']}. The colleague acknowledges it and offers specific support, such as the Financial Support team or extra time.",
        ("C2", "no"): f"The customer {s['vuln_cue']} in passing. The colleague " + ("says they're sorry to hear it but offers no support at all." if s["subtle"] else "ignores it and offers no support."),
        ("C3", "yes"): "The colleague makes no promise about any outcome and says nothing misleading.",
        ("C3", "no"): "Before anything has been investigated, the colleague promises or strongly implies the outcome (for example that the money will be refunded or returned).",
        ("C4", "yes"): "Before discussing any account details, the colleague verifies identity with at least two pieces of information (for example full name, date of birth, first line of address).",
        ("C4", "no"): "The colleague discusses specific account details (a balance, a fee or a transaction) BEFORE verifying identity" + (", and only checks identity afterwards." if s["subtle"] else ", and never properly verifies identity."),
        ("S1", "yes"): f"Near the end, the colleague explains exactly what happens next and gives the timescale: a full written response within {timescale}." if s["complaint"] else "The colleague explains clearly what happens next.",
        ("S1", "no"): (f"The colleague tells the customer they'll hear back within {wrong} (this is the wrong timescale)." if s["wrong_timescale"] else "The colleague is vague about next steps, e.g. 'someone will be in touch', with no timescale."),
        ("S1", "na"): None,
        ("S2", "yes"): "The colleague checks the customer has understood, e.g. by summarising and asking if that makes sense.",
        ("S2", "no"): "The colleague never checks whether the customer understood.",
        ("S3", "yes"): None,
        ("S3", "no"): None if s["wrong_timescale"] else "The colleague states something inaccurate about the bank's fees or rules (for example that fees can never be refunded).",
        ("S4", "yes"): "The colleague is courteous, patient and empathetic.",
        ("S4", "no"): "The colleague sounds rushed and dismissive (short answers, no warmth), without being openly rude.",
        ("S5", "yes"): "The colleague takes ownership and agrees a specific follow-up: who will do what, and by when.",
        ("S5", "no"): "The colleague doesn't take ownership or agree any specific follow-up.",
        ("S5", "na"): None,
    }
    return t.get((item, answer))


def make_spec(i: int, split: str, rng: random.Random) -> dict:
    sit = rng.choice(SITUATIONS)
    complaint = sit.get("complaint", True)
    vuln_driver = rng.choice(list(VULN)) if rng.random() < 0.45 else None
    s = {
        "id": f"{'p' if split == 'practice' else 'h'}{i:03d}", "split": split, "situation": sit["key"],
        "situation_desc": sit["desc"], "payment": sit["payment"], "account": sit["account"], "complaint": complaint,
        "vulnerability": vuln_driver, "vuln_cue": rng.choice(VULN[vuln_driver]) if vuln_driver else None,
        "customer": f"{rng.choice(FIRST)} {rng.choice(LAST)}", "agent": rng.choice(AGENTS),
        "subtle": rng.random() < 0.5, "wrong_timescale": False,
    }
    g = {}
    g["C1"] = "na" if not complaint else ("no" if rng.random() < 0.4 else "yes")
    g["C2"] = "na" if not vuln_driver else ("no" if rng.random() < 0.45 else "yes")
    g["C3"] = "no" if rng.random() < (0.3 if complaint else 0.08) else "yes"
    g["C4"] = "na" if not sit["account"] else ("no" if rng.random() < 0.25 else "yes")
    if complaint:
        g["S1"] = "no" if rng.random() < 0.4 else "yes"
        s["wrong_timescale"] = g["S1"] == "no" and rng.random() < 0.5
    else:
        g["S1"] = "na" if rng.random() < 0.5 else "yes"
    g["S2"] = "no" if rng.random() < 0.35 else "yes"
    g["S3"] = "no" if s["wrong_timescale"] or rng.random() < 0.08 else "yes"
    g["S4"] = "no" if rng.random() < 0.2 else "yes"
    g["S5"] = ("no" if rng.random() < 0.3 else "yes") if complaint else ("na" if rng.random() < 0.5 else "yes")
    s["gold"] = g
    return s


def user_message(s: dict) -> str:
    lines = [
        f"SCENARIO: The customer, {s['customer']}, {s['situation_desc']}."
        + (" They are unhappy with the bank about it." if s["complaint"] else " They are not unhappy with the bank."),
        f"COLLEAGUE: {s['agent']} at Thistle Bank.",
        "REQUIRED BEHAVIOURS:",
    ]
    for item, ans in s["gold"].items():
        b = behaviour(item, ans, s)
        if b:
            lines.append(f"- {b}")
    if not s["vulnerability"]:
        lines.append("- The customer mentions nothing about health, bereavement, money worries or difficulty understanding.")
    if not s["account"]:
        lines.append("- No account-specific details are discussed (it's a general enquiry).")
    return "\n".join(lines)


def timestamps(utts: list[dict]) -> list[dict]:
    t, out = 0.0, []
    for u in utts:
        dur = max(1.2, len(u["text"].split()) / 2.6)
        out.append({"speaker": u["speaker"], "text": u["text"].strip(), "start_s": round(t, 1), "end_s": round(t + dur, 1)})
        t += dur + 0.5
    return out


def generate(spec: dict) -> dict:
    res = mubit_client.call("data.generate", SYSTEM, user_message(spec), SCHEMA, record="metadata", reasoning_effort="low")
    utts = [u for u in res["output"]["utterances"] if u["text"].strip()]
    if utts and utts[0]["speaker"] != "agent":
        raise ValueError("transcript must start with the colleague")
    return {"id": spec["id"], "agent_name": spec["agent"], "spec": {k: v for k, v in spec.items() if k != "gold"},
            "gold": spec["gold"], "utterances": timestamps(utts)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--practice", type=int, default=80)
    ap.add_argument("--heldout", type=int, default=25)
    ap.add_argument("--only-missing", action="store_true", help="skip calls whose file already exists")
    args = ap.parse_args()
    db.init()
    specs = [make_spec(i, "practice", random.Random(1000 + i)) for i in range(1, args.practice + 1)]
    specs += [make_spec(i, "heldout", random.Random(9000 + i)) for i in range(1, args.heldout + 1)]
    todo = [s for s in specs if not (args.only_missing and (CALLS_DIR / s["split"] / f"{s['id']}.json").exists())]
    print(f"generating {len(todo)} calls through Mubit (data.generate, record=metadata)…")

    def one(s):
        for attempt in range(2):
            try:
                return s, generate(s)
            except Exception as exc:  # retry once, then report
                err = exc
        return s, err

    done = 0
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        for s, out in pool.map(one, todo):
            if isinstance(out, Exception):
                print(f"  {s['id']}: FAILED {str(out)[:120]}")
                continue
            path = CALLS_DIR / s["split"] / f"{s['id']}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
            done += 1
    print(f"wrote {done} transcripts")

    # Gold labels for held-out calls (spec-derived; check them by hand)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    gold = []
    for p in sorted((CALLS_DIR / "heldout").glob("*.json")):
        c = json.loads(p.read_text(encoding="utf-8"))
        gold.append({"call_id": c["id"], "items": c["gold"], "complaint": c["spec"]["complaint"],
                     "vulnerability": bool(c["spec"]["vulnerability"]), "situation": c["spec"]["situation"]})
    (EVAL_DIR / "gold.jsonl").write_text("\n".join(json.dumps(g) for g in gold) + "\n", encoding="utf-8")
    print(f"wrote {len(gold)} gold labels to data/eval/gold.jsonl")

    # Synthetic customers, so their names get redacted
    customers = json.loads(CUSTOMERS_PATH.read_text(encoding="utf-8"))
    known = {c["name"] for c in customers}
    for s in specs:
        if s["customer"] not in known:
            customers.append({"id": f"SYN-{s['id']}", "name": s["customer"], "note": "synthetic"})
            known.add(s["customer"])
    CUSTOMERS_PATH.write_text(json.dumps(customers, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
