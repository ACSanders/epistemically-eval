"""Epistemically dashboard: dark-theme evaluation explorer for eval results."""

import json
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
    ACCENT,
    APP_CSS,
    BAD,
    CARD_BG,
    CORAL,
    CORAL_FILL,
    GOOD,
    HEATMAP_SCALE,
    MUTED,
    failure_card,
    field_accuracy,
    field_rows,
    json_or_empty,
    load_all_results,
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

tab_overview, tab_profile, tab_failures, tab_explorer, tab_compare, tab_method = st.tabs(
    [
        "Overview",
        "Module Profile",
        "Failure Gallery",
        "Case Explorer",
        "Model Comparison",
        "Methodology",
    ]
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

# --- Model Comparison ------------------------------------------------------------------
with tab_compare:
    combined, loaded_files = load_all_results(RESULTS_DIR)
    n_models = combined["model"].nunique() if not combined.empty else 0
    if n_models < 2:
        st.info(
            "Model comparison needs results from at least two models in "
            "data/results/. Run the eval with different --model values."
        )
    else:
        st.caption(
            f"Combined from {len(loaded_files)} file(s): {', '.join(loaded_files)}. "
            "Latest run kept per model/case. This tab ignores the filter panel above."
        )
        all_models = sorted(combined["model"].astype(str).unique())
        col_a, col_b = st.columns(2)
        with col_a:
            index_a = all_models.index("gpt-4o-mini") if "gpt-4o-mini" in all_models else 0
            model_a = st.selectbox("Baseline model (A)", all_models, index=index_a)
        with col_b:
            index_b = (
                all_models.index("gpt-5-mini")
                if "gpt-5-mini" in all_models
                else min(1, len(all_models) - 1)
            )
            model_b = st.selectbox("Comparison model (B)", all_models, index=index_b)

        if model_a == model_b:
            st.warning("Pick two different models to compare.")
        else:
            cdf = combined[combined["model"].isin([model_a, model_b])].copy()
            shared_ids = set(cdf[cdf["model"] == model_a]["case_id"]) & set(
                cdf[cdf["model"] == model_b]["case_id"]
            )
            cdf = cdf[cdf["case_id"].isin(shared_ids)]
            adf = cdf[cdf["model"] == model_a]
            bdf = cdf[cdf["model"] == model_b]
            mean_a, mean_b = adf["score"].mean(), bdf["score"].mean()
            color_map = {model_a: MUTED, model_b: ACCENT}

            cards = st.columns(4)
            cards[0].markdown(metric_card(f"A · {model_a}", f"{mean_a:.3f}"), unsafe_allow_html=True)
            cards[1].markdown(
                metric_card(f"B · {model_b}", f"{mean_b:.3f}", accent=True), unsafe_allow_html=True
            )
            cards[2].markdown(
                metric_card("Δ overall (B − A)", f"{mean_b - mean_a:+.3f}"), unsafe_allow_html=True
            )
            cards[3].markdown(
                metric_card("Shared cases", str(len(shared_ids)), sub="latest run per model"),
                unsafe_allow_html=True,
            )

            # Module-level scores: grouped bars with CI, plus a fingerprint radar
            summary = summarize_by_model_module(cdf)
            bars = px.bar(
                summary,
                x="module",
                y="mean_score",
                color="model",
                barmode="group",
                error_y=summary["ci_high"] - summary["mean_score"],
                error_y_minus=summary["mean_score"] - summary["ci_low"],
                range_y=[0, 1.02],
                color_discrete_map=color_map,
            )
            bars.update_traces(marker_line_width=0)
            st.plotly_chart(
                style_fig(bars, "Module score by model (bootstrap 95% CI)", height=380),
                width="stretch",
            )

            module_means = cdf.pivot_table(index="module", columns="model", values="score")
            if len(module_means) >= 3:
                radar = go.Figure()
                for model_name, line_color, fill in [
                    (model_a, MUTED, "rgba(139, 150, 165, 0.15)"),
                    (model_b, CORAL, CORAL_FILL),
                ]:
                    values = module_means[model_name].tolist()
                    radar.add_trace(
                        go.Scatterpolar(
                            r=values + values[:1],
                            theta=list(module_means.index) + [module_means.index[0]],
                            fill="toself",
                            name=model_name,
                            line=dict(color=line_color, width=2),
                            fillcolor=fill,
                        )
                    )
                radar.update_layout(
                    polar=dict(
                        bgcolor=CARD_BG,
                        radialaxis=dict(range=[0, 1], gridcolor="#232a35", tickfont=dict(size=10)),
                        angularaxis=dict(gridcolor="#232a35"),
                    ),
                )
                radar_fig = style_fig(radar, "Epistemic fingerprint", height=460)
                radar_fig.update_layout(margin=dict(l=90, r=90, t=60, b=70))
                st.plotly_chart(radar_fig, width="stretch")

            # Schema-family heatmap per model
            family_pivot = cdf.pivot_table(
                index="model", columns="schema_family", values="score", aggfunc="mean"
            )
            heat = px.imshow(
                family_pivot,
                zmin=0,
                zmax=1,
                text_auto=".2f",
                color_continuous_scale=HEATMAP_SCALE,
                aspect="auto",
            )
            heat.update_layout(coloraxis_colorbar=dict(title="score"))
            st.plotly_chart(
                style_fig(heat, "Schema-family score by model", height=300), width="stretch"
            )

            # Delta charts: B − A by module and by schema family
            def delta_chart(group_col: str, title: str):
                pivot = cdf.pivot_table(index=group_col, columns="model", values="score")
                delta = (pivot[model_b] - pivot[model_a]).sort_values()
                fig = go.Figure(
                    go.Bar(
                        x=delta.values,
                        y=delta.index,
                        orientation="h",
                        marker_color=[GOOD if v >= 0 else BAD for v in delta.values],
                    )
                )
                fig.update_xaxes(title=f"Δ mean score ({model_b} − {model_a})")
                return style_fig(fig, title, height=max(260, 40 * len(delta) + 120))

            col_dm, col_df = st.columns(2)
            with col_dm:
                st.plotly_chart(delta_chart("module", "Δ by module"), width="stretch")
            with col_df:
                st.plotly_chart(delta_chart("schema_family", "Δ by schema family"), width="stretch")

            # Field-level accuracy
            acc = field_accuracy(cdf)
            if not acc.empty:
                acc_fig = px.bar(
                    acc,
                    x="field",
                    y="accuracy",
                    color="model",
                    barmode="group",
                    range_y=[0, 1.02],
                    color_discrete_map=color_map,
                    hover_data=["n"],
                )
                acc_fig.update_traces(marker_line_width=0)
                st.plotly_chart(
                    style_fig(acc_fig, "Field-level accuracy by model", height=380),
                    width="stretch",
                )

            # Disagreement explorer (case counts as correct when score == 1.0)
            st.subheader("Disagreement explorer")
            case_scores = cdf.pivot_table(index="case_id", columns="model", values="score")
            b_only = case_scores[(case_scores[model_b] >= 1.0) & (case_scores[model_a] < 1.0)]
            a_only = case_scores[(case_scores[model_a] >= 1.0) & (case_scores[model_b] < 1.0)]
            both_missed = case_scores[(case_scores[model_a] < 1.0) & (case_scores[model_b] < 1.0)]
            categories = {
                f"B correct, A missed ({len(b_only)})": b_only,
                f"A correct, B missed ({len(a_only)})": a_only,
                f"Both missed ({len(both_missed)})": both_missed,
            }
            picked = st.radio(
                "Category", list(categories), horizontal=True, label_visibility="collapsed"
            )
            bucket = categories[picked]
            if bucket.empty:
                st.success("No cases in this category.")
            else:
                meta = (
                    cdf[cdf["case_id"].isin(bucket.index)][["case_id", "module", "schema_family"]]
                    .drop_duplicates("case_id")
                    .set_index("case_id")
                )
                listing = bucket.join(meta).reset_index()
                listing = listing[["case_id", "module", "schema_family", model_a, model_b]]
                st.dataframe(
                    listing.sort_values(model_b),
                    width="stretch",
                    hide_index=True,
                    column_config={
                        model_a: st.column_config.NumberColumn(f"A · {model_a}", format="%.2f"),
                        model_b: st.column_config.NumberColumn(f"B · {model_b}", format="%.2f"),
                    },
                )

                detail_id = st.selectbox("Inspect case", sorted(bucket.index))
                detail_case = cases_by_id.get(detail_id)
                if detail_case is not None:
                    st.markdown(f"**Scenario:** {detail_case.scenario}")
                    st.markdown(f"**Target proposition:** {detail_case.target_proposition}")
                row_a = adf[adf["case_id"] == detail_id].iloc[0]
                row_b = bdf[bdf["case_id"] == detail_id].iloc[0]
                expected = json_or_empty(row_a["expected_json"])
                pred_a = json_or_empty(row_a.get("predicted_json"))
                pred_b = json_or_empty(row_b.get("predicted_json"))
                res_a = json_or_empty(row_a.get("field_results_json"))
                res_b = json_or_empty(row_b.get("field_results_json"))
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "field": field,
                                "expected": json.dumps(value),
                                f"A · {model_a}": json.dumps(pred_a.get(field, "—")),
                                "A ✓": "✓" if res_a.get(field) else "✗",
                                f"B · {model_b}": json.dumps(pred_b.get(field, "—")),
                                "B ✓": "✓" if res_b.get(field) else "✗",
                            }
                            for field, value in expected.items()
                        ]
                    ),
                    width="stretch",
                    hide_index=True,
                )
                for label, row in ((f"A · {model_a}", row_a), (f"B · {model_b}", row_b)):
                    explanation = row.get("brief_explanation")
                    if isinstance(explanation, str) and explanation.strip():
                        st.caption(f"{label}: {explanation}")

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
