from __future__ import annotations

import difflib
import hashlib
import math
import re
import unicodedata
from collections import Counter
from typing import Any

import streamlit as st

KB_MODE_GENERAL = "general"
KB_MODE_STRICT = "strict"
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
_AGE_RE = re.compile(r"\b(\d{1,2})\s*a(?:ñ|n)os\b", re.IGNORECASE)
_LAST_KB_DEBUG: dict[str, Any] = {}
_BM25_K1 = 1.5
_BM25_B = 0.75
_EXACT_SUBSTRING_BONUS = 0.28
_CHILD_TERMS = (
    "trabajo infantil",
    "esclavitud moderna",
    "trabajo forzado",
    "menores",
    "edad minima",
    "derechos humanos",
)
_CHILD_TRIGGER_TERMS = ("menor", "nino", "niño", "nene", "adolescente", "hijo", "hija")
_STOPWORDS = {
    "a",
    "al",
    "algo",
    "ante",
    "con",
    "contra",
    "cual",
    "cuales",
    "de",
    "del",
    "donde",
    "el",
    "en",
    "es",
    "esa",
    "ese",
    "esta",
    "este",
    "hay",
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
    "y",
}


def normalize_kb_mode(mode: Any) -> str:
    if isinstance(mode, str):
        raw = mode.strip().lower()
        if raw in _KB_MODE_STRICT_ALIASES:
            return KB_MODE_STRICT
        if raw in _KB_MODE_GENERAL_ALIASES:
            return KB_MODE_GENERAL
    return KB_MODE_GENERAL


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
        if len(token) < 3:
            continue
        if token in _STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def _contains_child_trigger(normalized_query: str) -> bool:
    return any(term in normalized_query for term in _CHILD_TRIGGER_TERMS)


def _requires_exact_age_query(normalized_query: str) -> bool:
    if "edad minima exacta" in normalized_query:
        return True
    if "edad exacta" in normalized_query:
        return True
    if "exacta" in normalized_query and "edad" in normalized_query:
        return True
    return False


def expand_query(query: str) -> dict[str, Any]:
    original = str(query or "").strip()
    normalized_query = _normalize_for_match(original)
    ages = [int(match.group(1)) for match in _AGE_RE.finditer(normalized_query)]
    detected_child_context = bool(ages and min(ages) <= 15) or _contains_child_trigger(
        normalized_query
    )

    tags: list[str] = []
    extra_terms: list[str] = []
    if detected_child_context:
        tags.append("child_labor")
        extra_terms.extend(
            [
                "trabajo infantil",
                "esclavitud moderna",
                "trabajo forzado",
                "menores",
                "edad minima",
                "derechos humanos",
            ]
        )
    deduped_extra = list(dict.fromkeys(extra_terms))
    expanded_text = original
    if deduped_extra:
        expanded_text = f"{original} {' '.join(deduped_extra)}".strip()
    expanded_normalized = _normalize_for_match(expanded_text)
    expanded_terms = _tokenize(expanded_text)

    return {
        "original_query": original,
        "normalized_query": normalized_query,
        "expanded_text": expanded_text,
        "expanded_normalized": expanded_normalized,
        "query_terms": _tokenize(original),
        "expanded_terms": expanded_terms,
        "tags": tags,
        "intent": tags[0] if tags else "",
        "age_values": ages,
        "requires_exact_age": _requires_exact_age_query(normalized_query),
    }


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
                split["source_label"] = str(split.get("source_label", heading["source_label"]))[:140]
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


def load_kb(text: str, name: str) -> dict[str, Any]:
    normalized_text = str(text or "").strip()
    kb_name = str(name or "KB cargada").strip() or "KB cargada"
    kb_hash = _hash_text(normalized_text)
    chunks = parse_policy(normalized_text)
    index = build_bm25_index(chunks)
    return {
        "kb_name": kb_name,
        "kb_hash": kb_hash,
        "chunks": chunks,
        "index": index,
        "chunks_total": len(chunks),
    }


def _set_last_kb_debug(payload: dict[str, Any]) -> None:
    global _LAST_KB_DEBUG
    _LAST_KB_DEBUG = dict(payload)


def get_last_kb_debug() -> dict[str, Any]:
    return dict(_LAST_KB_DEBUG)


