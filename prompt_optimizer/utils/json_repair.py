"""Robust JSON extraction and recovery utility for LLM outputs."""

import json
import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def extract_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """Extract and parse JSON from raw LLM output even if surrounded by prose or markdown."""
    if not raw_text or not raw_text.strip():
        return None

    cleaned = raw_text.strip()

    # 1. Direct parse attempt
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 2. Markdown code block extraction
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if code_block_match:
        content = code_block_match.group(1).strip()
        try:
            return json.loads(content)
        except Exception:
            cleaned = content

    # 3. Outer brace boundary extraction
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = cleaned[first_brace : last_brace + 1]
        try:
            return json.loads(candidate)
        except Exception:
            # 4. Remove trailing commas before closing brackets/braces
            sanitized = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                return json.loads(sanitized)
            except Exception as e:
                logger.debug(f"JSON recovery failed on extracted braces: {e}")

    logger.warning("Could not extract valid JSON from LLM response.")
    return None
