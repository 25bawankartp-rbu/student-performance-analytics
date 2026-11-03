"""Student Analysis System - multi-section Streamlit dashboard."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import analysis as an
import export as ex
import validation as vd

st.set_page_config(page_title="Student Analysis System", page_icon="🎓", layout="wide")

BG, PANEL, TEXT, MUTED, LINE = "#0e1117", "#161b26", "#e8ecf3", "#9aa5b8", "#262d3d"
BLUE, GREEN, YELLOW, RED = "#4da3ff", "#3ecf8e", "#ffd34d", "#ff6b6b"
SECTIONS = ["Overview", "Charts", "Rankings", "Support List", "Reports"]

st.markdown(f"""
<style>
.block-container {{padding-top: 1.4rem; max-width: 1200px;}}
header[data-testid="stHeader"] {{background: transparent;}}

/* header */
.hero {{padding: .2rem 0 1rem 0; margin-bottom: .8rem; border-bottom: 1px solid {LINE};}}
.hero .t {{font-size: 1.6rem; font-weight: 700; color: {TEXT};}}
.hero .t span {{color: {BLUE};}}
.hero .d {{color: {MUTED}; font-size: .9rem; margin-top: .1rem;}}

/* top navigation bar */
div[role="radiogroup"] {{
  display: flex; gap: .3rem; background: {PANEL}; padding: .35rem;
  border-radius: 12px; border: 1px solid {LINE}; flex-wrap: wrap;
}}
div[role="radiogroup"] > label {{
  flex: 1; justify-content: center; padding: .5rem .9rem; border-radius: 9px;
  cursor: pointer; margin: 0; transition: background .15s;
}}
div[role="radiogroup"] > label:hover {{background: #1f2736;}}
div[role="radiogroup"] > label > div:first-child {{display: none;}}
div[role="radiogroup"] > label:has(input:checked) {{background: {BLUE};}}
div[role="radiogroup"] > label:has(input:checked) p {{color: #08111f; font-weight: 700;}}
div[role="radiogroup"] p {{font-size: .95rem; margin: 0;}}

/* metric cards */
.card {{background: {PANEL}; border: 1px solid {LINE}; border-top: 3px solid {BLUE};
        border-radius: 12px; padding: .9rem 1.1rem;}}
.card h4 {{margin: 0; font-size: .75rem; color: {MUTED}; font-weight: 600;
           text-transform: uppercase; letter-spacing: .05em;}}
.card .v {{font-size: 1.7rem; font-weight: 700; color: {TEXT}; line-height: 1.35;}}
.card .s {{font-size: .78rem; color: {MUTED};}}
.insight {{background: {PANEL}; border-left: 3px solid {BLUE}; padding: .55rem 1rem;
           border-radius: 8px; margin-bottom: .45rem;}}

/* chart boxes */
div[data-testid="stVerticalBlockBorderWrapper"] {{background: {PANEL}; border-color: {LINE} !important;
                                                  border-radius: 12px;}}
.ctitle {{font-size: 1.05rem; font-weight: 700; color: {TEXT};}}
.ccap {{font-size: .82rem; color: {MUTED}; margin: .1rem 0 .5rem 0;}}
.pill {{display: inline-block; font-size: .68rem; font-weight: 700; padding: .1rem .55rem;
        border-radius: 99px; margin-left: .5rem; vertical-align: middle;
        background: #1f2c44; color: {BLUE}; letter-spacing: .03em;}}

/* empty state */
.empty {{text-align: center; padding: 3.5rem 1rem; background: {PANEL}; border: 1px dashed #36405a;
         border-radius: 16px; margin-top: 1rem;}}
.empty .big {{font-size: 3rem;}}
.empty .h {{font-size: 1.3rem; font-weight: 700; color: {TEXT}; margin: .3rem 0;}}
.empty .p {{color: {MUTED}; max-width: 520px; margin: 0 auto;}}
</style>
""", unsafe_allow_html=True)


def card(col, title, value, sub=""):
    col.markdown(f'<div class="card"><h4>{title}</h4><div class="v">{value}</div>'
                 f'<div class="s">{sub}</div></div>', unsafe_allow_html=True)


def chart_head(title, caption, tag):
    st.markdown(f'<div class="ctitle">{title}<span class="pill">{tag}</span></div>'
                f'<div class="ccap">{caption}</div>', unsafe_allow_html=True)


def style_ax(fig, ax):
    fig.patch.set_facecolor(PANEL)
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=TEXT)
    for sp in ax.spines.values():
        sp.set_color("#3a4358")
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)


def show(fig):
    fig.tight_layout()
    st.pyplot(fig, width="stretch")
    plt.close(fig)


# ------------------------------------------------------------------ header
st.markdown('<div class="hero"><div class="t">🎓 Student <span>Analysis System</span></div>'
            '<div class="d">Upload marks, explore class performance, rank students and export reports.</div></div>',
            unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Data & Settings")
    upload = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])
    threshold = st.slider("Support / pass threshold", 0, 100, 40,
                          help="Students below this in any subject go on the support list.")

# ------------------------------------------------------------------ empty state
if upload is None:
    st.markdown("""
    <div class="empty">
      <div class="big">📂</div>
      <div class="h">No dataset uploaded yet</div>
      <div class="p">Upload a CSV or Excel file from the sidebar to see the analysis.
      Your file needs a student ID or name column and numeric subject columns with marks from 0 to 100.</div>
    </div>""", unsafe_allow_html=True)
    try:
        sample = Path(__file__).with_name("students.csv").read_bytes()
        st.write("")
        st.download_button("⬇️ Download a sample file to try", sample, "students_sample.csv", "text/csv")
    except Exception:  # noqa: BLE001
        pass
    st.stop()

# ------------------------------------------------------------------ data
try:
    raw = vd.load_file(upload)
    df, id_cols, subjects, warns = vd.validate_dataframe(raw)
except vd.ValidationError as e:
    st.error(f"❌ {e}")
    st.stop()

stats = an.class_stats(df, subjects, threshold)
ranks = an.student_table(df, id_cols, subjects)
subj_tbl = an.subject_table(df, subjects)
support = an.support_list(df, id_cols, subjects, threshold)

# ------------------------------------------------------------------ top nav
page = st.radio("Navigation", SECTIONS, horizontal=True, label_visibility="collapsed")
st.write("")
for w in warns:
    st.warning(w)

# ================================================================== OVERVIEW
if page == SECTIONS[0]:
    st.subheader("Class Overview")
    c = st.columns(4)
    card(c[0], "Total Students", stats["total_students"], f"{stats['num_subjects']} subjects")
    card(c[1], "Class Average", stats["class_average"], f"Median {stats['class_median']}")
    card(c[2], "Pass Rate", f"{stats['pass_rate']}%", f"≥ {threshold} in every subject")
    card(c[3], "Need Support", len(support), f"below {threshold} in ≥ 1 subject")
    st.write("")
    c = st.columns(4)
    card(c[0], "Highest Average", stats["highest_average"])
    card(c[1], "Lowest Average", stats["lowest_average"])
    card(c[2], "Strongest Subject", stats["strongest_subject"])
    card(c[3], "Weakest Subject", stats["weakest_subject"])

    st.write("")
    st.subheader("Key Insights")
    for line in an.insights(stats, support, threshold):
        st.markdown(f'<div class="insight">{line}</div>', unsafe_allow_html=True)

    st.subheader("Data Preview")
    st.dataframe(df.head(15), width="stretch", hide_index=True)
    st.caption(f"Showing 15 of {len(df)} rows · Identifier column(s): {', '.join(id_cols)} · "
               f"Subjects: {', '.join(subjects)}")

# ================================================================== CHARTS
elif page == SECTIONS[1]:
    st.subheader("Visual Analysis")
    st.caption("Each box below is one chart. The tag next to the title tells you what the chart is about.")

    left, right = st.columns(2)
    with left, st.container(border=True):
        chart_head("1. Subject Averages", "Class average mark in each subject.", "BY SUBJECT")
        d = subj_tbl.sort_values("Average")
        fig, ax = plt.subplots(figsize=(6, 3.8))
        bars = ax.barh(d["Subject"], d["Average"], color=BLUE)
        for b, v in zip(bars, d["Average"]):
            ax.text(v + 1, b.get_y() + b.get_height() / 2, f"{v:.1f}", va="center", color=TEXT, fontsize=9)
        ax.set_xlim(0, 100)
        ax.set_xlabel("Average mark")
        style_ax(fig, ax)
        show(fig)

    with right, st.container(border=True):
        chart_head("2. Distribution of Student Averages",
                   "How many students fall in each average-mark range. Dashed line = class average.",
                   "BY STUDENT")
        fig, ax = plt.subplots(figsize=(6, 3.8))
        ax.hist(ranks["Average"], bins=10, range=(0, 100), color=GREEN, edgecolor=PANEL)
        ax.axvline(stats["class_average"], color=YELLOW, linestyle="--", linewidth=2,
                   label=f"Class average {stats['class_average']}")
        ax.set_xlabel("Student average mark")
        ax.set_ylabel("Number of students")
        ax.legend(facecolor=PANEL, edgecolor="#3a4358", labelcolor=TEXT)
        style_ax(fig, ax)
        show(fig)

    left, right = st.columns(2)
    with left, st.container(border=True):
        chart_head("3. Grade Bands", "Number of students in each grade band, based on their overall average.",
                   "BY STUDENT")
        order = ["A+ (90-100)", "A (80-89)", "B (70-79)", "C (60-69)", "D (40-59)", "F (<40)"]
        bands = ranks["Average"].map(an.grade_band).value_counts().reindex(order, fill_value=0)
        fig, ax = plt.subplots(figsize=(6, 3.8))
        ax.bar(bands.index, bands.values, color=[GREEN, GREEN, BLUE, BLUE, YELLOW, RED])
        for i, v in enumerate(bands.values):
            ax.text(i, v + 0.1, str(v), ha="center", color=TEXT)
        ax.set_ylabel("Number of students")
        plt.setp(ax.get_xticklabels(), rotation=25, ha="right")
        style_ax(fig, ax)
        show(fig)

    with right, st.container(border=True):
        chart_head("4. Passing vs Needs Support",
                   f"Share of the class at or above {threshold} in every subject, versus the rest.",
                   "WHOLE CLASS")
        n_support = len(support)
        n_pass = stats["total_students"] - n_support
        fig, ax = plt.subplots(figsize=(6, 3.8))
        ax.pie([n_pass, n_support], colors=[GREEN, RED], startangle=90, counterclock=False,
               wedgeprops=dict(width=0.42, edgecolor=PANEL),
               autopct=lambda p: f"{p:.0f}%" if p > 0 else "", pctdistance=0.79,
               textprops=dict(color="#08111f", fontweight="bold"))
        ax.legend([f"Passing ({n_pass})", f"Needs support ({n_support})"], loc="center left",
                  bbox_to_anchor=(1, 0.5), facecolor=PANEL, edgecolor="#3a4358", labelcolor=TEXT)
        fig.patch.set_facecolor(PANEL)
        show(fig)

    st.write("")
    st.subheader("Subject Statistics")
    st.dataframe(subj_tbl, width="stretch", hide_index=True)

# ================================================================== RANKINGS
elif page == SECTIONS[2]:
    st.subheader("Student Rankings")

    def clear_search():
        st.session_state["rank_search"] = ""

    c1, c2 = st.columns([6, 1], vertical_alignment="bottom")
    q = c1.text_input("🔍 Search student", key="rank_search", placeholder="Type a name or ID…")
    c2.button("✕ Clear", on_click=clear_search, width="stretch", disabled=not q)

    view = ranks
    if q:
        mask = view[id_cols].astype(str).apply(
            lambda col: col.str.contains(q, case=False, na=False, regex=False)).any(axis=1)
        view = view[mask]
        st.caption(f"{len(view)} match(es) for “{q}”")
    st.dataframe(view, width="stretch", hide_index=True, height=440)
    st.caption("Students with equal averages share the same rank.")

    label = id_cols[-1]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**🥇 Top 5**")
        st.dataframe(ranks.head(5)[["Rank", label, "Average"]], hide_index=True, width="stretch")
    with c2:
        st.markdown("**⬇️ Bottom 5**")
        st.dataframe(ranks.tail(5).iloc[::-1][["Rank", label, "Average"]], hide_index=True, width="stretch")

# ================================================================== SUPPORT
elif page == SECTIONS[3]:
    st.subheader("Students Needing Support")
    st.info(f"A student is listed if **any one subject** is below **{threshold}**, "
            "even when their overall average is higher.")
    if support.empty:
        st.success("🎉 No students are below the threshold in any subject.")
    else:
        c = st.columns(3)
        card(c[0], "Flagged Students", len(support), f"{len(support) / stats['total_students'] * 100:.1f}% of class")
        card(c[1], "Multiple Weak Subjects", int((support["Count"] > 1).sum()))
        card(c[2], "Flagged but Avg ≥ Threshold", int((support["Average"] >= threshold).sum()))
        st.write("")
        st.dataframe(support, width="stretch", hide_index=True)

        with st.container(border=True):
            chart_head("Weak-subject frequency", f"Number of students below {threshold} in each subject.",
                       "BY SUBJECT")
            counts = {s: int((df[s] < threshold).sum()) for s in subjects}
            fig, ax = plt.subplots(figsize=(7, 3))
            ax.bar(counts.keys(), counts.values(), color=RED)
            ax.set_ylabel("Students")
            plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
            style_ax(fig, ax)
            show(fig)

# ================================================================== REPORTS
else:
    st.subheader("Download Reports")
    excel = ex.build_excel(stats, ranks, subj_tbl, support, df)
    c = st.columns(2)
    with c[0], st.container(border=True):
        st.markdown("**📗 Full Excel Workbook**")
        st.caption("Sheets: Overview, Rankings, Subject Averages, Support List, Uploaded Data")
        st.download_button("Download Excel report", excel, "student_analysis_report.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           width="stretch")
    with c[1], st.container(border=True):
        st.markdown("**📄 CSV Exports**")
        st.download_button("Rankings (CSV)", ex.to_csv_bytes(ranks), "rankings.csv", "text/csv", width="stretch")
        st.download_button("Support list (CSV)", ex.to_csv_bytes(support), "support_list.csv", "text/csv", width="stretch")
        st.download_button("Subject averages (CSV)", ex.to_csv_bytes(subj_tbl), "subject_averages.csv",
                           "text/csv", width="stretch")
    st.warning("These files contain student data. Share them only with authorised staff.")
