"""Epistemically dashboard: dark-theme evaluation explorer for eval results."""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from epistemically.analysis import summarize_by_model_module  # noqa: E402
from epistemically.app_utils import (  # noqa: E402
    APP_CSS,
    CARD_BG,
    CORAL,
    CORAL_FILL,
    HEATMAP_SCALE,
    failure_card,
    field_rows,
    json_or_empty,
    load_case_lookup,
    metric_card,
    style_fig,
)

RESULTS_DIR = REPO_ROOT / "data" / "results"
CASES_DIR = REPO_ROOT / "data" / "cases"
PREFERRED_RESULTS = RESULTS_DIR / "user_cases_results.csv"
DEMO_RESULTS = RESULTS_DIR / "sample_results.csv"

st.set_page_config(page_title="Epistemically", page_icon="◉", layout="wide")
st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)

st.markdown(
    '<div class="hero"><h1>Epistemically<span class="dot">.</span></h1>'
    "<p>An epistemic behavior lab for evaluating how LLMs track belief, truth, "
    "knowledge, inference, defeaters, and luck.</p></div>",
    unsafe_allow_html=True,
)


def results_label(path: Path) -> str:
    return f"{path.name} (demo)" if path == DEMO_RESULTS else path.name


# --- Sidebar: file selection and filters -------------------------------------
all_csvs = sorted(RESULTS_DIR.glob("*.csv")) if RESULTS_DIR.exists() else []
csv_files = [p for p in all_csvs if not p.name.endswith("_test_results.csv")]
# De-emphasize the demo file: list it last, and only offer it alongside real runs.
csv_files.sort(key=lambda p: (p == DEMO_RESULTS, p.name))
if not csv_files:
    csv_files = all_csvs
if not csv_files:
    st.warning("No results found in data/results/. Run `python scripts/run_eval.py` first.")
    st.stop()

# Top controls panel; columns stack vertically on narrow viewports.
with st.container(border=True):
    col_file, col_models, col_modules = st.columns([2, 2, 2])
    with col_file:
        default_index = (
            csv_files.index(PREFERRED_RESULTS) if PREFERRED_RESULTS in csv_files else 0
        )
        selected_csv = st.selectbox(
            "Results file", csv_files, index=default_index, format_func=results_label
        )
    df = pd.read_csv(selected_csv)
    # Cases without a schema_family group under a placeholder so they still
    # appear in family filters and the heatmap.
    if "schema_family" in df.columns:
        df["schema_family"] = df["schema_family"].fillna("(none)")
    models = sorted(df["model"].astype(str).unique())
    modules = sorted(df["module"].astype(str).unique())

    with col_models:
        if len(models) > 1:
            model_filter = st.multiselect("Models", models, default=models)
        else:
            model_filter = models
            st.selectbox("Model", models, disabled=True)
    with col_modules:
        module_filter = st.multiselect("Modules", modules, default=modules)

    col_range, col_toggle = st.columns([3, 2])
    with col_range:
        score_range = st.slider("Score range", 0.0, 1.0, (0.0, 1.0), 0.05)
    with col_toggle:
        imperfect_only = st.toggle(
            "Show imperfect cases only",
            value=False,
            help="Applies to Overview, Module Profile, and Case Explorer. "
            "The Failure Gallery is always failure-focused.",
        )

base = df[
    df["model"].astype(str).isin(model_filter)
    & df["module"].astype(str).isin(module_filter)
    & df["score"].between(score_range[0], score_range[1])
]
fdf = base[base["score"] < 1.0] if imperfect_only else base
st.caption(f"{len(fdf)} of {len(df)} rows selected — {results_label(selected_csv)}")

api_errors = df["error"].fillna("").astype(str).str.strip().str.len() > 0
parse_failures = df["parsed_ok"].astype(str).str.lower() != "true"
if api_errors.any() or parse_failures.any():
    st.warning(
        f"This file contains {int(api_errors.sum())} row(s) with API errors and "
        f"{int(parse_failures.sum())} row(s) with unparseable responses. Affected "
        "fields score 0; interpret aggregates with care."
    )

