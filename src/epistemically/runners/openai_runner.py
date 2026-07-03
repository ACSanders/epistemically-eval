"""OpenAI runner: one fresh, independent API call per case.

Reads OPENAI_API_KEY (and optionally OPENAI_MODEL) from the environment /
.env. Each case gets its own message list — no shared conversation state.
"""

import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from epistemically.prompts import SYSTEM_PROMPT, build_prompt
from epistemically.schemas import EpistemicCase
from epistemically.scoring import score_case

FALLBACK_MODEL = "gpt-4o-mini"

_JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def resolve_model(cli_model: Optional[str] = None) -> str:
    """CLI flag wins, then OPENAI_MODEL from the environment, then fallback."""
    return cli_model or os.getenv("OPENAI_MODEL") or FALLBACK_MODEL


def parse_json_response(raw: str) -> Optional[Dict[str, Any]]:
    """Parse a model response as a JSON object; tolerate code fences."""
    text = _JSON_FENCE.sub("", raw).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def run_case(
    client: OpenAI,
    case: EpistemicCase,
    model: str,
    temperature: float = 0.0,
) -> Dict[str, Any]:
    """Run one case with a fresh API call and return a flat result row."""
    row: Dict[str, Any] = {
        "case_id": case.id,
        "module": case.module,
        "schema_family": case.schema_family,
        "variant_id": case.variant_id,
        "difficulty": case.difficulty,
        "model": model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "expected_json": json.dumps(case.expected),
    }

    started = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(case)},
            ],
        )
        raw = response.choices[0].message.content or ""
        row["error"] = ""
    except Exception as exc:  # keep the sweep going; record the failure
        raw = ""
        row["error"] = f"{type(exc).__name__}: {exc}"
    row["latency_s"] = round(time.perf_counter() - started, 3)
    row["raw_response"] = raw

    parsed = parse_json_response(raw) if raw else None
    row["parsed_ok"] = parsed is not None
    row["predicted_json"] = json.dumps(parsed) if parsed is not None else ""
    row["brief_explanation"] = (parsed or {}).get("brief_explanation", "")

    result = score_case(case, parsed)
    row["field_results_json"] = json.dumps(result.per_field)
    row["points"] = result.points
    row["max_points"] = result.max_points
    row["score"] = result.score
    return row


def run_cases(
    cases: List[EpistemicCase],
    model: Optional[str] = None,
    temperature: float = 0.0,
    verbose: bool = True,
) -> List[Dict[str, Any]]:
    """Run all cases against one OpenAI model, one independent call each."""
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set; copy .env.example to .env and fill it in")

    resolved = resolve_model(model)
    client = OpenAI()
    rows = []
    for i, case in enumerate(cases, start=1):
        row = run_case(client, case, resolved, temperature=temperature)
        rows.append(row)
        if verbose:
            status = f"score={row['score']:.2f}" if not row["error"] else f"ERROR {row['error']}"
            print(f"[{i}/{len(cases)}] {case.id} ({case.module}) {status}")
    return rows
