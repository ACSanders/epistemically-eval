"""Presentation helpers for the Streamlit dashboard (app.py).

Pure presentation layer: colors, CSS, Plotly styling, and HTML builders.
No scoring, runner, or schema logic lives here.
"""

import html
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple

import pandas as pd

from epistemically.dataset import check_cases
from epistemically.schemas import EpistemicCase

ACCENT = "#f0883e"
ACCENT_SOFT = "#ffa657"
BG = "#0a0e14"
CARD_BG = "#11161f"
CARD_BORDER = "#232a35"
GRID = "#1c222c"
TEXT = "#e6edf3"
MUTED = "#8b96a5"
GOOD = "#3fb950"
BAD = "#f85149"

# Chart palette: coral distinguishes data visuals from the orange UI accent,
# and the heatmap ramps navy -> muted purple -> amber/gold so intensity reads
# on the dark background without being orange everywhere.
CORAL = "#f4695f"
CORAL_FILL = "rgba(244, 105, 95, 0.22)"
HEATMAP_SCALE = [[0.0, "#141b29"], [0.5, "#5d4a7e"], [1.0, "#f5c04e"]]

CHART_COLORWAY = [ACCENT, "#ffd27d", "#d16a1f", "#8b96a5"]

APP_CSS = """
html, body, .stApp { background-color: #0a0e14; color: #e6edf3; }
[data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #232a35; }
[data-testid="stHeader"] { background: rgba(0,0,0,0); }

.hero { padding: 0.2rem 0 1rem 0; border-bottom: 1px solid #232a35; margin-bottom: 1rem; }
.hero h1 { font-size: 2.3rem; margin: 0; letter-spacing: -0.02em; color: #e6edf3; }
.hero h1 .dot { color: #f0883e; }
.hero p { color: #8b96a5; margin: 0.4rem 0 0 0; font-size: 1rem; max-width: 62rem; }

.metric-card { background: #11161f; border: 1px solid #232a35; border-radius: 12px;
               padding: 0.9rem 1.05rem; margin-bottom: 0.8rem; min-height: 5.4rem; }
.metric-card .label { color: #8b96a5; font-size: 0.72rem; text-transform: uppercase;
                      letter-spacing: 0.09em; }
.metric-card .value { color: #e6edf3; font-size: 1.6rem; font-weight: 650; margin-top: 0.15rem; }
.metric-card .value.accent { color: #ffa657; }
.metric-card .sub { color: #8b96a5; font-size: 0.78rem; margin-top: 0.05rem; }

.badge { display: inline-block; padding: 0.1rem 0.55rem; border-radius: 999px;
         font-size: 0.72rem; border: 1px solid #232a35; background: #161c26;
         color: #a9b4c0; margin-right: 0.3rem; }
.badge.accent { color: #ffa657; border-color: #5c3a1e; background: #241a10; }
.badge.good { color: #3fb950; border-color: #1f4429; background: #0e1f14; }
.badge.bad { color: #f85149; border-color: #5a1e1b; background: #24100f; }

.epi-card { background: #11161f; border: 1px solid #232a35; border-radius: 12px;
            padding: 1.05rem 1.2rem; margin-bottom: 0.9rem; }
.epi-card-head { display: flex; align-items: center; gap: 0.45rem; flex-wrap: wrap;
                 margin-bottom: 0.55rem; }
.epi-case-id { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
               color: #e6edf3; font-weight: 600; }
.epi-score { margin-left: auto; font-weight: 700; font-size: 1.05rem; }
.epi-score.warn { color: #ffa657; } .epi-score.bad { color: #f85149; }
.epi-card p { color: #c3ccd7; font-size: 0.9rem; margin: 0.3rem 0; line-height: 1.45; }
.epi-card p.muted { color: #8b96a5; }
table.epi-fields { width: 100%; border-collapse: collapse; margin-top: 0.55rem;
                   font-size: 0.84rem; }
table.epi-fields th { text-align: left; color: #8b96a5; font-weight: 500;
                      padding: 0.3rem 0.5rem; border-bottom: 1px solid #232a35; }
table.epi-fields td { padding: 0.3rem 0.5rem; border-bottom: 1px solid #1a2028;
                      color: #e6edf3;
                      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
.tick-good { color: #3fb950; font-weight: 700; }
.tick-bad { color: #f85149; font-weight: 700; }

div[data-testid="stVerticalBlockBorderWrapper"] { background: #11161f;
    border: 1px solid #232a35 !important; border-radius: 12px; }

.stTabs [data-baseweb="tab-list"] { gap: 0.3rem; border-bottom: 1px solid #232a35; }
.stTabs [data-baseweb="tab"] { color: #8b96a5; padding: 0.75rem 1.35rem; }
.stTabs [data-baseweb="tab"] p { font-size: 1.05rem; }
.stTabs [aria-selected="true"] { color: #ffa657 !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color: #f0883e; }
"""