cases_by_id, case_file_problems = load_case_lookup(CASES_DIR)
for problem in case_file_problems:
    st.warning(f"Case file issue — {problem}")

tab_overview, tab_profile, tab_failures, tab_explorer, tab_method = st.tabs(
    ["Overview", "Module Profile", "Failure Gallery", "Case Explorer", "Methodology"]
)

# --- Overview -----------------------------------------------------------------
with tab_overview:
    if fdf.empty:
        st.info("No rows match the current filters.")
    else:
        module_means = fdf.groupby("module")["score"].mean()
        strongest = module_means.idxmax()
        weakest = module_means.idxmin()
        n_failures = int((fdf["score"] < 1.0).sum())

        row1 = st.columns(3)
        row1[0].markdown(
            metric_card("Overall Epistemic Score", f"{fdf['score'].mean():.3f}", accent=True),
            unsafe_allow_html=True,
        )
        row1[1].markdown(
            metric_card("Cases Evaluated", str(len(fdf)), sub=f"{len(model_filter)} model(s)"),
            unsafe_allow_html=True,
        )
        row1[2].markdown(
            metric_card("Failures", str(n_failures), sub="cases below a perfect score"),
            unsafe_allow_html=True,
        )
        row2 = st.columns(3)
        row2[0].markdown(
            metric_card("Strongest Module", strongest, sub=f"mean {module_means.max():.3f}"),
            unsafe_allow_html=True,
        )
        row2[1].markdown(
            metric_card("Weakest Module", weakest, sub=f"mean {module_means.min():.3f}"),
            unsafe_allow_html=True,
        )
        row2[2].markdown(
            metric_card(
                "Points Earned",
                f"{fdf['points'].sum():g} / {fdf['max_points'].sum():g}",
                sub="weighted label components",
            ),
            unsafe_allow_html=True,
        )

        summary = summarize_by_model_module(fdf)
        fig = px.bar(
            summary,
            x="module",
            y="mean_score",
            color="model",
            barmode="group",
            error_y=summary["ci_high"] - summary["mean_score"],
            error_y_minus=summary["mean_score"] - summary["ci_low"],
            range_y=[0, 1.02],
        )
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(
            style_fig(fig, "Mean score by module (bootstrap 95% CI)", height=380),
            width="stretch",
        )

        st.dataframe(
            summary,
            width="stretch",
            hide_index=True,
            column_config={
                "mean_score": st.column_config.ProgressColumn(
                    "mean score", min_value=0.0, max_value=1.0, format="%.3f"
                ),
                "ci_low": st.column_config.NumberColumn("CI low", format="%.3f"),
                "ci_high": st.column_config.NumberColumn("CI high", format="%.3f"),
                "n_cases": st.column_config.NumberColumn("n"),
            },
        )

