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

st.set_page_config(page_title="Epistemically", page_icon="◉", layout="wide")
st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)

st.markdown(
    '<div class="hero"><h1>Epistemically<span class="dot">.</span></h1>'
    "<p>An epistemic behavior lab for evaluating how LLMs track belief, truth, "
    "knowledge, inference, defeaters, and luck.</p></div>",
    unsafe_allow_html=True,
)

cases_by_id, case_file_problems = load_case_lookup(CASES_DIR)

# All result CSVs are combined into one dataset; the latest run wins per
# model/case, and rows are restricted to the current case universe so stale
# results for retired or renamed cases never surface in summaries.
combined, loaded_files = load_all_results(RESULTS_DIR, valid_case_ids=set(cases_by_id))
if combined.empty:
    st.warning("No results found in data/results/. Run `python scripts/run_eval.py` first.")
    st.stop()

all_models = sorted(combined["model"].astype(str).unique())
all_modules = sorted(combined["module"].astype(str).unique())
n_cases = combined["case_id"].nunique()
st.caption(
    f"{len(all_models)} model(s) evaluated on {n_cases} cases; combined from "
    f"{len(loaded_files)} result file(s), latest run kept per model and case."
)

api_errors = combined["error"].fillna("").astype(str).str.strip().str.len() > 0
parse_failures = combined["parsed_ok"].astype(str).str.lower() != "true"
if api_errors.any() or parse_failures.any():
    st.warning(
        f"The combined results contain {int(api_errors.sum())} row(s) with API "
        f"errors and {int(parse_failures.sum())} row(s) with unparseable "
        "responses. Affected fields score 0; interpret aggregates with care."
    )

for problem in case_file_problems:
    st.warning(f"Case file issue: {problem}")

tab_overview, tab_profile, tab_compare, tab_failures, tab_explorer, tab_method = st.tabs(
    [
        "Overview",
        "Model Profile",
        "Model Comparison",
        "Failure Gallery",
        "Case Explorer",
        "Methodology",
    ]
)