@st.cache_resource(show_spinner=False)
def _build_index_cached(text_hash: str, corpus: tuple[str, ...]) -> dict[str, Any]:
    _ = text_hash
    token_lists = [tuple(_tokenize(text)) for text in corpus]
    token_sets = [set(tokens) for tokens in token_lists]
    normalized_texts = [ _normalize_for_match(text) for text in corpus ]
    doc_len = [len(tokens) for tokens in token_lists]
    avgdl = (sum(doc_len) / float(len(doc_len))) if doc_len else 0.0
    tf_docs = [dict(Counter(tokens)) for tokens in token_lists]
    df: dict[str, int] = {}
    for token_set in token_sets:
        for token in token_set:
            df[token] = df.get(token, 0) + 1
    return {
        "token_lists": token_lists,
        "token_sets": token_sets,
        "normalized_texts": normalized_texts,
        "doc_len": doc_len,
        "avgdl": avgdl,
        "tf_docs": tf_docs,
        "df": df,
    }


def build_bm25_index(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    if not chunks:
        return {
            "token_lists": [],
            "token_sets": [],
            "normalized_texts": [],
            "doc_len": [],
            "avgdl": 0.0,
            "tf_docs": [],
            "df": {},
        }
    corpus = tuple(str(chunk.get("text", "")) for chunk in chunks)
    text_hash = _hash_text("\n".join(corpus))
    return _build_index_cached(text_hash, corpus)


def _bm25_idf(term: str, index: dict[str, Any], total_docs: int) -> float:
    df_map = index.get("df", {})
    if not isinstance(df_map, dict):
        return 0.0
    df_value = int(df_map.get(term, 0))
    if total_docs <= 0:
        return 0.0
    numerator = total_docs - df_value + 0.5
    denominator = df_value + 0.5
    if numerator <= 0 or denominator <= 0:
        return 0.0
    # Keep positive IDF values and avoid extreme spikes in tiny corpora.
    return max(0.0, float(math.log1p(numerator / denominator)))


def _rank_by_bm25(
    query_meta: dict[str, Any],
    index: dict[str, Any],
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    expanded_tokens = list(dict.fromkeys(query_meta.get("expanded_terms", [])))
    if not expanded_tokens:
        return []

    tf_docs = index.get("tf_docs", [])
    doc_len = index.get("doc_len", [])
    normalized_texts = index.get("normalized_texts", [])
    avgdl = float(index.get("avgdl", 0.0) or 0.0)
    total_docs = len(chunks)

    ranked: list[dict[str, Any]] = []
    for idx, chunk in enumerate(chunks):
        tf = tf_docs[idx] if idx < len(tf_docs) and isinstance(tf_docs[idx], dict) else {}
        dl = float(doc_len[idx]) if idx < len(doc_len) else float(len(_tokenize(str(chunk.get("text", "")))))
        normalized_text = normalized_texts[idx] if idx < len(normalized_texts) else ""
        score = 0.0
        matched_terms: list[str] = []

        for term in expanded_tokens:
            tf_value = float(tf.get(term, 0))
            if tf_value <= 0:
                continue
            matched_terms.append(term)
            idf = _bm25_idf(term, index, total_docs)
            denominator = tf_value + _BM25_K1 * (1 - _BM25_B + _BM25_B * (dl / max(1.0, avgdl or 1.0)))
            score += idf * ((tf_value * (_BM25_K1 + 1)) / max(0.0001, denominator))

        exact_bonus = 0.0
        expanded_normalized = str(query_meta.get("expanded_normalized", ""))
        if expanded_normalized and expanded_normalized in normalized_text:
            exact_bonus = _EXACT_SUBSTRING_BONUS
            score += exact_bonus

        if score <= 0:
            continue

        ranked.append(
            {
                **chunk,
                "score": score,
                "overlap": len(matched_terms),
                "match_type": "bm25_exact" if exact_bonus > 0 else "bm25",
                "matched_terms": matched_terms,
            }
        )

    ranked.sort(
        key=lambda item: (float(item.get("score", 0.0)), int(item.get("overlap", 0))),
        reverse=True,
    )
    return ranked


def _rank_by_token_overlap(
    query_tokens: list[str],
    index: dict[str, Any],
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not query_tokens:
        return []
    query_set = set(query_tokens)
    ranked: list[dict[str, Any]] = []
    for idx, chunk in enumerate(chunks):
        chunk_set = index["token_sets"][idx] if idx < len(index["token_sets"]) else set()
        overlap = query_set.intersection(chunk_set)
        overlap_count = len(overlap)
        if overlap_count <= 0:
            continue
        score = overlap_count / float(max(1, len(query_set)))
        ranked.append(
            {
                **chunk,
                "score": score,
                "overlap": overlap_count,
                "match_type": "token_overlap",
                "matched_terms": sorted(overlap),
            }
        )
    ranked.sort(
        key=lambda item: (int(item.get("overlap", 0)), float(item.get("score", 0.0))),
        reverse=True,
    )
    return ranked


def _rank_by_substring(
    query_tokens: list[str],
    index: dict[str, Any],
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not query_tokens:
        return []
    ranked: list[dict[str, Any]] = []
    query_terms = sorted(set(query_tokens), key=len, reverse=True)
    for idx, chunk in enumerate(chunks):
        normalized_text = index["normalized_texts"][idx] if idx < len(index["normalized_texts"]) else ""
        if not normalized_text:
            continue
        matched = [term for term in query_terms if term in normalized_text]
        if not matched:
            continue
        score = len(matched) / float(max(1, len(query_terms)))
        ranked.append(
            {
                **chunk,
                "score": score,
                "overlap": len(matched),
                "match_type": "substring",
                "matched_terms": matched,
            }
        )
    ranked.sort(
        key=lambda item: (int(item.get("overlap", 0)), float(item.get("score", 0.0))),
        reverse=True,
    )
    return ranked


def _rank_by_sequence_match(
    query: str,
    index: dict[str, Any],
    chunks: list[dict[str, Any]],
    min_ratio: float = 0.28,
) -> list[dict[str, Any]]:
    query_norm = _normalize_for_match(query)
    if not query_norm:
        return []
    best_item: dict[str, Any] | None = None
    best_ratio = 0.0
    for idx, chunk in enumerate(chunks):
        normalized_text = index["normalized_texts"][idx] if idx < len(index["normalized_texts"]) else ""
        if not normalized_text:
            continue
        ratio = difflib.SequenceMatcher(None, query_norm, normalized_text[:2500]).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_item = chunk
    if best_item is None or best_ratio < min_ratio:
        return []
    return [
        {
            **best_item,
            "score": best_ratio,
            "overlap": 0,
            "match_type": "sequence",
            "matched_terms": [],
        }
    ]


def _collect_debug_candidates(
    query_meta: dict[str, Any],
    query_tokens: list[str],
    index: dict[str, Any],
    chunks: list[dict[str, Any]],
    top_n: int = 4,
) -> list[dict[str, Any]]:
    if not chunks:
        return []
    query_norm = str(query_meta.get("expanded_normalized", ""))
    query_terms = sorted(set(query_tokens), key=len, reverse=True)
    total_terms = max(1, len(query_terms))
    candidates: list[dict[str, Any]] = []
    for idx, chunk in enumerate(chunks):
        text = str(chunk.get("text", ""))
        norm_text = index["normalized_texts"][idx] if idx < len(index["normalized_texts"]) else ""
        chunk_tokens = index["token_sets"][idx] if idx < len(index["token_sets"]) else set()
        overlap_count = len(set(query_tokens).intersection(chunk_tokens))
        substring_hits = 0
        if norm_text and query_terms:
            substring_hits = sum(1 for term in query_terms if term in norm_text)
        seq_ratio = 0.0
        if query_norm and norm_text:
            seq_ratio = difflib.SequenceMatcher(None, query_norm, norm_text[:2500]).ratio()

        if overlap_count > 0:
            match_type = "token_overlap"
        elif substring_hits > 0:
            match_type = "substring"
        elif seq_ratio > 0:
            match_type = "sequence"
        else:
            match_type = "none"

        score = max(
            overlap_count / float(total_terms),
            substring_hits / float(total_terms),
            seq_ratio,
        )
        snippet = _normalize_spaces(text)[:200]
        section = str(
            chunk.get("source_label")
            or (
                f"Articulo {chunk.get('article_id')}"
                if chunk.get("article_id")
                else f"Seccion {chunk.get('section_id')}"
                if chunk.get("section_id")
                else ""
            )
        )
        candidates.append(
            {
                "chunk_id": chunk.get("chunk_id", idx + 1),
                "source_label": str(chunk.get("source_label", f"Chunk {idx + 1}")),
                "source": str(chunk.get("source_label", f"Chunk {idx + 1}")),
                "section": section,
                "score": round(float(score), 4),
                "overlap": int(overlap_count),
                "match_type": match_type,
                "preview": snippet,
                "snippet": snippet,
            }
        )

    candidates.sort(
        key=lambda item: (float(item.get("score", 0.0)), int(item.get("overlap", 0))),
        reverse=True,
    )
    return candidates[: max(1, top_n)]


def retrieve(
    query: str,
    index: dict[str, Any],
    chunks: list[dict[str, Any]],
    k: int = 4,
    kb_name: str = "",
    min_score: float = 0.0,
) -> list[dict[str, Any]]:
    if not query or not chunks:
        _set_last_kb_debug(
            {
                "query": str(query or ""),
                "query_original": str(query or ""),
                "query_expanded": str(query or ""),
                "intent": "",
                "tags": [],
                "kb_name": kb_name,
                "chunks_total": len(chunks or []),
                "retrieved_count": 0,
                "reason": "no_query_or_chunks",
                "min_score": float(min_score),
                "top_candidates": [],
            }
        )
        return []
    if not index:
        _set_last_kb_debug(
            {
                "query": str(query),
                "query_original": str(query),
                "query_expanded": str(query),
                "intent": "",
                "tags": [],
                "kb_name": kb_name,
                "chunks_total": len(chunks),
                "retrieved_count": 0,
                "reason": "no_index",
                "min_score": float(min_score),
                "top_candidates": [],
            }
        )
        return []

    query_meta = expand_query(query)
    expanded_text = str(query_meta.get("expanded_text", query))
    query_tokens = _tokenize(expanded_text)
    debug_candidates = _collect_debug_candidates(
        query_meta, query_tokens, index, chunks, top_n=6
    )
    ranked = _rank_by_bm25(query_meta, index, chunks)
    reason = "bm25"
    if not ranked:
        ranked = _rank_by_token_overlap(query_tokens, index, chunks)
        reason = "token_overlap"
    if not ranked:
        ranked = _rank_by_substring(query_tokens, index, chunks)
        reason = "substring_fallback"
    if not ranked:
        ranked = _rank_by_sequence_match(expanded_text, index, chunks)
        reason = "sequence_fallback"
    if not ranked:
        reason = "no_hits"

    results = []
    score_threshold = float(min_score)
    for item in ranked:
        if float(item.get("score", 0.0)) < score_threshold:
            continue
        chunk_id = int(item.get("chunk_id", 0)) if str(item.get("chunk_id", "")).isdigit() else item.get("chunk_id")
        source_label = str(item.get("source_label", "")).strip() or f"Chunk {chunk_id or 1}"
        results.append(
            {
                **item,
                "chunk_id": chunk_id,
                "source_label": source_label,
                "source": source_label,
                "score": float(item.get("score", 0.0)),
                "overlap": int(item.get("overlap", 0)),
                "match_type": str(item.get("match_type", "")),
            }
        )
        if len(results) >= max(1, k):
            break
    _set_last_kb_debug(
        {
            "query": query,
            "query_original": str(query_meta.get("original_query", query)),
            "query_expanded": str(query_meta.get("expanded_text", query)),
            "intent": str(query_meta.get("intent", "")),
            "tags": list(query_meta.get("tags", [])),
            "expanded_terms": list(query_meta.get("expanded_terms", [])),
            "query_terms": list(query_meta.get("query_terms", [])),
            "requires_exact_age": bool(query_meta.get("requires_exact_age", False)),
            "kb_name": kb_name,
            "chunks_total": len(chunks),
            "retrieved_count": len(results),
            "reason": reason,
            "min_score": score_threshold,
            "top_candidates": debug_candidates,
        }
    )
    return results
