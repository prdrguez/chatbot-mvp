from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

import streamlit as st

_ARTICLE_RE = re.compile(r"(?im)^\s*art[i\u00ed]culo\s+([0-9]+[a-zA-Z0-9-]*)\b")
_WS_RE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"[a-z0-9\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1]+", re.IGNORECASE)
_STOPWORDS = {
    "a",
    "al",
    "and",
    "are",
    "as",
    "at",
    "be",
    "con",
    "como",
    "de",
    "del",
    "do",
    "el",
    "en",
    "es",
    "for",
    "from",
    "in",
    "is",
    "la",
    "las",
    "los",
    "no",
    "of",
    "on",
    "or",
    "para",
    "por",
    "que",
    "se",
    "si",
    "sin",
    "the",
    "to",
    "un",
    "una",
    "with",
    "y",
}


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_spaces(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _tokenize(text: str) -> list[str]:
    tokens = []
    for raw in _TOKEN_RE.findall(text):
        token = _strip_accents(raw.lower())
        if len(token) < 3:
            continue
        if token in _STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def _chunk_by_size(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    normalized = _normalize_spaces(text)
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    total = len(normalized)
    while start < total:
        end = min(total, start + chunk_size)
        if end < total:
            boundary = normalized.rfind(" ", start, end)
            if boundary > start + 120:
                end = boundary
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= total:
            break
        start = max(0, end - overlap)
    return chunks


def _chunk_text(text: str) -> list[str]:
    raw_paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
    if not raw_paragraphs:
        return []
    if len(raw_paragraphs) == 1:
        return _chunk_by_size(raw_paragraphs[0])

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    min_target = 750
    max_target = 1150
    for paragraph in raw_paragraphs:
        paragraph_len = len(paragraph)
        if paragraph_len > max_target:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_len = 0
            chunks.extend(_chunk_by_size(paragraph))
            continue

        candidate_len = current_len + paragraph_len + (2 if current else 0)
        if candidate_len <= max_target or current_len < min_target:
            current.append(paragraph)
            current_len = candidate_len
            continue

        chunks.append("\n\n".join(current))
        current = [paragraph]
        current_len = paragraph_len

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def _extract_source_label(chunk_text: str, index: int) -> str:
    article_match = _ARTICLE_RE.search(chunk_text)
    if article_match:
        return f"Articulo {article_match.group(1)}"

    first_line = chunk_text.splitlines()[0].strip() if chunk_text.splitlines() else ""
    if 3 <= len(first_line) <= 96:
        return first_line
    return f"Chunk {index}"


def _load_kb_impl(text: str, name: str) -> dict[str, Any]:
    chunks_text = _chunk_text(text)
    chunks: list[dict[str, Any]] = []
    for idx, chunk_text in enumerate(chunks_text, start=1):
        source = _extract_source_label(chunk_text, idx)
        chunks.append(
            {
                "chunk_id": idx,
                "source": source,
                "text": chunk_text,
                "tokens": tuple(_tokenize(chunk_text)),
            }
        )
    return {"name": name, "chunks": chunks, "chunk_count": len(chunks)}


@st.cache_data(show_spinner=False)
def _load_kb_cached(text_hash: str, text: str, name: str) -> dict[str, Any]:
    _ = text_hash
    return _load_kb_impl(text, name)


def load_kb(text: str, name: str) -> dict[str, Any]:
    clean_text = text.strip()
    if not clean_text:
        return {"name": name, "chunks": [], "chunk_count": 0}
    return _load_kb_cached(_hash_text(clean_text), clean_text, name)


def retrieve(
    query: str, kb_index: dict[str, Any], top_k: int = 4, min_overlap: int = 1
) -> list[dict[str, Any]]:
    if not query or not kb_index:
        return []
    chunks = kb_index.get("chunks", [])
    if not chunks:
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []
    query_token_set = set(query_tokens)

    matches: list[dict[str, Any]] = []
    for chunk in chunks:
        chunk_tokens = set(chunk.get("tokens", ()))
        overlap = query_token_set.intersection(chunk_tokens)
        overlap_count = len(overlap)
        if overlap_count < min_overlap:
            continue
        score = overlap_count / float(len(query_tokens))
        matches.append(
            {
                "chunk_id": chunk["chunk_id"],
                "source": chunk["source"],
                "text": chunk["text"],
                "score": score,
                "overlap_count": overlap_count,
                "query_token_count": len(query_tokens),
                "matched_tokens": sorted(overlap),
            }
        )

    matches.sort(
        key=lambda item: (item["overlap_count"], item["score"], -item["chunk_id"]),
        reverse=True,
    )
    return matches[: max(1, top_k)]
