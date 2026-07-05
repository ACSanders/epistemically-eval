"""Provider-neutral helpers shared by the model runners."""

import json
import re
from typing import Any, Dict, Optional

_JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_json_response(raw: str) -> Optional[Dict[str, Any]]:
    """Parse a model response as a JSON object; tolerate code fences."""
    text = _JSON_FENCE.sub("", raw).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None
