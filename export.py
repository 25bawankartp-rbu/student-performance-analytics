"""CSV and Excel report generation."""
from __future__ import annotations

from io import BytesIO

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def _style(ws):
    fill = PatternFill("solid", fgColor="1F4E79")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = fill
        cell.alignment = Alignment(horizontal="center")
    for i, col in enumerate(ws.columns, 1):
        width = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws.column_dimensions[get_column_letter(i)].width = min(max(width + 2, 10), 45)
    ws.freeze_panes = "A2"


def build_excel(overview: dict, rankings, subjects, support, raw) -> bytes:
    buf = BytesIO()
    ov = pd.DataFrame({"Metric": [k.replace("_", " ").title() for k in overview],
                       "Value": list(overview.values())})
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        ov.to_excel(xw, sheet_name="Overview", index=False)
        rankings.to_excel(xw, sheet_name="Rankings", index=False)
        subjects.to_excel(xw, sheet_name="Subject Averages", index=False)
        support.to_excel(xw, sheet_name="Support List", index=False)
        raw.to_excel(xw, sheet_name="Uploaded Data", index=False)
        for ws in xw.book.worksheets:
            _style(ws)
    return buf.getvalue()
