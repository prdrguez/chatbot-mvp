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
_ENTITY_TOKEN_RE = re.compile(
    r"\b(?:[A-Z\u00c1\u00c9\u00cd\u00d3\u00da\u00d1][A-Za-z\u00c1\u00c9\u00cd\u00d3\u00da\u00d1\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1]{3,}|[A-Z]{4,})\b"
)
_LAST_KB_DEBUG: dict[str, Any] = {}
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
_ENTITY_STOPWORDS = {
    "seccion",
    "secciones",
    "section",
    "articulo",
    "articulos",
    "capitulo",
    "capitulos",
    "codigo",
    "etico",
    "politica",
    "politicas",
    "linea",
    "etica",
    "introduccion",
    "publicado",
    "enero",
    "grupo",
    "valores",
    "mision",
    "vision",
}
_CHILD_LABOR_TERMS = (
    "menor",
    "nino",
    "nene",
    "adolescente",
    "trabajo infantil",
)
_CHILD_LABOR_EXPANSION_TERMS = (
    "trabajo infantil",
    "esclavitud moderna",
    "trabajo forzado",
    "menores",
    "edad minima",
    "derechos humanos",
)
_CHILD_LABOR_EVIDENCE_PHRASES = (
    "trabajo infantil",
    "esclavitud moderna",
    "trabajo forzado",
)
_CHILD_LABOR_AGE_RE = re.compile(r"\b(\d{1,2})\s*a(?:ñ|n)os\b", re.IGNORECASE)
_CHILD_LABOR_BOOST = 1.8


def detect_intent_and_expand(query: str) -> dict[str, Any]:
    original_query = str(query or "").strip()
    normalized_query = _normalize_for_match(original_query)
    intent = ""
    tags: list[str] = []
    expanded_terms: list[str] = []

    has_minor_term = any(
        re.search(rf"\b{re.escape(term)}\b", normalized_query)
        for term in _CHILD_LABOR_TERMS
    )
    has_work_root = "trabaj" in normalized_query
    has_minor_age = False
    for match in _CHILD_LABOR_AGE_RE.finditer(original_query):
        try:
            age = int(match.group(1))
        except (TypeError, ValueError):
            continue
        if age <= 15:
            has_minor_age = True
            break
    if (has_minor_term or has_minor_age) and has_work_root:
        intent = "child_labor"
        tags = ["child_labor"]
        expanded_terms.extend(_CHILD_LABOR_EXPANSION_TERMS)

    expanded_query = original_query
    if expanded_terms:
        existing = set(_tokenize(expanded_query))
        additions: list[str] = []
        for term in expanded_terms:
            term_tokens = _tokenize(term)
            if term_tokens and all(token in existing for token in term_tokens):
                continue
            additions.append(term)
            existing.update(term_tokens)
        if additions:
            expanded_query = f"{expanded_query} {' '.join(additions)}".strip()

    return {
        "expanded_query": expanded_query,
        "intent": intent,
        "tags": tags,
    }


