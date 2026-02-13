import hashlib
from typing import Any

from chatbot_mvp.knowledge import policy_kb as _policy_kb

KB_MODE_GENERAL = _policy_kb.KB_MODE_GENERAL
KB_MODE_STRICT = _policy_kb.KB_MODE_STRICT
normalize_kb_mode = _policy_kb.normalize_kb_mode
parse_policy = _policy_kb.parse_policy
build_bm25_index = _policy_kb.build_bm25_index
retrieve = _policy_kb.retrieve
get_last_kb_debug = _policy_kb.get_last_kb_debug


def load_kb(text: str, name: str) -> dict[str, Any]:
    if hasattr(_policy_kb, "load_kb"):
        return _policy_kb.load_kb(text, name)

    normalized_text = str(text or "").strip()
    kb_name = str(name or "KB cargada").strip() or "KB cargada"
    chunks = parse_policy(normalized_text)
    index = build_bm25_index(chunks)
    kb_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
    return {
        "kb_name": kb_name,
        "kb_hash": kb_hash,
        "chunks": chunks,
        "index": index,
        "chunks_total": len(chunks),
    }

__all__ = [
    "KB_MODE_GENERAL",
    "KB_MODE_STRICT",
    "normalize_kb_mode",
    "load_kb",
    "parse_policy",
    "build_bm25_index",
    "retrieve",
    "get_last_kb_debug",
]