# --- Overview: global benchmark snapshot -----------------------------------------
with tab_overview:
    st.caption(
        "Global benchmark snapshot: how reliably each evaluated model's "
        "structured outputs track expected epistemic labels on the shared case set."
    )
    model_means = combined.groupby("model")["score"].mean().sort_values(ascending=False)
    best_model = str(model_means.index[0])

    case_pivot = combined.pivot_table(index="case_id", columns="model", values="score")
    fully_shared = case_pivot.dropna()
    n_persistent = int((fully_shared < 1.0).all(axis=1).sum()) if len(all_models) > 1 else int(
        (fully_shared[best_model] < 1.0).sum()
    )
    module_pivot = combined.pivot_table(
        index="module", columns="model", values="score", aggfunc="mean"
    )
    if len(all_models) > 1:
        module_gaps = module_pivot.max(axis=1) - module_pivot.min(axis=1)
        gap_module, gap_value = str(module_gaps.idxmax()), float(module_gaps.max())
    else:
        gap_module, gap_value = "n/a", 0.0

    row1 = st.columns(3)
    row1[0].markdown(
        metric_card("Models Evaluated", str(len(all_models)), sub=", ".join(all_models)),
        unsafe_allow_html=True,
    )
    row1[1].markdown(
        metric_card("Total Cases", str(n_cases), sub="each scored per model"),
        unsafe_allow_html=True,
    )
    row1[2].markdown(
        metric_card(
            "🏆 Best Overall Model",
            best_model,
            sub=f"mean score {model_means.iloc[0]:.3f}",
            accent=True,
        ),
        unsafe_allow_html=True,
    )
    row2 = st.columns(3)
    row2[0].markdown(
        metric_card(
            "Mean Score Across Models",
            f"{model_means.mean():.3f}",
            sub="average of per-model means",
        ),
        unsafe_allow_html=True,
    )
    row2[1].markdown(
        metric_card(
            "Persistently Hard Cases",
            str(n_persistent),
            sub="missed by every evaluated model",
        ),
        unsafe_allow_html=True,
    )
    row2[2].markdown(
        metric_card(
            "Largest Module Gap",
            f"{gap_value:.3f}" if gap_module != "n/a" else "n/a",
            sub=f"between models on {gap_module}" if gap_module != "n/a" else "needs 2+ models",
        ),
        unsafe_allow_html=True,
    )

    leaderboard = go.Figure(
        go.Bar(
            x=model_means.values[::-1],
            y=[str(m) for m in model_means.index[::-1]],
            orientation="h",
            marker_color=[
                ACCENT if str(m) == best_model else MUTED for m in model_means.index[::-1]
            ],
            text=[f"{v:.3f}" for v in model_means.values[::-1]],
            textposition="outside",
        )
    )
    leaderboard.update_xaxes(range=[0, 1.05])
    st.plotly_chart(
        style_fig(
            leaderboard,
            "Model leaderboard (mean score, best first)",
            height=max(220, 70 * len(all_models) + 120),
        ),
        width="stretch",
    )

    module_heat = combined.pivot_table(
        index="model", columns="module", values="score", aggfunc="mean"
    )
    heat_modules = px.imshow(
        module_heat,
        zmin=0,
        zmax=1,
        text_auto=".2f",
        color_continuous_scale=HEATMAP_SCALE,
        aspect="auto",
    )
    heat_modules.update_layout(coloraxis_colorbar=dict(title="score"))
    st.plotly_chart(
        style_fig(heat_modules, "Model performance by module", height=280),
        width="stretch",
    )

    family_heat = combined.pivot_table(
        index="model", columns="schema_family", values="score", aggfunc="mean"
    )
    heat_families = px.imshow(
        family_heat,
        zmin=0,
        zmax=1,
        text_auto=".2f",
        color_continuous_scale=HEATMAP_SCALE,
        aspect="auto",
    )
    heat_families.update_layout(coloraxis_colorbar=dict(title="score"))
    st.plotly_chart(
        style_fig(heat_families, "Schema-family performance by model", height=300),
        width="stretch",
    )

    acc_all = field_accuracy(combined)
    if not acc_all.empty:
        acc_fig = px.bar(
            acc_all,
            x="field",
            y="accuracy",
            color="model",
            barmode="group",
            range_y=[0, 1.02],
            hover_data=["n"],
        )
        acc_fig.update_traces(marker_line_width=0)
        st.plotly_chart(
            style_fig(acc_fig, "Field-level accuracy by model", height=380),
            width="stretch",
        )

