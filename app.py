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
from epistemically.dataset import check_cases  # noqa: E402

RESULTS_DIR = REPO_ROOT / "data" / "results"
CASES_DIR = REPO_ROOT / "data" / "cases"
PREFERRED_RESULTS = RESULTS_DIR / "user_cases_results.csv"
FALLBACK_RESULTS = RESULTS_DIR / "sample_results.csv"

st.set_page_config(page_title="Epistemically", layout="wide")
st.title("Epistemically")
st.markdown(
    "Practical evaluation of LLM behavior under epistemic norms: "
    "belief/truth/knowledge distinctions, Gettier-style epistemic luck, "
    "deduction/rationality, and defeaters. Scores measure whether model "
    "*outputs* track these distinctions on structured cases — no claim that "
    "models literally believe or know anything."
)


def load_case_lookup():
    """Index every case in data/cases/*.jsonl by case id."""
    lookup = {}
    problems = []
    for path in sorted(CASES_DIR.glob("*.jsonl")):
        cases, errors = check_cases(path)
        for case in cases:
            lookup[case.id] = case
        problems.extend(f"{path.name}: {err}" for err in errors)
    return lookup, problems


def json_or_empty(value) -> dict:
    if pd.isna(value) or not value:
        return {}
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}


# --- Load results ----------------------------------------------------------
all_csvs = sorted(RESULTS_DIR.glob("*.csv")) if RESULTS_DIR.exists() else []
# De-emphasize scratch/test outputs; fall back to everything if that's all there is.
csv_files = [p for p in all_csvs if not p.name.endswith("_test_results.csv")] or all_csvs
if not csv_files:
    st.warning(
        "No results found in data/results/. Run "
        "`python scripts/run_eval.py` to generate some."
    )
    st.stop()

if PREFERRED_RESULTS in csv_files:
    default_index = csv_files.index(PREFERRED_RESULTS)
elif FALLBACK_RESULTS in csv_files:
    default_index = csv_files.index(FALLBACK_RESULTS)
else:
    default_index = 0

selected_csv = st.selectbox(
    "Results file", csv_files, index=default_index, format_func=lambda p: p.name
)
df = load_results(selected_csv)
models = ", ".join(sorted(df["model"].astype(str).unique()))
st.caption(
    f"Loaded **{selected_csv.relative_to(REPO_ROOT).as_posix()}** — "
    f"{len(df)} rows, model(s): {models}"
)

api_errors = df["error"].fillna("").astype(str).str.strip().str.len() > 0
parse_failures = df["parsed_ok"].astype(str).str.lower() != "true"
if api_errors.any() or parse_failures.any():
    st.warning(
        f"This file contains {int(api_errors.sum())} row(s) with API errors and "
        f"{int(parse_failures.sum())} row(s) whose response could not be parsed as JSON. "
        "Affected fields score 0; interpret aggregates with care."
    )

# --- Score table and chart --------------------------------------------------
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

# --- Case explorer -----------------------------------------------------------
st.header("Case explorer")
cases_by_id, case_file_problems = load_case_lookup()
for problem in case_file_problems:
    st.warning(f"Case file issue — {problem}")

case_ids = sorted(df["case_id"].astype(str).unique())
selected_id = st.selectbox("Case", case_ids)
case_rows = df[df["case_id"] == selected_id]

case = cases_by_id.get(selected_id)
if case is not None:
    st.subheader(f"{case.id} — {case.module} / {case.schema_family} ({case.difficulty})")
    st.markdown(f"**Scenario:** {case.scenario}")
    st.markdown(f"**Target proposition:** {case.target_proposition}")
    st.markdown(f"**Question:** {case.question}")
    if case.notes:
        st.caption(case.notes)
else:
    st.info(
        f"Case `{selected_id}` was not found in any data/cases/*.jsonl file; "
        "showing result rows only."
    )

for _, row in case_rows.iterrows():
    st.markdown(f"### `{row['model']}`")
    st.markdown(
        f"**Score:** {row['score']:.2f} ({row['points']:g}/{row['max_points']:g} points)"
    )
    if isinstance(row.get("error"), str) and row["error"].strip():
        st.error(f"API error: {row['error']}")

    col_expected, col_predicted = st.columns(2)
    with col_expected:
        st.markdown("**Expected labels**")
        st.json(json_or_empty(row.get("expected_json")))
    with col_predicted:
        st.markdown("**Model labels**")
        predicted = json_or_empty(row.get("predicted_json"))
        if predicted:
            st.json(predicted)
        else:
            st.caption("No parseable model output.")

    field_results = json_or_empty(row.get("field_results_json"))
    if field_results:
        st.markdown("**Field-level correctness**")
        st.dataframe(
            pd.DataFrame(
                {"field": list(field_results), "correct": ["✓" if v else "✗" for v in field_results.values()]}
            ),
            use_container_width=True,
            hide_index=True,
        )

    explanation = row.get("brief_explanation")
    if isinstance(explanation, str) and explanation.strip():
        st.caption(f"Model explanation: {explanation}")

# --- Failures -----------------------------------------------------------------
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