def expand_query(query: str) -> dict[str, Any]:
    original_query = str(query or "").strip()
    normalized_query = _normalize_for_match(original_query)
    intent_meta = detect_intent_and_expand(original_query)
    expanded_query = str(intent_meta.get("expanded_query", original_query))
    tags = list(intent_meta.get("tags", []))
    intent = str(intent_meta.get("intent", ""))
    expanded_tokens = _tokenize(expanded_query)
    return {
        "original_query": original_query,
        "normalized_query": normalized_query,
        "expanded_text": expanded_query,
        "expanded_tokens": expanded_tokens,
        "intent": intent,
        "tags": tags,
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


def infer_primary_entity(text: str) -> str:
    source = str(text or "")
    if not source.strip():
        return ""
    counts: Counter[str] = Counter()
    first_seen: dict[str, int] = {}
    for idx, match in enumerate(_ENTITY_TOKEN_RE.finditer(source)):
        token = match.group(0).strip()
        if not token:
            continue
        normalized = _strip_accents(token).lower()
        if normalized in _ENTITY_STOPWORDS:
            continue
        canonical = token.title() if token.isupper() else token
        counts[canonical] += 1
        first_seen.setdefault(canonical, idx)
    if not counts:
        return ""
    ranked = sorted(
        counts.items(),
        key=lambda item: (
            -int(item[1]),
            int(first_seen.get(item[0], 0)),
            str(item[0]).lower(),
        ),
    )
    return str(ranked[0][0])


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


def load_kb(
    text: str,
    name: str,
    kb_updated_at: str | int | None = None,
) -> dict[str, Any]:
    normalized_text = str(text or "").strip()
    kb_name = str(name or "KB cargada").strip() or "KB cargada"
    kb_hash = _hash_text(normalized_text)
    chunks = parse_policy(normalized_text)
    index = build_bm25_index(chunks)
    kb_primary_entity = infer_primary_entity(normalized_text)
    return {
        "kb_name": kb_name,
        "kb_hash": kb_hash,
        "chunks": chunks,
        "index": index,
        "chunks_total": len(chunks),
        "kb_updated_at": str(kb_updated_at or ""),
        "kb_primary_entity": kb_primary_entity,
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
    normalized_texts = [_normalize_for_match(text) for text in corpus]
    token_freqs = [dict(Counter(tokens)) for tokens in token_lists]
    doc_lens = [len(tokens) for tokens in token_lists]
    avg_doc_len = (
        sum(doc_lens) / float(len(doc_lens))
        if doc_lens
        else 0.0
    )
    doc_freq: Counter[str] = Counter()
    for token_set in token_sets:
        for token in token_set:
            doc_freq[token] += 1
    total_docs = max(1, len(token_lists))
    idf = {
        token: math.log((total_docs - freq + 0.5) / (freq + 0.5) + 1.0)
        for token, freq in doc_freq.items()
    }
    return {
        "token_lists": token_lists,
        "token_sets": token_sets,
        "normalized_texts": normalized_texts,
        "token_freqs": token_freqs,
        "doc_lens": doc_lens,
        "avg_doc_len": avg_doc_len,
        "idf": idf,
    }


def build_bm25_index(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    if not chunks:
        return {
            "token_lists": [],
            "token_sets": [],
            "normalized_texts": [],
            "token_freqs": [],
            "doc_lens": [],
            "avg_doc_len": 0.0,
            "idf": {},
        }
    corpus = tuple(str(chunk.get("text", "")) for chunk in chunks)
    text_hash = _hash_text("\n".join(corpus))
    return _build_index_cached(text_hash, corpus)


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


def _rank_by_bm25(
    query_tokens: list[str],
    index: dict[str, Any],
    chunks: list[dict[str, Any]],
    k1: float = 1.5,
    b: float = 0.75,
) -> list[dict[str, Any]]:
    if not query_tokens:
        return []
    query_counts = Counter(query_tokens)
    token_freqs = index.get("token_freqs", [])
    doc_lens = index.get("doc_lens", [])
    avg_doc_len = float(index.get("avg_doc_len", 0.0) or 0.0)
    idf = index.get("idf", {})
    ranked: list[dict[str, Any]] = []
    for idx, chunk in enumerate(chunks):
        freqs = token_freqs[idx] if idx < len(token_freqs) else {}
        if not isinstance(freqs, dict) or not freqs:
            continue
        doc_len = float(doc_lens[idx]) if idx < len(doc_lens) else 0.0
        norm = 1.0 - b + b * (doc_len / avg_doc_len) if avg_doc_len > 0 else 1.0
        score = 0.0
        matched_terms: list[str] = []
        for term, query_tf in query_counts.items():
            term_tf = float(freqs.get(term, 0.0))
            if term_tf <= 0:
                continue
            idf_score = float(idf.get(term, 0.0))
            denom = term_tf + (k1 * norm)
            if denom <= 0:
                continue
            term_score = idf_score * ((term_tf * (k1 + 1.0)) / denom)
            score += term_score * float(max(1, query_tf))
            matched_terms.append(term)
        if score <= 0:
            continue
        ranked.append(
            {
                **chunk,
                "score": score,
                "overlap": len(matched_terms),
                "match_type": "bm25",
                "matched_terms": sorted(set(matched_terms)),
            }
        )
    ranked.sort(
        key=lambda item: (float(item.get("score", 0.0)), int(item.get("overlap", 0))),
        reverse=True,
    )
    return ranked


def _build_chunk_key(item: dict[str, Any], fallback_idx: int = 0) -> str:
    chunk_id = item.get("chunk_id")
    source = str(item.get("source_label") or item.get("source") or "").strip()
    if chunk_id not in (None, "") or source:
        return f"{chunk_id}|{source}"
    return f"fallback:{fallback_idx}"


def _normalize_scores(items: list[dict[str, Any]]) -> dict[str, float]:
    if not items:
        return {}
    max_score = max(float(item.get("score", 0.0)) for item in items)
    if max_score <= 0:
        return {}
    normalized: dict[str, float] = {}
    for idx, item in enumerate(items):
        key = _build_chunk_key(item, fallback_idx=idx)
        normalized[key] = float(item.get("score", 0.0)) / max_score
    return normalized


def _contains_child_labor_evidence(chunk: dict[str, Any]) -> bool:
    title = str(
        chunk.get("section_title")
        or chunk.get("source_label")
        or chunk.get("source")
        or ""
    )
    text = str(chunk.get("text", ""))
    haystack = _normalize_for_match(f"{title} {text}")
    return any(phrase in haystack for phrase in _CHILD_LABOR_EVIDENCE_PHRASES)


def _build_hybrid_ranking(
    token_ranked: list[dict[str, Any]],
    bm25_ranked: list[dict[str, Any]],
    intent: str,
) -> list[dict[str, Any]]:
    combined: dict[str, dict[str, Any]] = {}
    token_norm = _normalize_scores(token_ranked)
    bm25_norm = _normalize_scores(bm25_ranked)

    def merge_items(
        rows: list[dict[str, Any]],
        normalized: dict[str, float],
        method: str,
        weight: float,
    ) -> None:
        for idx, row in enumerate(rows):
            key = _build_chunk_key(row, fallback_idx=idx)
            existing = combined.get(key)
            if existing is None:
                existing = {
                    **row,
                    "score": 0.0,
                    "overlap": int(row.get("overlap", 0)),
                    "matched_terms": set(row.get("matched_terms", [])),
                    "match_types": set(),
                }
                combined[key] = existing
            score_component = float(normalized.get(key, 0.0))
            existing["score"] = float(existing.get("score", 0.0)) + (weight * score_component)
            existing["overlap"] = max(
                int(existing.get("overlap", 0)),
                int(row.get("overlap", 0)),
            )
            existing["matched_terms"].update(row.get("matched_terms", []))
            existing["match_types"].add(method)

    merge_items(token_ranked, token_norm, method="token_overlap", weight=0.5)
    merge_items(bm25_ranked, bm25_norm, method="bm25", weight=0.5)

    ranked: list[dict[str, Any]] = []
    for item in combined.values():
        enriched = dict(item)
        match_types = set(enriched.pop("match_types", set()))
        matched_terms = set(enriched.pop("matched_terms", set()))
        if intent == "child_labor" and _contains_child_labor_evidence(enriched):
            enriched["score"] = float(enriched.get("score", 0.0)) + _CHILD_LABOR_BOOST
            match_types.add("child_labor_boost")
        enriched["matched_terms"] = sorted(matched_terms)
        if match_types:
            enriched["match_type"] = "hybrid:" + "+".join(sorted(match_types))
        else:
            enriched["match_type"] = "hybrid"
        ranked.append(enriched)
    ranked.sort(
        key=lambda row: (float(row.get("score", 0.0)), int(row.get("overlap", 0))),
        reverse=True,
    )
    return ranked


def _ensure_child_labor_evidence_in_top_k(
    ranked: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
    top_k: int,
) -> list[dict[str, Any]]:
    if top_k <= 0:
        return ranked
    if any(_contains_child_labor_evidence(item) for item in ranked[:top_k]):
        return ranked
    for idx, row in enumerate(ranked):
        if not _contains_child_labor_evidence(row):
            continue
        boosted = dict(row)
        boosted["score"] = float(boosted.get("score", 0.0)) + _CHILD_LABOR_BOOST
        boosted["match_type"] = str(boosted.get("match_type", "hybrid")) + "+child_labor_topk"
        reordered = [boosted] + ranked[:idx] + ranked[idx + 1 :]
        return reordered
    for idx, chunk in enumerate(chunks):
        if not _contains_child_labor_evidence(chunk):
            continue
        fallback = {
            **chunk,
            "score": _CHILD_LABOR_BOOST + 1.0,
            "overlap": 1,
            "match_type": "child_labor_exact_fallback",
            "matched_terms": list(_CHILD_LABOR_EVIDENCE_PHRASES),
        }
        return [fallback] + ranked
    return ranked


def _debug_chunk_row(item: dict[str, Any], idx: int) -> dict[str, Any]:
    chunk_id = item.get("chunk_id")
    if str(chunk_id).isdigit():
        chunk_id = int(chunk_id)
    source_label = str(item.get("source_label") or item.get("source") or "").strip()
    if not source_label:
        source_label = f"Chunk {idx + 1}"
    text = str(item.get("text", ""))
    section_id = str(item.get("section_id", "")).strip()
    return {
        "chunk_id": chunk_id,
        "source_label": source_label,
        "source": source_label,
        "section": section_id,
        "score": round(float(item.get("score", 0.0)), 4),
        "overlap": int(item.get("overlap", 0)),
        "match_type": str(item.get("match_type", "hybrid")),
        "snippet": _normalize_spaces(text)[:200],
    }


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
    query: str,
    query_tokens: list[str],
    index: dict[str, Any],
    chunks: list[dict[str, Any]],
    top_n: int = 4,
) -> list[dict[str, Any]]:
    if not chunks:
        return []
    query_norm = _normalize_for_match(query)
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
        candidates.append(
            {
                "chunk_id": chunk.get("chunk_id", idx + 1),
                "source_label": str(chunk.get("source_label", f"Chunk {idx + 1}")),
                "source": str(chunk.get("source_label", f"Chunk {idx + 1}")),
                "score": round(float(score), 4),
                "overlap": int(overlap_count),
                "match_type": match_type,
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
                "retrieval_method": "hybrid",
                "kb_name": kb_name,
                "chunks_total": len(chunks or []),
                "retrieved_count": 0,
                "reason": "no_query_or_chunks",
                "min_score": float(min_score),
                "chunks_final": [],
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
                "retrieval_method": "hybrid",
                "kb_name": kb_name,
                "chunks_total": len(chunks),
                "retrieved_count": 0,
                "reason": "no_index",
                "min_score": float(min_score),
                "chunks_final": [],
                "top_candidates": [],
            }
        )
        return []

    query_meta = expand_query(query)
    expanded_query = str(query_meta.get("expanded_text", query))
    intent = str(query_meta.get("intent", ""))
    tags = list(query_meta.get("tags", []))
    query_tokens = list(query_meta.get("expanded_tokens", []))
    if not query_tokens:
        query_tokens = _tokenize(expanded_query)
    overlap_ranked = _rank_by_token_overlap(query_tokens, index, chunks)
    bm25_ranked = _rank_by_bm25(query_tokens, index, chunks)
    ranked = _build_hybrid_ranking(overlap_ranked, bm25_ranked, intent=intent)
    reason = "hybrid"
    if intent == "child_labor":
        ranked = _ensure_child_labor_evidence_in_top_k(ranked, chunks, top_k=max(1, int(k)))
        reason = "hybrid_child_labor_boost"
    if not ranked:
        ranked = _rank_by_sequence_match(expanded_query, index, chunks)
        reason = "sequence_fallback"

    results = []
    threshold = float(min_score)
    for item in ranked:
        if float(item.get("score", 0.0)) < threshold:
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
    debug_rows = [_debug_chunk_row(item, idx) for idx, item in enumerate(results)]
    if not results and reason == "hybrid":
        reason = "no_hits"
    _set_last_kb_debug(
        {
            "query": query,
            "query_original": str(query_meta.get("original_query", query)),
            "query_expanded": expanded_query,
            "intent": intent,
            "tags": tags,
            "retrieval_method": "hybrid",
            "kb_name": kb_name,
            "chunks_total": len(chunks),
            "retrieved_count": len(results),
            "reason": reason,
            "min_score": threshold,
            "chunks_final": debug_rows,
            "top_candidates": debug_rows,
        }
    )
    return results