# --- Model Profile: deep dive into one model ------------------------------------------
with tab_profile:
    st.caption(
        "Deep dive into one model's behavioral profile: where its outputs track "
        "expected epistemic labels and where its characteristic failure patterns sit."
    )
    col_model, col_modules = st.columns([2, 3])
    with col_model:
        profile_model = st.selectbox("Model", all_models)
    with col_modules:
        profile_modules = st.multiselect("Modules", all_modules, default=all_modules)

    mdf = combined[
        (combined["model"].astype(str) == profile_model)
        & combined["module"].astype(str).isin(profile_modules)
    ]
    if mdf.empty:
        st.info("No rows match the selected modules.")
    else:
        module_means = mdf.groupby("module")["score"].mean()
        n_solved = int((mdf["score"] >= 1.0).sum())
        n_missed = int((mdf["score"] < 1.0).sum())

        cards = st.columns(5)
        cards[0].markdown(
            metric_card("Overall Score", f"{mdf['score'].mean():.3f}", accent=True),
            unsafe_allow_html=True,
        )
        cards[1].markdown(
            metric_card("Cases Solved", str(n_solved), sub=f"of {len(mdf)} (perfect score)"),
            unsafe_allow_html=True,
        )
        cards[2].markdown(
            metric_card("Cases Missed", str(n_missed), sub="below a perfect score"),
            unsafe_allow_html=True,
        )
        cards[3].markdown(
            metric_card("Best Module", str(module_means.idxmax()), sub=f"mean {module_means.max():.3f}"),
            unsafe_allow_html=True,
        )
        cards[4].markdown(
            metric_card(
                "Weakest Module", str(module_means.idxmin()), sub=f"mean {module_means.min():.3f}"
            ),
            unsafe_allow_html=True,
        )

        summary = summarize_by_model_module(mdf)
        fig = px.bar(
            summary,
            x="module",
            y="mean_score",
            color="model",
            barmode="group",
            error_y=summary["ci_high"] - summary["mean_score"],
            error_y_minus=summary["mean_score"] - summary["ci_low"],
            range_y=[0, 1.02],
            color_discrete_sequence=[ACCENT],
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
            radar_fig = style_fig(radar, f"Module profile: {profile_model}", height=500)
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
            style_fig(heat, "Score by module and schema family", height=420),
            width="stretch",
        )

        acc_model = field_accuracy(mdf)
        if not acc_model.empty:
            acc_fig = px.bar(
                acc_model,
                x="field",
                y="accuracy",
                range_y=[0, 1.02],
                color_discrete_sequence=[ACCENT],
                hover_data=["n"],
            )
            acc_fig.update_traces(marker_line_width=0)
            st.plotly_chart(
                style_fig(acc_fig, f"Field-level accuracy: {profile_model}", height=360),
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
            "differences are directional rather than conclusive: treat this as a map of "
            "where to look, not a verdict. Scores describe output behavior on these cases, "
            "not any internal epistemic state of the model."
        )

        hardest = mdf[mdf["score"] < 1.0].sort_values("score").head(5)
        if not hardest.empty:
            st.subheader("Hardest cases for this model")
            st.caption(
                "The lowest-scoring cases in the current selection; the Failure "
                "Gallery has the full list."
            )
            for _, row in hardest.iterrows():
                st.markdown(
                    failure_card(row.to_dict(), cases_by_id.get(str(row["case_id"]))),
                    unsafe_allow_html=True,
                )

