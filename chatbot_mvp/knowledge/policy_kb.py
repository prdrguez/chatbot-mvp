from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

import streamlit as st
from rank_bm25 import BM25Okapi

_ARTICLE_RE = re.compile(
    r"(?im)^\s*art[i\u00ed]culo\s+([0-9]+[a-zA-Z0-9-]*)\b"
)
_TOKEN_RE = re.compile(r"[a-z0-9\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1]+", re.IGNORECASE)
_STOPWORDS = {
    "a",
    "al",
    "ante",
    "con",
    "contra",
    "de",
    "del",
    "desde",
    "el",
    "en",
    "entre",
    "es",
    "esta",
    "este",
    "ha",
    "la",
    "las",
    "lo",
    "los",
    "me",
    "mi",
    "mis",
    "o",
    "para",
    "por",
    "que",
    "se",
    "sin",
    "su",
    "sus",
    "te",
    "tu",
    "tus",
    "un",
    "una",
    "y",
    "ya",
}


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text).strip()


def _strip_accents(token: str) -> str:
    normalized = unicodedata.normalize("NFD", token)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def _tokenize(text: str) -> list[str]:
    tokens = []
    for raw_token in _TOKEN_RE.findall(text):
        token = _strip_accents(raw_token.lower())
        if len(token) < 3:
            continue
        if token in _STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def _chunk_by_size(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[dict[str, Any]]:
    normalized = _normalize_whitespace(text)
    if not normalized:
        return []

    chunks: list[dict[str, Any]] = []
    start = 0
    chunk_number = 1
    text_len = len(normalized)

    while start < text_len:
        end = min(text_len, start + chunk_size)
        if end < text_len:
            boundary = normalized.rfind(" ", start, end)
            if boundary > start + 100:
                end = boundary

        chunk_text = normalized[start:end].strip()
        if chunk_text:
            chunks.append(
                {
                    "chunk_id": len(chunks),
                    "fragment_id": chunk_number,
                    "article_id": None,
                    "source_label": f"Fragmento {chunk_number}",
                    "text": chunk_text,
                }
            )
            chunk_number += 1

        if end >= text_len:
            break

        start = max(0, end - overlap)

    return chunks


def _parse_policy_impl(text: str) -> list[dict[str, Any]]:
    clean_text = text.strip()
    if not clean_text:
        return []

    matches = list(_ARTICLE_RE.finditer(clean_text))
    if not matches:
        return _chunk_by_size(clean_text)

    chunks: list[dict[str, Any]] = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(clean_text)
        article_text = clean_text[start:end].strip()
        if not article_text:
            continue

        article_id = match.group(1)
        chunks.append(
            {
                "chunk_id": len(chunks),
                "fragment_id": None,
                "article_id": article_id,
                "source_label": f"Articulo {article_id}",
                "text": article_text,
            }
        )

    return chunks


@st.cache_data(show_spinner=False)
def _parse_policy_cached(text_hash: str, text: str) -> list[dict[str, Any]]:
    # text_hash is intentionally part of the cache key.
    _ = text_hash
    return _parse_policy_impl(text)


def parse_policy(text: str) -> list[dict[str, Any]]:
    if not text:
        return []
    text_hash = _hash_text(text)
    return _parse_policy_cached(text_hash, text)


@st.cache_resource(show_spinner=False)
def _build_bm25_index_cached(
    text_hash: str, corpus: tuple[str, ...]
) -> BM25Okapi | None:
    # text_hash is intentionally part of the cache key.
    _ = text_hash
    if not corpus:
        return None

    tokenized_corpus = []
    for entry in corpus:
        tokens = _tokenize(entry)
        tokenized_corpus.append(tokens if tokens else ["_"])
    return BM25Okapi(tokenized_corpus)


def build_bm25_index(chunks: list[dict[str, Any]]) -> BM25Okapi | None:
    if not chunks:
        return None

    corpus = tuple((chunk.get("text") or "").strip() for chunk in chunks)
    text_hash = _hash_text("\n".join(corpus))
    return _build_bm25_index_cached(text_hash, corpus)


def retrieve(
    query: str,
    index: BM25Okapi | None,
    chunks: list[dict[str, Any]],
    k: int = 4,
) -> list[dict[str, Any]]:
    if not query or not index or not chunks:
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []
    query_token_set = set(query_tokens)

    scores = index.get_scores(query_tokens)
    ranked = sorted(range(len(scores)), key=lambda i: float(scores[i]), reverse=True)

    results: list[dict[str, Any]] = []
    for idx in ranked:
        score = float(scores[idx])
        chunk_tokens = set(_tokenize(str(chunks[idx].get("text", ""))))
        overlap_count = len(query_token_set.intersection(chunk_tokens))
        if overlap_count == 0:
            continue
        chunk = dict(chunks[idx])
        chunk["score"] = score
        chunk["overlap"] = overlap_count
        results.append(chunk)
        if len(results) >= max(1, k):
            break

    return results
