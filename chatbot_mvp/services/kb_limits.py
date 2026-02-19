from __future__ import annotations

from typing import Any, MutableMapping

KB_MAX_CHARS = 120000


def limit_kb_text_size(text: str, max_chars: int = KB_MAX_CHARS) -> dict[str, Any]:
    raw_text = str(text or "")
    resolved_max = max(1000, int(max_chars))
    original_chars = len(raw_text)
    if original_chars <= resolved_max:
        return {
            "text": raw_text,
            "truncated": False,
            "original_chars": original_chars,
            "used_chars": original_chars,
            "max_chars": resolved_max,
        }

    limited_text = raw_text[:resolved_max]
    return {
        "text": limited_text,
        "truncated": True,
        "original_chars": original_chars,
        "used_chars": len(limited_text),
        "max_chars": resolved_max,
    }


def apply_kb_limit_to_session(
    session_state: MutableMapping[str, Any],
    text: str,
    max_chars: int = KB_MAX_CHARS,
) -> str:
    result = limit_kb_text_size(text=text, max_chars=max_chars)
    session_state["kb_truncated"] = bool(result["truncated"])
    session_state["kb_original_chars"] = int(result["original_chars"])
    session_state["kb_max_chars"] = int(result["max_chars"])
    return str(result["text"])
