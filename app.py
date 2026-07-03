"""Epistemically dashboard: explore eval results by model, module, and case."""

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from epistemically.analysis import failures, load_results, summarize_by_model_module  # noqa: E402
from epistemically.dataset import load_cases  # noqa: E402

RESULTS_DIR = REPO_ROOT / "data" / "results"
DEFAULT_RESULTS = RESULTS_DIR / "sample_results.csv"
CASES_PATH = REPO_ROOT / "data" / "cases" / "sample_cases.jsonl"

st.set_page_config(page_title="Epistemically", layout="wide")
st.title("Epistemically")
st.markdown(
    "Practical evaluation of LLM behavior under epistemic norms: "
    "belief/knowledge/fact distinctions, Gettier-style epistemic luck, deduction, "
    "and defeaters. Scores measure whether model *outputs* track these distinctions "
    "on structured cases — no claim that models literally believe or know anything."
)

# --- Load results ---------------------------------------------------------
csv_files = sorted(RESULTS_DIR.glob("*.csv")) if RESULTS_DIR.exists() else []
if not csv_files:
    st.warning(
        "No results found in data/results/. Run "
        "`python scripts/run_eval.py` to generate some."
    )
    st.stop()

default_index = csv_files.index(DEFAULT_RESULTS) if DEFAULT_RESULTS in csv_files else 0
selected_csv = st.selectbox(
    "Results file", csv_files, index=default_index, format_func=lambda p: p.name
)
df = load_results(selected_csv)

# --- Score table and chart ------------------------------------------------
st.header("Scores by model and module")
summary = summarize_by_model_module(df)
st.dataframe(summary, use_container_width=True, hide_index=True)

fig = px.bar(
    summary,
    x="module",
    y="mean_score",
    color="model",
    barmode="group",
    error_y=summary["ci_high"] - summary["mean_score"],
    error_y_minus=summary["mean_score"] - summary["ci_low"],
    range_y=[0, 1],
    title="Mean score by module (bootstrap 95% CI)",
)
st.plotly_chart(fig, use_container_width=True)

# --- Case explorer --------------------------------------------------------
st.header("Case explorer")
cases_by_id = {}
if CASES_PATH.exists():
    cases_by_id = {case.id: case for case in load_cases(CASES_PATH)}

case_ids = sorted(df["case_id"].unique())
selected_id = st.selectbox("Case", case_ids)
case_rows = df[df["case_id"] == selected_id]

case = cases_by_id.get(selected_id)
if case is not None:
    st.subheader(f"{case.id} — {case.module} / {case.schema_family}")
    st.markdown(f"**Scenario:** {case.scenario}")
    st.markdown(f"**Target proposition:** {case.target_proposition}")
    st.markdown(f"**Question:** {case.question}")
    if case.notes:
        st.caption(case.notes)
else:
    st.info("Case text not found in the sample case file; showing result rows only.")

for _, row in case_rows.iterrows():
    st.markdown(f"**Model:** `{row['model']}` — score {row['score']:.2f} "
                f"({row['points']:g}/{row['max_points']:g} points)")
    col_expected, col_predicted = st.columns(2)
    with col_expected:
        st.markdown("Expected labels")
        st.json(json.loads(row["expected_json"]) if pd.notna(row["expected_json"]) else {})
    with col_predicted:
        st.markdown("Model labels")
        predicted = row.get("predicted_json")
        st.json(json.loads(predicted) if pd.notna(predicted) and predicted else {})
    explanation = row.get("brief_explanation")
    if pd.notna(explanation) and explanation:
        st.caption(f"Model explanation: {explanation}")

# --- Failures --------------------------------------------------------------
st.header("Failure examples")
failed = failures(df)
if failed.empty:
    st.success("No failures in this results file.")
else:
    st.dataframe(
        failed[["case_id", "module", "schema_family", "model", "score", "field_results_json"]],
        use_container_width=True,
        hide_index=True,
    )
