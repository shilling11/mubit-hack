"""Write Thistle's October calls as the spreadsheet a QA firm receives: one row per line, Excel and CSV.

Usage: python -m scripts.make_batch
Writes data/batches/thistle-october-2026.xlsx and .csv from the practice calls (never the held-out ones,
and never their gold labels). Import it on the Batch page.
"""
import csv
import datetime as dt
import json

from openpyxl import Workbook
from openpyxl.styles import Font

from app.config import CALLS_DIR, DATA

OUT = DATA / "batches"
HEADERS = ["Call ID", "Date", "Agent", "Speaker", "Start", "Text"]


def _weekdays(year: int, month: int) -> list[dt.date]:
    d, days = dt.date(year, month, 1), []
    while d.month == month:
        if d.weekday() < 5:
            days.append(d)
        d += dt.timedelta(days=1)
    return days


def main() -> None:
    calls = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((CALLS_DIR / "practice").glob("*.json"))]
    days = _weekdays(2026, 10)
    rows = []
    for i, c in enumerate(calls):
        # Spread the calls across October's working days, 09:00-17:00
        when = dt.datetime.combine(days[i * len(days) // len(calls)], dt.time(9 + (i * 7) % 8, (i * 13) % 60))
        for u in c["utterances"]:
            s = int(u["start_s"])
            rows.append([c["id"], when.strftime("%d/%m/%Y %H:%M"), c["agent_name"],
                         "Agent" if u["speaker"] == "agent" else "Customer", f"{s // 60}:{s % 60:02d}", u["text"]])
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "thistle-october-2026.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([HEADERS, *rows])
    wb = Workbook()
    ws = wb.active
    ws.title = "October 2026"
    ws.append(HEADERS)
    for r in rows:
        ws.append(r)  # Start stays text ("0:03"), so Excel doesn't read it as hours:minutes
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for col, width in zip("ABCDEF", (10, 18, 12, 11, 8, 110)):
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A2"
    wb.save(OUT / "thistle-october-2026.xlsx")
    print(f"wrote {len(calls)} calls, {len(rows)} lines → {OUT / 'thistle-october-2026.xlsx'} (and .csv)")


if __name__ == "__main__":
    main()
