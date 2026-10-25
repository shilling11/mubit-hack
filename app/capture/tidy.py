"""Tidy a call transcript for the QA analyst, before it's stored and redacted.

1. Echo (two-channel phone calls): each phone's mic also picks up the other person (same room, or
   the other phone's speaker), so one line can show up on both channels at once. The copy with
   fewer words is dropped.
2. Fragments: one speaker's pieces with short pauses between them become one line.
3. Dates: "Nineteenth of December 2004" or "December 19th, 2004" become "19 Dec 2004", the way QA
   writes them. Spoken dates also need digits for the DOB redaction (app/privacy/redact.py) to catch them.
"""
import re

_WORD = re.compile(r"[a-z0-9']+")


def _words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _echoed(u: dict, v: dict, slack_s: float) -> int:
    """How many of u's words v also has at the same moment (an echo is simultaneous; a reply comes later)."""
    theirs = [(x["word"].lower(), x["start"]) for x in v["words"]]
    return sum(any(w["word"].lower() == x and abs(w["start"] - tx) <= slack_s for x, tx in theirs) for w in u["words"])


def drop_echo(utts: list[dict], slack_s: float = 0.5, share: float = 0.6) -> list[dict]:
    """utts carry a "channel" and word timings. Drop a line when most of its words are on the other channel at the
    same moment, in a longer line (ties: the less confident copy). That longer line is the speaker's own mic."""
    keep = []
    for u in utts:
        if not u["text"].strip():
            continue
        others = [v for v in utts if v["channel"] != u["channel"]]
        best = max(others, key=lambda v: _echoed(u, v, slack_s), default=None)
        if u["words"] and best and _echoed(u, best, slack_s) / len(u["words"]) >= share:
            mine, theirs = len(u["words"]), len(best["words"])
            if mine < theirs or (mine == theirs and u["confidence"] < best["confidence"]):
                continue
        keep.append(u)
    return keep


def merge_turns(utts: list[dict], gap_s: float = 2.0, interjection_words: int = 2) -> list[dict]:
    """utts carry a "speaker", sorted by start. One speaker's lines, paused less than gap_s, become one line,
    even across a short interjection from the other side ("Okay." while the customer gives a date of birth)."""
    out: list[dict] = []
    for u in utts:
        i = len(out) - 1
        while i >= 0 and out[i]["speaker"] != u["speaker"] and len(_words(out[i]["text"])) <= interjection_words:
            i -= 1
        prev = out[i] if i >= 0 and out[i]["speaker"] == u["speaker"] else None
        if prev and u["start_s"] - prev["end_s"] <= gap_s:
            n1, n2 = len(_words(prev["text"])), len(_words(u["text"]))
            prev["confidence"] = (prev["confidence"] * n1 + u["confidence"] * n2) / max(1, n1 + n2)
            prev["text"] = f"{prev['text']} {u['text']}"
            prev["end_s"] = u["end_s"]
        else:
            out.append(dict(u))
    return out


_MONTHS = {"jan": "Jan", "feb": "Feb", "mar": "Mar", "apr": "Apr", "may": "May", "jun": "Jun", "jul": "Jul",
           "aug": "Aug", "sep": "Sep", "oct": "Oct", "nov": "Nov", "dec": "Dec"}
_UNITS = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth"]
_ORDINALS = {w: i + 1 for i, w in enumerate(_UNITS)} | {
    "tenth": 10, "eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14, "fifteenth": 15,
    "sixteenth": 16, "seventeenth": 17, "eighteenth": 18, "nineteenth": 19, "twentieth": 20, "thirtieth": 30}
_TENS = {"twenty": 20, "thirty": 30}

_DAY = (r"(?P<{n}>\d{{1,2}}(?:st|nd|rd|th)?|(?:twenty|thirty)[- ]?(?:" + "|".join(_UNITS) + r")|"
        + "|".join(sorted(_ORDINALS, key=len, reverse=True)) + r")")
_MONTH = (r"(?P<{n}>jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?"
          r"|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)")
_DECADES = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
_DIGITS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9}
_SPOKEN_YEAR = (r"(?:nineteen[- ]?)?(?:" + "|".join(_DECADES) + r")(?:[- ]?(?:" + "|".join(_DIGITS) + r"))?")
# A four-digit year, or a two-digit one ('81, or ", 81" / ", eighty-one" at the end of a phrase)
_YEAR = (r"(?:,?\s+(?P<{n}>(?:19|20)\d{{2}}|'\d{{2}}|(?:\d{{2}}|" + _SPOKEN_YEAR + r")(?=\s*(?:[.?!,]|$))))?")
_DATE = re.compile(
    r"\b(?:the\s+)?" + _DAY.format(n="d1") + r"(?:\s+of)?\s+" + _MONTH.format(n="m1") + r"\b" + _YEAR.format(n="y1")
    + r"|\b" + _MONTH.format(n="m2") + r"\s+(?:the\s+)?" + _DAY.format(n="d2") + r"\b" + _YEAR.format(n="y2"),
    re.I)


def _day(s: str) -> int | None:
    s = s.lower().replace("-", " ")
    if s[:2].isdigit() or s[:1].isdigit():
        return int(re.match(r"\d+", s).group())
    if s in _ORDINALS:
        return _ORDINALS[s]
    tens, _, unit = s.partition(" ")
    if not unit:  # "twentyfirst"
        tens, unit = next(((t, s[len(t):]) for t in _TENS if s.startswith(t)), (s, ""))
    return _TENS.get(tens, 0) + _ORDINALS.get(unit, 0) or None


def _year(s: str | None) -> str:
    if not s:
        return ""
    yy = s.lstrip("'")
    if not yy[0].isdigit():  # "eighty-one", "nineteen eighty one"
        words = re.findall(r"[a-z]+", yy.lower().replace("nineteen", ""))
        yy = str(1900 + _DECADES[words[0]] + (_DIGITS[words[1]] if len(words) > 1 else 0))
    if len(yy) == 2:  # a date of birth: 00-12 → 2000s, otherwise 1900s
        yy = ("20" if int(yy) <= 12 else "19") + yy
    return f" {yy}"


def _fmt(m: re.Match) -> str:
    d, mo, y = (m["d1"], m["m1"], m["y1"]) if m["d1"] else (m["d2"], m["m2"], m["y2"])
    day = _day(d)
    if not day or day > 31:
        return m.group(0)
    return f"{day} {_MONTHS[mo[:3].lower()]}{_year(y)}"


def dates(text: str) -> str:
    return _DATE.sub(_fmt, text)
