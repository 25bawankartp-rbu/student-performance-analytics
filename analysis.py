"""Analytics for student performance."""
from __future__ import annotations

import numpy as np
import pandas as pd


def student_table(df, id_cols, subject_cols) -> pd.DataFrame:
    """Per-student average, median, rank, and strongest/weakest subject."""
    marks = df[subject_cols]
    out = df[id_cols].copy()
    out["Average"] = marks.mean(axis=1).round(2)
    out["Median"] = marks.median(axis=1).round(2)
    out["Highest"] = marks.max(axis=1)
    out["Lowest"] = marks.min(axis=1)
    out["Best Subject"] = marks.idxmax(axis=1)
    out["Weakest Subject"] = marks.idxmin(axis=1)
    out["Rank"] = out["Average"].rank(method="min", ascending=False).astype(int)
    return out.sort_values(["Rank"] + id_cols).reset_index(drop=True)


def subject_table(df, subject_cols) -> pd.DataFrame:
    m = df[subject_cols]
    res = pd.DataFrame({
        "Subject": subject_cols,
        "Average": m.mean().round(2).values,
        "Median": m.median().round(2).values,
        "Highest": m.max().values,
        "Lowest": m.min().values,
    })
    return res.sort_values("Average", ascending=False).reset_index(drop=True)


def below_threshold_mask(df, subject_cols, threshold) -> pd.Series:
    return (df[subject_cols] < threshold).any(axis=1)


def class_stats(df, subject_cols, threshold) -> dict:
    avgs = df[subject_cols].mean(axis=1)
    subj = df[subject_cols].mean()
    # pass = at least threshold in every subject (blank marks ignored)
    passed = ~below_threshold_mask(df, subject_cols, threshold)
    return {
        "total_students": int(len(df)),
        "num_subjects": len(subject_cols),
        "class_average": round(float(avgs.mean()), 2),
        "class_median": round(float(avgs.median()), 2),
        "highest_average": round(float(avgs.max()), 2),
        "lowest_average": round(float(avgs.min()), 2),
        "std_dev": round(float(np.std(avgs, ddof=0)), 2),
        "pass_rate": round(float(passed.mean() * 100), 1),
        "strongest_subject": subj.idxmax(),
        "weakest_subject": subj.idxmin(),
    }


def support_list(df, id_cols, subject_cols, threshold) -> pd.DataFrame:
    """Students with at least one subject below the threshold."""
    mask = below_threshold_mask(df, subject_cols, threshold)
    flagged = df[mask]
    rows = []
    for _, r in flagged.iterrows():
        low = {s: r[s] for s in subject_cols if pd.notna(r[s]) and r[s] < threshold}
        row = {c: r[c] for c in id_cols}
        row["Average"] = round(float(r[subject_cols].mean()), 2)
        row["Subjects Below Threshold"] = ", ".join(f"{k} ({v:g})" for k, v in low.items())
        row["Count"] = len(low)
        rows.append(row)
    res = pd.DataFrame(rows, columns=id_cols + ["Average", "Subjects Below Threshold", "Count"])
    return res.sort_values(["Count", "Average"], ascending=[False, True]).reset_index(drop=True)


def grade_band(avg: float) -> str:
    if avg >= 90: return "A+ (90-100)"
    if avg >= 80: return "A (80-89)"
    if avg >= 70: return "B (70-79)"
    if avg >= 60: return "C (60-69)"
    if avg >= 40: return "D (40-59)"
    return "F (<40)"


def insights(stats, support_df, threshold) -> list[str]:
    n = stats["total_students"]
    out = [
        f"The class average is {stats['class_average']} with a median of {stats['class_median']}.",
        f"{stats['strongest_subject']} is the strongest subject and {stats['weakest_subject']} is the weakest.",
        f"{stats['pass_rate']}% of students scored at least {threshold} in every subject.",
    ]
    if len(support_df):
        out.append(f"{len(support_df)} of {n} students are below {threshold} in at least one subject.")
    else:
        out.append(f"No student is below {threshold} in any subject.")
    return out
