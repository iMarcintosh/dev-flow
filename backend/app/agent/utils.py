"""Shared utilities for agent runners."""

from typing import Optional


def _collect_token_usage(messages: list) -> Optional[dict]:
    """Sum usage_metadata across all AIMessage turns.

    Prefers real token counts from API (Anthropic/OpenAI provide these via
    usage_metadata). Returns None if no data is available so callers can
    fall back to tiktoken estimation.
    """
    from langchain_core.messages import AIMessage as LCAIMessage

    total_input = total_output = 0
    found = False
    for m in messages:
        if isinstance(m, LCAIMessage) and getattr(m, "usage_metadata", None):
            meta = m.usage_metadata
            total_input += meta.get("input_tokens", 0)
            total_output += meta.get("output_tokens", 0)
            found = True
    if not found:
        return None
    return {
        "prompt": total_input,
        "completion": total_output,
        "total": total_input + total_output,
    }