# --- Module Profile -------------------------------------------------------------
with tab_profile:
    if fdf.empty:
        st.info("No rows match the current filters.")
    else:
        profile_models = sorted(fdf["model"].astype(str).unique())
        profile_model = (
            st.selectbox("Model", profile_models) if len(profile_models) > 1 else profile_models[0]
        )
        mdf = fdf[fdf["model"].astype(str) == profile_model]
        module_means = mdf.groupby("module")["score"].mean()

        if len(module_means) >= 3:
            theta = list(module_means.index) + [module_means.index[0]]
            r = list(module_means.values) + [module_means.values[0]]
            radar = go.Figure(
                go.Scatterpolar(
                    r=r,
                    theta=theta,
                    fill="toself",
                    line=dict(color=CORAL, width=2),
                    fillcolor=CORAL_FILL,
                )
            )
            radar.update_layout(
                polar=dict(
                    bgcolor=CARD_BG,
                    radialaxis=dict(range=[0, 1], gridcolor="#232a35", tickfont=dict(size=10)),
                    angularaxis=dict(gridcolor="#232a35"),
                ),
                showlegend=False,
            )
            radar_fig = style_fig(radar, f"Module profile — {profile_model}", height=500)
            # Room for the polar category labels on every side of the wheel.
            radar_fig.update_layout(margin=dict(l=90, r=90, t=60, b=70))
            st.plotly_chart(radar_fig, width="stretch")
        else:
            st.info("Radar view needs at least three modules; widen the module filter.")

        st.markdown("&nbsp;")
        pivot = mdf.pivot_table(
            index="module", columns="schema_family", values="score", aggfunc="mean"
        )
        heat = px.imshow(
            pivot,
            zmin=0,
            zmax=1,
            text_auto=".2f",
            color_continuous_scale=HEATMAP_SCALE,
            aspect="auto",
        )
        heat.update_layout(coloraxis_colorbar=dict(title="score"))
        st.plotly_chart(
            style_fig(heat, "Score by module × schema family", height=420),
            width="stretch",
        )

        n_per_module = mdf.groupby("module")["score"].count()
        weak_families = (
            mdf.groupby(["module", "schema_family"])["score"].mean().sort_values().head(3)
        )
        weak_lines = "\n".join(
            f"- `{family}` ({module}): mean {score:.2f}"
            for (module, family), score in weak_families.items()
        )
        st.markdown(
            f"**Reading this profile.** On this case set, `{profile_model}` scores highest "
            f"on `{module_means.idxmax()}` ({module_means.max():.2f}) and lowest on "
            f"`{module_means.idxmin()}` ({module_means.min():.2f}). The schema families "
            f"with the lowest mean scores are:\n\n{weak_lines}\n\n"
            f"With {int(n_per_module.min())}–{int(n_per_module.max())} cases per module, "
            "differences are directional rather than conclusive — treat this as a map of "
            "where to look, not a verdict. Scores describe output behavior on these cases, "
            "not any internal epistemic state of the model."
        )

# --- Failure Gallery -------------------------------------------------------------
with tab_failures:
    failed = base[base["score"] < 1.0].sort_values("score")
    if failed.empty:
        st.success("No failures within the current filters.")
    else:
        st.caption(
            f"{len(failed)} case(s) below a perfect score, worst first. "
            "✓/✗ marks per-field exact-label correctness."
        )
        MAX_CARDS = 30
        for _, row in failed.head(MAX_CARDS).iterrows():
            st.markdown(
                failure_card(row.to_dict(), cases_by_id.get(str(row["case_id"]))),
                unsafe_allow_html=True,
            )
        if len(failed) > MAX_CARDS:
            st.caption(f"Showing the {MAX_CARDS} lowest-scoring of {len(failed)} failures.")

