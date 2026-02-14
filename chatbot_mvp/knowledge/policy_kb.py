from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter
from typing import Any

import streamlit as st

KB_MODE_GENERAL = "general"
KB_MODE_STRICT = "strict"
KB_DEFAULT_TOP_K = 4
KB_DEFAULT_MIN_SCORE = 0.18
KB_DEFAULT_MAX_CONTEXT_CHARS = 3200

_KB_MODE_STRICT_ALIASES = {
    "strict",
    "estricto",
    "solo kb",
    "solo kb (estricto)",
    "solo_kb",
    "solo-kb",
}
_KB_MODE_GENERAL_ALIASES = {
    "general",
    "modo general",
}

_ARTICLE_RE = re.compile(r"(?im)^\s*art[i\u00ed]culo\s+([0-9]+[a-zA-Z0-9-]*)\b")
_CHAPTER_RE = re.compile(r"(?im)^\s*(cap[i\u00ed]tulo|secci[o\u00f3]n|section)\s+([^\n]{1,80})")
_NUMBERED_HEADING_RE = re.compile(r"(?m)^\s*(\d+(?:\.\d+)*)\s*[.)-]?\s+([^\n]{3,120})$")
_TOKEN_RE = re.compile(r"[a-z0-9\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1]+", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")

_BM25_K1 = 1.5
_BM25_B = 0.75
_EXACT_MATCH_BONUS = 0.35

_LAST_KB_DEBUG: dict[str, Any] = {}
_INDEX_BUILD_COUNT = 0

_STOPWORDS = {
    # ES
    "a",
    "al",
    "algo",
    "ante",
    "con",
    "contra",
    "como",
    "cual",
    "cuales",
    "de",
    "del",
    "donde",
    "el",
    "ella",
    "ellas",
    "ellos",
    "en",
    "era",
    "es",
    "esa",
    "ese",
    "eso",
    "esta",
    "este",
    "esto",
    "fue",
    "ha",
    "hay",
    "la",
    "las",
    "le",
    "les",
    "lo",
    "los",
    "me",
    "mi",
    "mis",
    "muy",
    "no",
    "o",
    "para",
    "pero",
    "por",
    "que",
    "se",
    "si",
    "sin",
    "sobre",
    "su",
    "sus",
    "te",
    "tu",
    "tus",
    "un",
    "una",
    "uno",
    "y",
    "ya",
    # EN
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
}


def normalize_kb_mode(mode: Any) -> str:
    if isinstance(mode, str):
        raw = mode.strip().lower()
        if raw in _KB_MODE_STRICT_ALIASES:
            return KB_MODE_STRICT
        if raw in _KB_MODE_GENERAL_ALIASES:
            return KB_MODE_GENERAL
    return KB_MODE_GENERAL


def get_index_build_count() -> int:
    return int(_INDEX_BUILD_COUNT)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _normalize_spaces(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def _normalize_for_match(text: str) -> str:
    lowered = _strip_accents(text.lower())
    lowered = re.sub(r"[^\w\s]", " ", lowered)
    return _normalize_spaces(lowered)


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in _TOKEN_RE.findall(text):
        token = _strip_accents(raw.lower())
        if len(token) < 2:
            continue
        if token in _STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def _is_upper_heading(line: str) -> bool:
    raw = line.strip()
    if len(raw) < 5 or len(raw) > 90:
        return False
    letters = [ch for ch in raw if ch.isalpha()]
    if len(letters) < 5:
        return False
    ratio_upper = sum(1 for ch in letters if ch.isupper()) / float(len(letters))
    return ratio_upper >= 0.8


def _chunk_by_size(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 220,
    label_prefix: str = "Chunk",
) -> list[dict[str, Any]]:
    normalized = _normalize_spaces(text)
    if not normalized:
        return []

    chunks: list[dict[str, Any]] = []
    start = 0
    text_len = len(normalized)
    chunk_number = 1
    while start < text_len:
        end = min(text_len, start + chunk_size)
        if end < text_len:
            boundary = normalized.rfind(" ", start, end)
            if boundary > start + 120:
                end = boundary
        chunk_text = normalized[start:end].strip()
        if chunk_text:
            chunks.append(
                {
                    "chunk_id": len(chunks) + 1,
                    "article_id": None,
                    "section_id": None,
                    "source_label": f"{label_prefix} {chunk_number}",
                    "text": chunk_text,
                }
            )
            chunk_number += 1
        if end >= text_len:
            break
        start = max(0, end - overlap)
    return chunks


def _extract_headings(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    headings: list[dict[str, Any]] = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        article_match = _ARTICLE_RE.match(stripped)
        if article_match:
            article_id = article_match.group(1)
            headings.append(
                {
                    "line": idx,
                    "article_id": article_id,
                    "section_id": None,
                    "source_label": f"Articulo {article_id}",
                }
            )
            continue

        chapter_match = _CHAPTER_RE.match(stripped)
        if chapter_match:
            chapter_name = _normalize_spaces(chapter_match.group(0))
            headings.append(
                {
                    "line": idx,
                    "article_id": None,
                    "section_id": None,
                    "source_label": chapter_name[:110],
                }
            )
            continue

        numbered_match = _NUMBERED_HEADING_RE.match(stripped)
        if numbered_match:
            section_id = numbered_match.group(1)
            title = _normalize_spaces(numbered_match.group(2))
            source_label = f"Seccion {section_id}"
            if title:
                source_label = f"{source_label} - {title[:80]}"
            headings.append(
                {
                    "line": idx,
                    "article_id": None,
                    "section_id": section_id,
                    "source_label": source_label,
                }
            )
            continue

        if _is_upper_heading(stripped):
            headings.append(
                {
                    "line": idx,
                    "article_id": None,
                    "section_id": None,
                    "source_label": _normalize_spaces(stripped.title())[:110],
                }
            )

    return headings


def _chunk_by_sections(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    headings = _extract_headings(text)
    if not headings:
        return []

    chunks: list[dict[str, Any]] = []
    for idx, heading in enumerate(headings):
        start_line = heading["line"]
        end_line = headings[idx + 1]["line"] if idx + 1 < len(headings) else len(lines)
        section_text = "\n".join(lines[start_line:end_line]).strip()
        if not section_text:
            continue

        if len(section_text) > 1600:
            split_chunks = _chunk_by_size(
                section_text,
                chunk_size=1200,
                overlap=220,
                label_prefix=heading["source_label"],
            )
            for split in split_chunks:
                split["article_id"] = heading.get("article_id")
                split["section_id"] = heading.get("section_id")
                split["source_label"] = str(
                    split.get("source_label", heading["source_label"])
                )[:140]
                split["chunk_id"] = len(chunks) + 1
                chunks.append(split)
            continue

        chunks.append(
            {
                "chunk_id": len(chunks) + 1,
                "article_id": heading.get("article_id"),
                "section_id": heading.get("section_id"),
                "source_label": heading["source_label"],
                "text": section_text,
            }
        )

    return chunks


def _parse_policy_impl(text: str) -> list[dict[str, Any]]:
    clean_text = text.strip()
    if not clean_text:
        return []

    section_chunks = _chunk_by_sections(clean_text)
    if section_chunks:
        return section_chunks

    return _chunk_by_size(clean_text, chunk_size=1200, overlap=220, label_prefix="Chunk")


@st.cache_data(show_spinner=False)
def _parse_policy_cached(text_hash: str, text: str) -> list[dict[str, Any]]:
    _ = text_hash
    return _parse_policy_impl(text)


def parse_policy(text: str) -> list[dict[str, Any]]:
    if not text:
        return []
    return _parse_policy_cached(_hash_text(text), text)


def _ensure_prefixed_source(kb_name: str, source_label: str) -> str:
    source = source_label.strip() or "Chunk"
    prefix = f"{kb_name} | "
    return source if source.startswith(prefix) else f"{prefix}{source}"


def _coerce_chunk(chunk: dict[str, Any], kb_name: str, position: int) -> dict[str, Any]:
    source_label = str(chunk.get("source_label", "")).strip() or f"Chunk {position}"
    prefixed_source = _ensure_prefixed_source(kb_name, source_label)
    chunk_id = chunk.get("chunk_id") or chunk.get("id") or position
    article_id = chunk.get("article_id")
    section_id = chunk.get("section_id")
    title = str(chunk.get("title", "")).strip()
    if not title:
        if article_id:
            title = f"Articulo {article_id}"
        elif section_id:
            title = f"Seccion {section_id}"
        else:
            title = source_label

    return {
        "id": int(chunk_id) if str(chunk_id).isdigit() else chunk_id,
        "chunk_id": int(chunk_id) if str(chunk_id).isdigit() else chunk_id,
        "title": title,
        "article_id": article_id,
        "section_id": section_id,
        "source_label": prefixed_source,
        "source": prefixed_source,
        "text": str(chunk.get("text", "")).strip(),
    }


def _build_index_payload(
    chunks: list[dict[str, Any]],
    kb_name: str,
    kb_hash: str,
    kb_updated_at: str,
) -> dict[str, Any]:
    tf_docs: list[dict[str, int]] = []
    doc_len: list[int] = []
    normalized_texts: list[str] = []
    df_counter: Counter[str] = Counter()

    for chunk in chunks:
        text = str(chunk.get("text", ""))
        tokens = _tokenize(text)
        tf = dict(Counter(tokens))
        tf_docs.append(tf)
        doc_len.append(len(tokens))
        normalized_texts.append(_normalize_for_match(text))
        for term in tf:
            df_counter[term] += 1

    doc_count = len(chunks)
    avgdl = (sum(doc_len) / float(doc_count)) if doc_count else 0.0

    return {
        "index_version": 2,
        "kb_name": kb_name,
        "kb_hash": kb_hash,
        "kb_updated_at": kb_updated_at,
        "doc_count": doc_count,
        "avgdl": avgdl,
        "doc_len": doc_len,
        "df": dict(df_counter),
        "tf_docs": tf_docs,
        "normalized_texts": normalized_texts,
        "k1": _BM25_K1,
        "b": _BM25_B,
        "exact_match_bonus": _EXACT_MATCH_BONUS,
        "chunks": chunks,
    }


@st.cache_data(show_spinner=False)
def _build_kb_index_cached(
    kb_hash: str,
    kb_name: str,
    kb_updated_at: str,
    text: str,
) -> dict[str, Any]:
    global _INDEX_BUILD_COUNT
    chunks_raw = parse_policy(text)
    chunks = [_coerce_chunk(chunk, kb_name, pos + 1) for pos, chunk in enumerate(chunks_raw)]
    index = _build_index_payload(chunks, kb_name, kb_hash, kb_updated_at)
    _INDEX_BUILD_COUNT += 1
    return {
        "kb_name": kb_name,
        "kb_hash": kb_hash,
        "kb_updated_at": kb_updated_at,
        "chunks": chunks,
        "index": index,
        "chunks_total": len(chunks),
    }


def build_kb_index(
    text: str,
    kb_name: str,
    kb_updated_at: str | int | None = None,
) -> dict[str, Any]:
    normalized_text = str(text or "").strip()
    normalized_name = str(kb_name or "KB cargada").strip() or "KB cargada"
    normalized_updated_at = str(kb_updated_at or "")
    kb_hash = _hash_text(normalized_text)
    return _build_kb_index_cached(
        kb_hash,
        normalized_name,
        normalized_updated_at,
        normalized_text,
    )


def build_bm25_index(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    normalized_chunks = [
        _coerce_chunk(chunk, "KB cargada", pos + 1)
        for pos, chunk in enumerate(chunks or [])
    ]
    chunks_fingerprint = "\n".join(
        f"{item.get('source_label', '')}::{item.get('text', '')}" for item in normalized_chunks
    )
    kb_hash = _hash_text(chunks_fingerprint)
    return _build_index_payload(
        normalized_chunks,
        "KB cargada",
        kb_hash,
        "",
    )


def load_kb(
    text: str,
    name: str,
    kb_updated_at: str | int | None = None,
) -> dict[str, Any]:
    return build_kb_index(text=text, kb_name=name, kb_updated_at=kb_updated_at)


def _set_last_kb_debug(payload: dict[str, Any]) -> None:
    global _LAST_KB_DEBUG
    _LAST_KB_DEBUG = dict(payload)


def get_last_kb_debug() -> dict[str, Any]:
    return dict(_LAST_KB_DEBUG)


def _bm25_idf(doc_count: int, doc_freq: int) -> float:
    numerator = max(0.0, doc_count - doc_freq + 0.5)
    denominator = doc_freq + 0.5
    return math.log1p(numerator / max(1e-9, denominator))


def _chunk_section(chunk: dict[str, Any]) -> str:
    article_id = chunk.get("article_id")
    if article_id:
        return f"Articulo {article_id}"
    section_id = chunk.get("section_id")
    if section_id:
        return f"Seccion {section_id}"
    title = str(chunk.get("title", "")).strip()
    if title:
        return title
    return str(chunk.get("source_label", "")).strip()


def _score_chunk(
    query_terms: list[str],
    query_norm: str,
    tf: dict[str, int],
    doc_len: int,
    avgdl: float,
    df: dict[str, int],
    doc_count: int,
    normalized_text: str,
) -> tuple[float, list[str], bool]:
    matched_terms: list[str] = []
    score = 0.0
    norm_denominator = max(1.0, avgdl)

    for term in query_terms:
        tf_value = int(tf.get(term, 0))
        if tf_value <= 0:
            continue
        matched_terms.append(term)
        idf = _bm25_idf(doc_count, int(df.get(term, 0)))
        denominator = tf_value + (_BM25_K1 * (1 - _BM25_B + _BM25_B * (doc_len / norm_denominator)))
        score += idf * ((tf_value * (_BM25_K1 + 1)) / max(1e-9, denominator))

    exact_match = bool(query_norm and query_norm in normalized_text)
    if exact_match:
        score += _EXACT_MATCH_BONUS

    return score, matched_terms, exact_match


def retrieve_evidence(
    query: str,
    index: dict[str, Any],
    top_k: int = KB_DEFAULT_TOP_K,
    min_score: float = KB_DEFAULT_MIN_SCORE,
    kb_name: str = "",
) -> list[dict[str, Any]]:
    chunks = index.get("chunks") if isinstance(index, dict) else []
    chunks = chunks if isinstance(chunks, list) else []
    if not query or not chunks:
        _set_last_kb_debug(
            {
                "query": str(query or ""),
                "kb_name": kb_name,
                "chunks_total": len(chunks or []),
                "retrieved_count": 0,
                "reason": "no_query_or_chunks",
                "top_candidates": [],
                "top_k": int(max(1, top_k)),
                "min_score": float(min_score),
                "index_build_count": get_index_build_count(),
            }
        )
        return []

    tf_docs = index.get("tf_docs") if isinstance(index.get("tf_docs"), list) else []
    doc_len = index.get("doc_len") if isinstance(index.get("doc_len"), list) else []
    normalized_texts = (
        index.get("normalized_texts")
        if isinstance(index.get("normalized_texts"), list)
        else []
    )
    df = index.get("df") if isinstance(index.get("df"), dict) else {}
    doc_count = int(index.get("doc_count", len(chunks)))
    avgdl = float(index.get("avgdl", 0.0))

    query_norm = _normalize_for_match(query)
    query_terms = sorted(set(_tokenize(query)))
    if not query_terms and not query_norm:
        _set_last_kb_debug(
            {
                "query": str(query),
                "kb_name": kb_name,
                "chunks_total": len(chunks),
                "retrieved_count": 0,
                "reason": "empty_query_terms",
                "top_candidates": [],
                "top_k": int(max(1, top_k)),
                "min_score": float(min_score),
                "index_build_count": get_index_build_count(),
            }
        )
        return []

    candidates: list[dict[str, Any]] = []
    for idx, chunk in enumerate(chunks):
        tf = tf_docs[idx] if idx < len(tf_docs) and isinstance(tf_docs[idx], dict) else {}
        dl = int(doc_len[idx]) if idx < len(doc_len) else len(_tokenize(str(chunk.get("text", ""))))
        normalized_text = (
            str(normalized_texts[idx])
            if idx < len(normalized_texts)
            else _normalize_for_match(str(chunk.get("text", "")))
        )
        score, matched_terms, exact_match = _score_chunk(
            query_terms,
            query_norm,
            tf,
            dl,
            avgdl,
            df,
            doc_count,
            normalized_text,
        )
        if score <= 0 and not exact_match:
            continue

        preview = _normalize_spaces(str(chunk.get("text", "")))[:220]
        enriched = {
            **chunk,
            "score": float(score),
            "overlap": len(matched_terms),
            "match_type": "bm25_exact" if exact_match else "bm25",
            "matched_terms": matched_terms,
            "section": _chunk_section(chunk),
            "preview": preview,
            "snippet": preview,
        }
        candidates.append(enriched)

    candidates.sort(
        key=lambda item: (
            float(item.get("score", 0.0)),
            int(item.get("overlap", 0)),
        ),
        reverse=True,
    )

    limit = int(max(1, top_k))
    threshold = float(min_score)
    selected = [item for item in candidates if float(item.get("score", 0.0)) >= threshold][:limit]

    reason = "bm25"
    if not candidates:
        reason = "no_hits"
    elif not selected:
        reason = "below_min_score"

    debug_candidates = candidates[: max(limit, 6)]
    _set_last_kb_debug(
        {
            "query": query,
            "kb_name": kb_name,
            "chunks_total": len(chunks),
            "retrieved_count": len(selected),
            "reason": reason,
            "top_candidates": debug_candidates,
            "top_k": limit,
            "min_score": threshold,
            "index_build_count": get_index_build_count(),
        }
    )

    return selected


def retrieve(
    query: str,
    index: dict[str, Any],
    chunks: list[dict[str, Any]],
    k: int = KB_DEFAULT_TOP_K,
    kb_name: str = "",
    min_score: float = KB_DEFAULT_MIN_SCORE,
) -> list[dict[str, Any]]:
    runtime_index = index if isinstance(index, dict) else {}
    runtime_chunks = runtime_index.get("chunks") if isinstance(runtime_index.get("chunks"), list) else []

    if not runtime_chunks and chunks:
        normalized_name = str(kb_name or "KB cargada").strip() or "KB cargada"
        normalized_chunks = [
            _coerce_chunk(chunk, normalized_name, pos + 1)
            for pos, chunk in enumerate(chunks)
        ]
        chunks_fingerprint = "\n".join(
            f"{item.get('source_label', '')}::{item.get('text', '')}" for item in normalized_chunks
        )
        runtime_index = _build_index_payload(
            normalized_chunks,
            normalized_name,
            _hash_text(chunks_fingerprint),
            "",
        )

    return retrieve_evidence(
        query=query,
        index=runtime_index,
        top_k=k,
        min_score=min_score,
        kb_name=kb_name,
    )
