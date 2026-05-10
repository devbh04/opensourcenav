"""
Utility helpers for extracting structured data from LLM responses.
"""
import json
import re
import logging

logger = logging.getLogger(__name__)


def extract_json(text: str) -> dict | list | None:
    """
    Robustly extract JSON from an LLM response.
    
    Handles common issues:
      - Markdown fences (```json ... ```)
      - Leading/trailing text around JSON
      - Gemini thinking mode responses
      - Empty responses
    
    Returns parsed JSON or None if extraction fails.
    """
    if not text or not text.strip():
        logger.warning("[extract_json] Empty response text")
        return None

    text = text.strip()

    # 1. Remove markdown code fences
    if "```" in text:
        # Extract content between first pair of fences
        parts = text.split("```")
        if len(parts) >= 3:
            inner = parts[1]
            # Remove language identifier if present (e.g., "json\n")
            if inner.startswith("json"):
                inner = inner[4:]
            elif inner.startswith("JSON"):
                inner = inner[4:]
            text = inner.strip()

    # 2. Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. Try to find JSON object or array with regex
    # Look for outermost { ... } or [ ... ]
    for pattern in [
        r'(\{[\s\S]*\})',   # JSON object
        r'(\[[\s\S]*\])',   # JSON array
    ]:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue

    logger.warning(f"[extract_json] Could not extract JSON from: {text[:200]}...")
    return None