def style_fig(fig, title: Optional[str] = None, height: Optional[int] = None):
    """Apply the shared dark/orange look to a Plotly figure."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=CHART_COLORWAY,
        font=dict(color=TEXT, size=13),
        title=dict(text=title, font=dict(size=16, color=TEXT)) if title else None,
        margin=dict(l=10, r=10, t=48 if title else 16, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    if height:
        fig.update_layout(height=height)
    return fig


def load_all_results(
    results_dir: Path, valid_case_ids: Optional[Set[str]] = None
) -> Tuple[pd.DataFrame, List[str]]:
    """Combine every results CSV in the directory for cross-model views.

    When the same (model, case_id) appears in several files, the row with the
    latest timestamp wins, so stale combined files coexist safely with fresh
    per-model files. When ``valid_case_ids`` is given, rows whose case id is
    not in the set are dropped: results for retired or renamed cases never
    reach the dashboard even though old CSVs stay on disk untouched.
    Returns (combined_frame, loaded_file_names).
    """
    files = [
        p for p in sorted(results_dir.glob("*.csv"))
        if not p.name.endswith("_test_results.csv")
    ]
    frames: List[pd.DataFrame] = []
    loaded: List[str] = []
    for path in files:
        try:
            frame = pd.read_csv(path)
        except Exception:
            continue
        if "case_id" not in frame.columns or "model" not in frame.columns:
            continue
        frame["source_file"] = path.name
        frames.append(frame)
        loaded.append(path.name)
    if not frames:
        return pd.DataFrame(), []
    combined = pd.concat(frames, ignore_index=True)
    if "schema_family" in combined.columns:
        combined["schema_family"] = combined["schema_family"].fillna("(none)")
    combined = (
        combined.sort_values("timestamp")
        .drop_duplicates(subset=["model", "case_id"], keep="last")
        .reset_index(drop=True)
    )
    if valid_case_ids is not None:
        combined = combined[
            combined["case_id"].astype(str).isin(valid_case_ids)
        ].reset_index(drop=True)
    return combined, loaded


def field_accuracy(df: pd.DataFrame) -> pd.DataFrame:
    """Per-(model, field) exact-label accuracy from field_results_json."""
    records = []
    for _, row in df.iterrows():
        for field, ok in json_or_empty(row.get("field_results_json")).items():
            records.append({"model": row["model"], "field": field, "correct": bool(ok)})
    if not records:
        return pd.DataFrame(columns=["model", "field", "accuracy", "n"])
    long = pd.DataFrame(records)
    return (
        long.groupby(["model", "field"])
        .agg(accuracy=("correct", "mean"), n=("correct", "size"))
        .reset_index()
    )


def json_or_empty(value: Any) -> Dict[str, Any]:
    """Parse a JSON-object cell from a results CSV; empty dict on any miss."""
    if value is None or (isinstance(value, float) and value != value) or value == "":
        return {}
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def load_case_lookup(cases_dir: Path) -> Tuple[Dict[str, EpistemicCase], List[str]]:
    """Index every case in data/cases/*.jsonl by case id."""
    lookup: Dict[str, EpistemicCase] = {}
    problems: List[str] = []
    for path in sorted(cases_dir.glob("*.jsonl")):
        cases, errors = check_cases(path)
        for case in cases:
            lookup[case.id] = case
        problems.extend(f"{path.name}: {err}" for err in errors)
    return lookup, problems


def field_rows(
    expected: Mapping[str, Any],
    predicted: Mapping[str, Any],
    field_results: Mapping[str, bool],
) -> List[Dict[str, Any]]:
    """Per-field comparison rows for display: field, expected, model, correct."""
    rows = []
    for field, expected_value in expected.items():
        rows.append(
            {
                "field": field,
                "expected": json.dumps(expected_value),
                "model": json.dumps(predicted[field]) if field in predicted else "—",
                "correct": bool(field_results.get(field, False)),
            }
        )
    return rows


def metric_card(label: str, value: str, sub: str = "", accent: bool = False) -> str:
    value_class = "value accent" if accent else "value"
    sub_html = f'<div class="sub">{html.escape(sub)}</div>' if sub else ""
    return (
        f'<div class="metric-card"><div class="label">{html.escape(label)}</div>'
        f'<div class="{value_class}">{html.escape(value)}</div>{sub_html}</div>'
    )


def badge(text: str, kind: str = "") -> str:
    css = f"badge {kind}".strip()
    return f'<span class="{css}">{html.escape(str(text))}</span>'


def _fields_table(rows: List[Dict[str, Any]]) -> str:
    tick_good = '<span class="tick-good">✓</span>'
    tick_bad = '<span class="tick-bad">✗</span>'
    body = "".join(
        "<tr>"
        f"<td>{html.escape(r['field'])}</td>"
        f"<td>{html.escape(r['expected'])}</td>"
        f"<td>{html.escape(r['model'])}</td>"
        f"<td>{tick_good if r['correct'] else tick_bad}</td>"
        "</tr>"
        for r in rows
    )
    return (
        '<table class="epi-fields">'
        "<tr><th>field</th><th>expected</th><th>model</th><th></th></tr>"
        f"{body}</table>"
    )


def failure_card(row: Mapping[str, Any], case: Optional[EpistemicCase]) -> str:
    """Render one below-perfect result row as an HTML card."""
    expected = json_or_empty(row.get("expected_json"))
    predicted = json_or_empty(row.get("predicted_json"))
    results = json_or_empty(row.get("field_results_json"))
    score = float(row.get("score", 0.0))
    score_class = "bad" if score < 0.6 else "warn"

    difficulty = row.get("difficulty")
    difficulty_badge = (
        badge(difficulty) if isinstance(difficulty, str) and difficulty.strip() else ""
    )
    model = row.get("model")
    model_badge = badge(model, "accent") if isinstance(model, str) and model.strip() else ""
    head = (
        '<div class="epi-card-head">'
        f'<span class="epi-case-id">{html.escape(str(row.get("case_id", "")))}</span>'
        f"{model_badge}"
        f'{badge(row.get("module", ""))}'
        f'{badge(row.get("schema_family", ""))}'
        f"{difficulty_badge}"
        f'<span class="epi-score {score_class}">{score:.2f}</span>'
        "</div>"
    )

    body = ""
    if case is not None:
        body += f"<p>{html.escape(case.scenario)}</p>"
        body += (
            f'<p class="muted"><strong>Target:</strong> '
            f"{html.escape(case.target_proposition)}</p>"
        )
    body += _fields_table(field_rows(expected, predicted, results))

    explanation = row.get("brief_explanation")
    if isinstance(explanation, str) and explanation.strip():
        body += f'<p class="muted"><em>Model: {html.escape(explanation)}</em></p>'

    return f'<div class="epi-card">{head}{body}</div>'
