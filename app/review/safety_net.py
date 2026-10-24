"""Keyword safety net, independent of the model (README §4.5).

If a customer line contains a vulnerability or complaint cue but the model
marked the matching item "na" (doesn't apply), the call goes to a human.
Cues are deliberately broad: a false alarm costs a minute of analyst time,
a miss costs a customer.
"""
import re

VULNERABILITY_CUES = [
    r"hospital", r"\bill\b", r"illness", r"cancer", r"surgery", r"operation", r"diagnos", r"chemo",
    r"depress", r"anxiety", r"mental health", r"panic", r"stress(ed)?\b",
    r"passed away", r"\bdied\b", r"death", r"funeral", r"bereave", r"widow", r"lost my (husband|wife|partner|mum|dad|mother|father|son|daughter)",
    r"lost my job", r"made redundant", r"redundan", r"unemployed", r"divorce", r"separated", r"carer", r"caring for",
    r"can't afford", r"cannot afford", r"struggling", r"in debt", r"behind on", r"food bank", r"no money",
    r"confus", r"don't understand", r"hard of hearing", r"english isn't",
]
COMPLAINT_CUES = [
    r"not happy", r"unhappy", r"unacceptable", r"complain", r"ridiculous", r"disgust", r"fed up", r"furious",
    r"angry", r"upset", r"not fair", r"unfair", r"rip.?off", r"want (my|the) money back", r"refund", r"nobody told me",
    r"terrible service", r"appalling",
]
_VULN = re.compile("|".join(VULNERABILITY_CUES), re.I)
_COMPLAINT = re.compile("|".join(COMPLAINT_CUES), re.I)


def check(utterances: list[dict], items: dict[str, dict]) -> list[str]:
    """Return human-readable reasons to send the call to an analyst."""
    reasons = []
    customer = [u for u in utterances if u["speaker"] == "customer"]
    if items["C2"]["answer"] == "na":
        for u in customer:
            m = _VULN.search(u["text"])
            if m:
                reasons.append(f"safety net: vulnerability cue “{m.group(0)}” at {u['start_s']:.0f}s, but C2 marked not applicable")
                break
    if items["C1"]["answer"] == "na":
        for u in customer:
            m = _COMPLAINT.search(u["text"])
            if m:
                reasons.append(f"safety net: complaint cue “{m.group(0)}” at {u['start_s']:.0f}s, but C1 marked not applicable")
                break
    return reasons
