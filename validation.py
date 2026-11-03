"""Input validation and cleaning for uploaded student datasets."""
from __future__ import annotations

import pandas as pd

ID_HINTS = ["student_id", "studentid", "student id", "id", "roll_no", "roll no",
            "rollno", "roll", "student_name", "student name", "name", "student"]


class ValidationError(Exception):
    """Raised when the uploaded dataset cannot be analysed."""


def load_file(file) -> pd.DataFrame:
    """Read a CSV or Excel upload (or a path) into a DataFrame."""
    name = getattr(file, "name", str(file)).lower()
    try:
        if name.endswith(".csv"):
            return pd.read_csv(file)
        if name.endswith((".xlsx", ".xls")):
            return pd.read_excel(file)
    except Exception as exc:  # noqa: BLE001
        raise ValidationError(f"Could not read the file: {exc}") from exc
    raise ValidationError("Unsupported file type. Please upload a .csv or .xlsx file.")


def validate_dataframe(df: pd.DataFrame):
    """Validate and clean a dataset.

    Returns (clean_df, id_columns, subject_columns, warnings).
    Raises ValidationError for problems that make analysis impossible.
    """
    warnings: list[str] = []
    if df is None or df.empty:
        raise ValidationError("The dataset is empty.")

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    if df.empty:
        raise ValidationError("The dataset has no data rows.")

    lowered = {c: c.lower().replace("-", "_") for c in df.columns}
    id_cols = [c for c in df.columns if lowered[c] in ID_HINTS]
    if not id_cols:
        raise ValidationError(
            "No student identifier column found. Add a column such as "
            "'Student ID', 'Roll No' or 'Name'.")

    candidates = [c for c in df.columns if c not in id_cols]
    subject_cols = []
    for col in candidates:
        numeric = pd.to_numeric(df[col], errors="coerce")
        # treat as subject if at least half of the non-blank cells are numeric
        non_blank = df[col].notna().sum()
        if non_blank and numeric.notna().sum() / non_blank >= 0.5:
            bad = df[col].notna() & numeric.isna()
            if bad.any():
                warnings.append(f"'{col}': {int(bad.sum())} non-numeric value(s) treated as missing.")
            df[col] = numeric
            subject_cols.append(col)
    if not subject_cols:
        raise ValidationError("No numeric subject columns found.")
    if len(subject_cols) == 1:
        warnings.append("Only one subject column found; rankings and comparisons are limited.")

    marks = df[subject_cols]
    out_of_range = ((marks < 0) | (marks > 100)).sum().sum()
    if out_of_range:
        raise ValidationError(f"{int(out_of_range)} mark(s) are outside the valid 0-100 range.")

    missing = int(marks.isna().sum().sum())
    if missing:
        warnings.append(f"{missing} blank mark(s) found; averages use the available subjects only.")
    all_blank = marks.isna().all(axis=1)
    if all_blank.any():
        warnings.append(f"{int(all_blank.sum())} student(s) have no marks and were removed.")
        df = df[~all_blank]

    dup = df.duplicated(subset=id_cols, keep=False)
    if dup.any():
        warnings.append(f"{int(dup.sum())} row(s) share duplicate student identifiers.")

    return df.reset_index(drop=True), id_cols, subject_cols, warnings
