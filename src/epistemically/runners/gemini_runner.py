"""Gemini runner: one fresh, independent API call per case.

Reads GEMINI_API_KEY (and optionally GEMINI_MODEL) from the environment /
.env. Uses the exact same system prompt and per-case prompt as the OpenAI
and Anthropic runners, and feeds raw response text through the same shared
JSON parser and scorer, so results are directly comparable across providers.
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

from epistemically.prompts import SYSTEM_PROMPT, build_prompt
from epistemically.runners.common import parse_json_response
from epistemically.schemas import EpistemicCase
from epistemically.scoring import score_case

FALLBACK_MODEL = "gemini-2.5-pro"

# Gemini 2.5 models think by default and thinking tokens count against
# max_output_tokens, so short JSON answers still need generous headroom.
DEFAULT_MAX_OUTPUT_TOKENS = 8192


def resolve_model(cli_model: Optional[str] = None) -> str:
    """CLI flag wins, then GEMINI_MODEL from the environment, then fallback."""
    return cli_model or os.getenv("GEMINI_MODEL") or FALLBACK_MODEL


def run_case(
    client: "genai.Client",
    case: EpistemicCase,
    model: str,
    temperature: float = 0.0,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
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

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        response_mime_type="application/json",
    )

    started = time.perf_counter()
    try:
        response = client.models.generate_content(
            model=model,
            contents=build_prompt(case),
            config=config,
        )
        raw = response.text or ""
        finish = None
        if response.candidates:
            finish = getattr(response.candidates[0], "finish_reason", None)
        finish_name = getattr(finish, "name", str(finish)) if finish is not None else None
        if finish_name in (None, "STOP"):
            row["error"] = ""
        else:
            # Safety blocks and truncation surface here instead of crashing
            # the sweep.
            row["error"] = f"finish_reason: {finish_name}"
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
    """Run all cases against one Gemini model, one independent call each."""
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError(
            "GEMINI_API_KEY is not set; add it to .env or the environment"
        )

    resolved = resolve_model(model)
    client = genai.Client()
    rows = []
    for i, case in enumerate(cases, start=1):
        row = run_case(client, case, resolved, temperature=temperature)
        rows.append(row)
        if verbose:
            status = f"score={row['score']:.2f}" if not row["error"] else f"ERROR {row['error']}"
            print(f"[{i}/{len(cases)}] {case.id} ({case.module}) {status}")
    return rows
