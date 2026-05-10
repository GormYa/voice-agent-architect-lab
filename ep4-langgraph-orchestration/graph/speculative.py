from __future__ import annotations


def speculative_response(prefix: str, likely_intent: str) -> str:
    return f"{prefix} (speculative): {likely_intent}"
