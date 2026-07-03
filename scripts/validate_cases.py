"""Validate a JSONL case file and report problems.

Usage:
    python scripts/validate_cases.py
    python scripts/validate_cases.py data/cases/sample_cases.jsonl
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from epistemically.dataset import check_cases  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an Epistemically case file")
    parser.add_argument(
        "path",
        nargs="?",
        default=str(REPO_ROOT / "data" / "cases" / "sample_cases.jsonl"),
        help="Path to a JSONL case file",
    )
    args = parser.parse_args()

    cases, errors = check_cases(args.path)
    print(f"{args.path}: {len(cases)} valid case(s), {len(errors)} error(s)")

    if cases:
        by_module = Counter(case.module for case in cases)
        for module, count in sorted(by_module.items()):
            print(f"  {module}: {count}")

    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  - {err}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
