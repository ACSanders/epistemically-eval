"""Run an evaluation sweep: load cases, query the model, score, save CSV.

Usage:
    python scripts/run_eval.py
    python scripts/run_eval.py --model gpt-4o-mini --cases data/cases/sample_cases.jsonl
    python scripts/run_eval.py --cases data/cases/user_cases_draft.jsonl --output data/results/user_cases_results.csv
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from epistemically.dataset import load_cases  # noqa: E402
from epistemically.runners.openai_runner import resolve_model, run_cases  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an Epistemically eval sweep")
    parser.add_argument(
        "--cases",
        default=str(REPO_ROOT / "data" / "cases" / "sample_cases.jsonl"),
        help="Path to a JSONL case file",
    )
    parser.add_argument("--model", default=None, help="OpenAI model (default: OPENAI_MODEL from .env)")
    parser.add_argument(
        "--output",
        "--out",
        dest="output",
        default=None,
        help="Output CSV path (default: auto under data/results/)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Only run the first N cases")
    args = parser.parse_args()

    cases = load_cases(args.cases)
    if args.limit:
        cases = cases[: args.limit]
    print(f"Loaded {len(cases)} cases from {args.cases}")

    rows = run_cases(cases, model=args.model)
    df = pd.DataFrame(rows)

    if args.output:
        out_path = Path(args.output)
    else:
        model_slug = resolve_model(args.model).replace("/", "-").replace(":", "-")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        out_path = REPO_ROOT / "data" / "results" / f"results_{model_slug}_{stamp}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"\nSaved {len(df)} rows to {out_path}")
    print(f"Mean score: {df['score'].mean():.3f}")
    print(df.groupby("module")["score"].mean().round(3).to_string())


if __name__ == "__main__":
    main()
