"""Anthropic runner: one fresh, independent API call per case.

Reads ANTHROPIC_API_KEY (and optionally ANTHROPIC_MODEL) from the
environment / .env. Uses the exact same system prompt and per-case prompt as
the OpenAI runner, and feeds raw response text through the same JSON parser
and scorer, so results are directly comparable across providers.
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from anthropic import Anthropic

from epistemically.prompts import SYSTEM_PROMPT, build_prompt
from epistemically.runners.common import parse_json_response
from epistemically.schemas import EpistemicCase
from epistemically.scoring import score_case

FALLBACK_MODEL = "claude-haiku-4-5"

# Room for short JSON answers plus any provider-default reasoning tokens,
# which count against max_tokens on newer Claude models.
DEFAULT_MAX_TOKENS = 4096

# Claude models from Opus 4.7 / Sonnet 5 / Fable 5 onward reject non-default
# sampling parameters (400), while Haiku 4.5 and the 4.6 family still accept
# temperature=0 for deterministic behavior.
_NO_TEMPERATURE_PREFIXES = (
    "claude-opus-4-7",
    "claude-opus-4-8",
    "claude-sonnet-5",
    "claude-fable",
    "claude-mythos",
)


def resolve_model(cli_model: Optional[str] = None) -> str:
    """CLI flag wins, then ANTHROPIC_MODEL from the environment, then fallback."""
    return cli_model or os.getenv("ANTHROPIC_MODEL") or FALLBACK_MODEL


def _supports_custom_temperature(model: str) -> bool:
    return not model.startswith(_NO_TEMPERATURE_PREFIXES)


def run_case(
    client: Anthropic,
    case: EpistemicCase,
    model: str,
    temperature: float = 0.0,
    max_tokens: int = DEFAULT_MAX_TOKENS,
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

    request: Dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": build_prompt(case)}],
    }
    if _supports_custom_temperature(model):
        request["temperature"] = temperature

    started = time.perf_counter()
    try:
        response = client.messages.create(**request)
        raw = "".join(
            block.text for block in response.content if block.type == "text"
        )
        if response.stop_reason == "end_turn":
            row["error"] = ""
        else:
            # Refusals and truncation surface here instead of crashing the sweep.
            row["error"] = f"stop_reason: {response.stop_reason}"
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
    """Run all cases against one Anthropic model, one independent call each."""
    load_dotenv()
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set; add it to .env or the environment"
        )

    resolved = resolve_model(model)
    client = Anthropic()
    rows = []
    for i, case in enumerate(cases, start=1):
        row = run_case(client, case, resolved, temperature=temperature)
        rows.append(row)
        if verbose:
            status = f"score={row['score']:.2f}" if not row["error"] else f"ERROR {row['error']}"
            print(f"[{i}/{len(cases)}] {case.id} ({case.module}) {status}")
    return rows