# --- Model Comparison ------------------------------------------------------------------
with tab_compare:
    n_models = len(all_models)
    if n_models < 2:
        st.info(
            "Model comparison needs results from at least two models in "
            "data/results/. Run the eval with different --model values."
        )
    else:
        st.caption(
            "Head-to-head behavioral comparison on the shared case set, using the "
            "combined results (latest run kept per model and case)."
        )
        col_a, col_b = st.columns(2)
        with col_a:
            index_a = all_models.index("gpt-4o-mini") if "gpt-4o-mini" in all_models else 0
            model_a = st.selectbox(
                "Model A (baseline)",
                all_models,
                index=index_a,
                help="Reference model. Deltas are computed as B minus A.",
            )
        with col_b:
            index_b = (
                all_models.index("gpt-5-mini")
                if "gpt-5-mini" in all_models
                else min(1, len(all_models) - 1)
            )
            model_b = st.selectbox(
                "Model B (comparison)",
                all_models,
                index=index_b,
                help="Model under comparison. Positive deltas mean B scores higher.",
            )

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

            st.subheader("Headline result")
            case_scores_head = cdf.pivot_table(index="case_id", columns="model", values="score")
            n_improved = int(
                ((case_scores_head[model_b] >= 1.0) & (case_scores_head[model_a] < 1.0)).sum()
            )
            n_regressed = int(
                ((case_scores_head[model_a] >= 1.0) & (case_scores_head[model_b] < 1.0)).sum()
            )
            cards = st.columns(4)
            cards[0].markdown(
                metric_card(f"A · {model_a}", f"{mean_a:.3f}", sub="baseline mean score"),
                unsafe_allow_html=True,
            )
            cards[1].markdown(
                metric_card(f"B · {model_b}", f"{mean_b:.3f}", sub="comparison mean score", accent=True),
                unsafe_allow_html=True,
            )
            cards[2].markdown(
                metric_card(
                    "Δ mean score (B − A)",
                    f"{mean_b - mean_a:+.3f}",
                    sub=f"on {len(shared_ids)} shared cases",
                ),
                unsafe_allow_html=True,
            )
            cards[3].markdown(
                metric_card(
                    "Cases improved / regressed",
                    f"{n_improved} / {n_regressed}",
                    sub="B fixes A's misses / B loses cases A had",
                ),
                unsafe_allow_html=True,
            )

            st.subheader("Epistemic fingerprint")
            st.caption(
                "Module-level behavioral profile: where each model's outputs track "
                "the expected labels, with bootstrap 95% intervals over this case set."
            )
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

            st.subheader("Strengths and weaknesses by schema family")
            st.caption(
                "Schema families are reusable scenario templates. Family-level scores "
                "localize each model's epistemic failure patterns more precisely than "
                "module means; deltas show where the comparison model gains or loses."
            )
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
                st.plotly_chart(
                    delta_chart("module", f"Δ by module ({model_b} − {model_a})"),
                    width="stretch",
                )
            with col_df:
                st.plotly_chart(
                    delta_chart("schema_family", f"Δ by schema family ({model_b} − {model_a})"),
                    width="stretch",
                )

            st.subheader("Field-level diagnostic signal")
            st.caption(
                "Exact-label accuracy per output field, aggregated across every case "
                "that scores the field. Persistent gaps on a single field (e.g. "
                "defeater_type) isolate a specific epistemic distinction a model "
                "mishandles, independent of overall score."
            )
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

            st.subheader("Case-level disagreements")
            st.caption(
                "A case counts as solved only at a perfect score (every expected "
                "field exact). Improved and regressed cases show what changed "
                "between models; persistently hard cases are the shared blind "
                "spots, the most informative targets for new schema families."
            )
            case_scores = cdf.pivot_table(index="case_id", columns="model", values="score")
            b_only = case_scores[(case_scores[model_b] >= 1.0) & (case_scores[model_a] < 1.0)]
            a_only = case_scores[(case_scores[model_a] >= 1.0) & (case_scores[model_b] < 1.0)]
            both_missed = case_scores[(case_scores[model_a] < 1.0) & (case_scores[model_b] < 1.0)]
            categories = {
                f"Improved: B solves, A missed ({len(b_only)})": b_only,
                f"Regressed: A solved, B misses ({len(a_only)})": a_only,
                f"Persistently hard: both miss ({len(both_missed)})": both_missed,
            }
            picked = st.radio(
                "Disagreement category",
                list(categories),
                horizontal=True,
                label_visibility="collapsed",
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
                    detail_meta = [f"`{detail_case.module}`"]
                    if detail_case.schema_family:
                        detail_meta.append(f"`{detail_case.schema_family}`")
                    st.markdown(f"**{detail_case.id}**: " + " · ".join(detail_meta))
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
                                f"A · {model_a}": json.dumps(pred_a.get(field, "-")),
                                "A ✓": "✓" if res_a.get(field) else "✗",
                                f"B · {model_b}": json.dumps(pred_b.get(field, "-")),
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

# --- Failure Gallery -------------------------------------------------------------
with tab_failures:
    st.caption(
        "Every case where a model's output fell short of a perfect exact-label "
        "score, worst first. ✓/✗ marks per-field correctness."
    )
    col_gm, col_gmod = st.columns(2)
    with col_gm:
        gallery_models = st.multiselect("Models", all_models, default=all_models)
    with col_gmod:
        gallery_modules = st.multiselect(
            "Modules", all_modules, default=all_modules, key="gallery_modules"
        )
    failed = combined[
        combined["model"].astype(str).isin(gallery_models)
        & combined["module"].astype(str).isin(gallery_modules)
        & (combined["score"] < 1.0)
    ].sort_values("score")
    if failed.empty:
        st.success("No failures within the current selection.")
    else:
        st.caption(f"{len(failed)} result(s) below a perfect score.")
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
    st.caption(
        "Audit view: filter to any slice of the combined results and inspect a "
        "case's scenario, expected labels, and every model's output on it."
    )
    col_m, col_search, col_module, col_family, col_correct = st.columns([2, 2, 2, 2, 2])
    with col_m:
        explorer_models = st.multiselect(
            "Models", all_models, default=all_models, key="explorer_models"
        )
    with col_search:
        search = st.text_input("Search case id", "")
    with col_module:
        explorer_module = st.selectbox("Module", ["all"] + all_modules)
    with col_family:
        family_pool = (
            combined if explorer_module == "all" else combined[combined["module"] == explorer_module]
        )
        explorer_family = st.selectbox(
            "Schema family", ["all"] + sorted(family_pool["schema_family"].astype(str).unique())
        )
    with col_correct:
        explorer_correct = st.selectbox("Correctness", ["all", "solved", "missed"])

    edf = combined[combined["model"].astype(str).isin(explorer_models)].copy()
    if search.strip():
        edf = edf[edf["case_id"].astype(str).str.contains(search.strip(), case=False)]
    if explorer_module != "all":
        edf = edf[edf["module"] == explorer_module]
    if explorer_family != "all":
        edf = edf[edf["schema_family"] == explorer_family]
    if explorer_correct == "solved":
        edf = edf[edf["score"] >= 1.0]
    elif explorer_correct == "missed":
        edf = edf[edf["score"] < 1.0]

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
                with st.expander(f"Raw model response ({row['model']})"):
                    st.code(raw, language="json")

# --- Methodology ---------------------------------------------------------------------
with tab_method:
    st.markdown(
        """
### What Epistemically evaluates

Each case describes an agent in a short scenario and asks the model for
structured judgments about a target proposition. Epistemically behaviorally
evaluates whether those outputs track expected epistemic labels: it
operationalizes distinctions from epistemology as scoreable fields, without
claiming models literally believe or know anything. Current modules:

- **belief_acceptance_knowledge**: families `belief_truth_knowledge`
  (attitude/truth/knowledge), `acceptance_and_belief` (belief vs. pragmatic
  acceptance and reason type), and `justification` (reason type and epistemic
  justification status)
- **gettier_luck**: justified true belief undermined by epistemic luck
- **rational_reasoning**: family `deduction` covering the reasoning pattern of a
  belief transition or belief set, its logical status, and the rational
  constraint it places on the agent (for example, accept the target or revise a
  premise when the entailment is recognized and in view)
- **defeaters**: family `rebuttal_and_undercut` covering defeater presence,
  mainstream defeater type, and whether new information requires belief revision

An induction/updating module is planned.

### Why exact-label scoring

Models answer from a fixed vocabulary of labels per field, and each field is
scored by exact match after light normalization. This keeps scoring
deterministic, cheap, and auditable: every point can be traced to a specific
field on a specific case. The trade-off is no partial credit for near-miss
phrasing, which is why prompts constrain the model to the exact vocabulary.

### What the confidence intervals mean

Mean scores carry percentile-bootstrap 95% intervals: the case set is
resampled with replacement many times and the middle 95% of resampled means
is reported. Wide intervals mean the case sample is too small to pin down the
score precisely. Comparisons between models on the same cases use a paired
bootstrap on per-case differences.

### How results are combined

Every results CSV in `data/results/` is merged into one dataset, keeping the
latest run per model and case. Superseded or duplicate files never appear as
extra leaderboard entries. The Overview summarizes all evaluated models; the
Model Profile and Model Comparison tabs slice the same combined data.

### How model comparison works

The Model Comparison tab pairs two models on the identical case set (latest
run per model). A case counts as solved only at a perfect score, so the
improved / regressed / persistently-hard buckets are conservative. Buckets and
deltas are diagnostic signals about epistemic failure patterns on this case
set: a map of where to look, not a leaderboard verdict, especially at current
sample sizes.

### Behavioral, not literal

A high score means the model's *outputs* reliably track epistemic
distinctions on these cases. It is not evidence that the model believes,
knows, or represents anything in the philosophical sense, and a claim like
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