# --- Case Explorer -----------------------------------------------------------------
with tab_explorer:
    if fdf.empty:
        st.info("No rows match the current filters.")
    else:
        col_search, col_module, col_family = st.columns([2, 2, 2])
        with col_search:
            search = st.text_input("Search case id", "")
        with col_module:
            explorer_module = st.selectbox(
                "Module", ["all"] + sorted(fdf["module"].astype(str).unique())
            )
        with col_family:
            family_pool = (
                fdf if explorer_module == "all" else fdf[fdf["module"] == explorer_module]
            )
            explorer_family = st.selectbox(
                "Schema family", ["all"] + sorted(family_pool["schema_family"].astype(str).unique())
            )

        edf = fdf.copy()
        if search.strip():
            edf = edf[edf["case_id"].astype(str).str.contains(search.strip(), case=False)]
        if explorer_module != "all":
            edf = edf[edf["module"] == explorer_module]
        if explorer_family != "all":
            edf = edf[edf["schema_family"] == explorer_family]

        case_ids = sorted(edf["case_id"].astype(str).unique())
        if not case_ids:
            st.info("No cases match the search and filters.")
        else:
            selected_id = st.selectbox("Case", case_ids)
            case = cases_by_id.get(selected_id)

            if case is not None:
                st.subheader(f"{case.id}")
                meta = [f"`{case.module}`"]
                if case.schema_family:
                    meta.append(f"`{case.schema_family}`")
                if case.variant_id is not None:
                    meta.append(f"variant {case.variant_id}")
                if case.difficulty:
                    meta.append(f"difficulty **{case.difficulty}**")
                st.markdown(" · ".join(meta))
                st.markdown(f"**Scenario:** {case.scenario}")
                st.markdown(f"**Target proposition:** {case.target_proposition}")
                st.markdown(f"**Question:** {case.question}")
                if case.notes:
                    st.caption(case.notes)
            else:
                st.info(f"Case `{selected_id}` not found in any data/cases/*.jsonl file.")

            for _, row in edf[edf["case_id"].astype(str) == selected_id].iterrows():
                st.markdown(f"#### `{row['model']}`")
                st.markdown(
                    f"**Score:** {row['score']:.2f} "
                    f"({row['points']:g}/{row['max_points']:g} points)"
                )
                if isinstance(row.get("error"), str) and row["error"].strip():
                    st.error(f"API error: {row['error']}")

                expected = json_or_empty(row.get("expected_json"))
                predicted = json_or_empty(row.get("predicted_json"))
                results = json_or_empty(row.get("field_results_json"))

                col_exp, col_pred = st.columns(2)
                with col_exp:
                    st.markdown("**Expected labels**")
                    st.json(expected)
                with col_pred:
                    st.markdown("**Model labels**")
                    if predicted:
                        st.json(predicted)
                    else:
                        st.caption("No parseable model output.")

                comparison = field_rows(expected, predicted, results)
                if comparison:
                    st.dataframe(
                        pd.DataFrame(
                            [
                                {
                                    "field": r["field"],
                                    "expected": r["expected"],
                                    "model": r["model"],
                                    "correct": "✓" if r["correct"] else "✗",
                                }
                                for r in comparison
                            ]
                        ),
                        width="stretch",
                        hide_index=True,
                    )

                raw = row.get("raw_response")
                if isinstance(raw, str) and raw.strip():
                    with st.expander("Raw model response"):
                        st.code(raw, language="json")

# --- Methodology ---------------------------------------------------------------------
with tab_method:
    st.markdown(
        """
### What Epistemically evaluates

Each case describes an agent in a short scenario and asks the model for
structured judgments about a target proposition: belief, truth, justification,
knowledge, entailment, and how justification responds to new evidence. Cases
span five modules — belief/truth/knowledge, Gettier-style epistemic luck,
deduction/rationality, defeaters, and (planned) induction/updating.

### Why exact-label scoring

Models answer from a fixed vocabulary of labels per field, and each field is
scored by exact match after light normalization. This keeps scoring
deterministic, cheap, and auditable — every point can be traced to a specific
field on a specific case. The trade-off is no partial credit for near-miss
phrasing, which is why prompts constrain the model to the exact vocabulary.

### What the confidence intervals mean

Mean scores carry percentile-bootstrap 95% intervals: the case set is
resampled with replacement many times and the middle 95% of resampled means
is reported. Wide intervals mean the case sample is too small to pin down the
score precisely. Comparisons between models on the same cases use a paired
bootstrap on per-case differences.

### Behavioral, not literal

A high score means the model's *outputs* reliably track epistemic
distinctions on these cases. It is not evidence that the model believes,
knows, or represents anything in the philosophical sense — and a claim like
that is outside what this kind of test could establish.

### Current limitations

- Small case counts per module: intervals are wide, results are directional.
- Exact-label scoring gives no credit for partially correct reasoning, and
  `brief_explanation` is collected but unscored.
- Single-run evaluation at temperature 0 does not measure sampling variance.
- Expected labels follow mainstream textbook verdicts; a few standard cases
  (notably fake barns) are philosophically contested.
        """
    )
