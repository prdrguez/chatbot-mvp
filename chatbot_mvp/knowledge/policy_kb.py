from __future__ import annotations

import difflib
import hashlib
import math
import re
import unicodedata
from collections import Counter, defaultdict
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
_MARKDOWN_HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$")
_TOKEN_RE = re.compile(r"[a-z0-9\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1]+", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")
_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\u00c1\u00c9\u00cd\u00d3\u00da\u00dc\u00d1])")
_DEFAULT_TARGET_CHUNK_CHARS = 1100
_DEFAULT_MAX_CHUNK_CHARS = 1400
_DEFAULT_OVERLAP_MAX_CHARS = 260
_LAST_KB_DEBUG: dict[str, Any] = {}
_SIGNAL_WEIGHTS = {
    "bm25": 0.50,
    "overlap": 0.30,
}
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
    lowered = _strip_accents(str(text or "").lower())
    lowered = re.sub(r"[^\w\s]", " ", lowered)
    return _normalize_spaces(lowered)


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in _TOKEN_RE.findall(str(text or "")):
        token = _strip_accents(raw.lower())
        if len(token) < 3:
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


def _split_paragraphs(text: str) -> list[str]:
    normalized = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    paragraphs = [
        block.strip()
        for block in _PARAGRAPH_SPLIT_RE.split(normalized)
        if block and block.strip()
    ]
    if paragraphs:
        return paragraphs
    return [line.strip() for line in normalized.splitlines() if line.strip()]


def _split_sentences(text: str) -> list[str]:
    normalized = _normalize_spaces(text)
    if not normalized:
        return []
    parts = [part.strip() for part in _SENTENCE_SPLIT_RE.split(normalized) if part.strip()]
    return parts if parts else [normalized]


def _split_paragraph_to_units(paragraph: str, max_chars: int) -> list[str]:
    clean_paragraph = str(paragraph or "").strip()
    if not clean_paragraph:
        return []
    if len(clean_paragraph) <= max(240, int(max_chars)):
        return [clean_paragraph]

    sentences = _split_sentences(clean_paragraph)
    if len(sentences) <= 1:
        return [clean_paragraph]

    resolved_max = max(240, int(max_chars))
    units: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = sentence if not current else f"{current} {sentence}"
        if current and len(candidate) > resolved_max:
            units.append(current.strip())
            current = sentence
            continue
        current = candidate
    if current.strip():
        units.append(current.strip())
    return units if units else [clean_paragraph]


def _build_chunk_texts_from_paragraphs(
    paragraphs: list[str],
    target_chunk_chars: int,
    max_chunk_chars: int,
) -> list[str]:
    resolved_target = max(500, int(target_chunk_chars))
    resolved_max = max(resolved_target, int(max_chunk_chars))
    units: list[str] = []
    for paragraph in paragraphs:
        units.extend(_split_paragraph_to_units(paragraph, resolved_max))
    if not units:
        return []

    chunks: list[str] = []
    current_parts: list[str] = []
    current_chars = 0
    for unit in units:
        unit_text = str(unit or "").strip()
        if not unit_text:
            continue
        sep = 2 if current_parts else 0
        next_chars = current_chars + sep + len(unit_text)
        if current_parts and next_chars > resolved_max:
            chunk_text = "\n\n".join(current_parts).strip()
            if chunk_text:
                chunks.append(chunk_text)
            current_parts = [unit_text]
            current_chars = len(unit_text)
            continue

        current_parts.append(unit_text)
        current_chars = next_chars
        if current_chars >= resolved_target:
            chunk_text = "\n\n".join(current_parts).strip()
            if chunk_text:
                chunks.append(chunk_text)
            current_parts = []
            current_chars = 0

    if current_parts:
        chunk_text = "\n\n".join(current_parts).strip()
        if chunk_text:
            chunks.append(chunk_text)

    return chunks


def _extract_overlap_text(
    previous_chunk_text: str,
    max_overlap_chars: int = _DEFAULT_OVERLAP_MAX_CHARS,
) -> str:
    max_chars = max(80, int(max_overlap_chars))
    previous = str(previous_chunk_text or "").strip()
    if not previous:
        return ""

    previous_paragraphs = _split_paragraphs(previous)
    if previous_paragraphs:
        last_paragraph = previous_paragraphs[-1].strip()
        if 40 <= len(last_paragraph) <= max_chars:
            return last_paragraph
        if len(last_paragraph) < 40 and len(previous_paragraphs) >= 2:
            merged = f"{previous_paragraphs[-2].strip()} {last_paragraph}".strip()
            if 40 <= len(merged) <= max_chars:
                return merged

    sentences = _split_sentences(previous)
    if not sentences:
        return ""
    tail = " ".join(sentences[-2:]).strip()
    if len(tail) > max_chars and len(sentences) >= 1:
        tail = sentences[-1].strip()
    if len(tail) > max_chars:
        return ""
    return tail


def _apply_chunk_overlap(
    chunk_texts: list[str],
    max_overlap_chars: int = _DEFAULT_OVERLAP_MAX_CHARS,
) -> list[str]:
    if len(chunk_texts) < 2:
        return chunk_texts

    resolved: list[str] = [chunk_texts[0].strip()]
    for idx in range(1, len(chunk_texts)):
        current = chunk_texts[idx].strip()
        overlap_text = _extract_overlap_text(chunk_texts[idx - 1], max_overlap_chars=max_overlap_chars)
        if overlap_text:
            overlap_norm = _normalize_for_match(overlap_text)
            current_start_norm = _normalize_for_match(current[: max(240, len(overlap_text) + 40)])
            if overlap_norm and overlap_norm not in current_start_norm:
                current = f"{overlap_text}\n\n{current}".strip()
        resolved.append(current)
    return resolved


def _chunk_by_size(
    text: str,
    chunk_size: int = _DEFAULT_TARGET_CHUNK_CHARS,
    overlap: int = _DEFAULT_OVERLAP_MAX_CHARS,
    label_prefix: str = "Chunk",
) -> list[dict[str, Any]]:
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return []

    target_chunk_chars = max(700, min(1600, int(chunk_size or _DEFAULT_TARGET_CHUNK_CHARS)))
    max_chunk_chars = max(target_chunk_chars, min(1800, target_chunk_chars + 300))
    chunk_texts = _build_chunk_texts_from_paragraphs(
        paragraphs,
        target_chunk_chars=target_chunk_chars,
        max_chunk_chars=max_chunk_chars,
    )
    chunk_texts = _apply_chunk_overlap(
        chunk_texts,
        max_overlap_chars=max(120, int(overlap or _DEFAULT_OVERLAP_MAX_CHARS)),
    )

    chunks: list[dict[str, Any]] = []
    for idx, chunk_text in enumerate(chunk_texts, start=1):
        source = f"{label_prefix} {idx}"
        chunks.append(
            {
                "chunk_id": len(chunks) + 1,
                "article_id": None,
                "section_id": None,
                "section_key": "",
                "section_chunk_index": idx,
                "section_chunks_total": len(chunk_texts),
                "section_title": "",
                "source_label": source[:140],
                "text": chunk_text,
            }
        )
    return chunks


def _extract_headings(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    headings: list[dict[str, Any]] = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        markdown_match = _MARKDOWN_HEADING_RE.match(stripped)
        if markdown_match:
            level = len(markdown_match.group(1))
            title = _normalize_spaces(markdown_match.group(2))
            if title:
                headings.append(
                    {
                        "line": idx,
                        "article_id": None,
                        "section_id": f"md-{idx + 1}",
                        "section_title": title[:110],
                        "source_label": f"Seccion {title[:100]}",
                        "heading_level": level,
                    }
                )
                continue

        article_match = _ARTICLE_RE.match(stripped)
        if article_match:
            article_id = article_match.group(1)
            headings.append(
                {
                    "line": idx,
                    "article_id": article_id,
                    "section_id": None,
                    "section_title": f"Articulo {article_id}",
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
                    "section_title": chapter_name[:110],
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
                    "section_title": title,
                    "source_label": source_label,
                }
            )
            continue

        if _is_upper_heading(stripped):
            title = _normalize_spaces(stripped.title())[:110]
            headings.append(
                {
                    "line": idx,
                    "article_id": None,
                    "section_id": None,
                    "section_title": title,
                    "source_label": title,
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

        section_key_parts = [
            str(heading.get("section_id", "")).strip(),
            str(heading.get("article_id", "")).strip(),
            str(heading.get("source_label", "")).strip().lower(),
            str(idx + 1),
        ]
        section_key = "|".join(part for part in section_key_parts if part) or f"section|{idx + 1}"

        section_paragraphs = _split_paragraphs(section_text)
        section_chunk_texts = _build_chunk_texts_from_paragraphs(
            section_paragraphs,
            target_chunk_chars=_DEFAULT_TARGET_CHUNK_CHARS,
            max_chunk_chars=_DEFAULT_MAX_CHUNK_CHARS,
        )
        section_chunk_texts = _apply_chunk_overlap(
            section_chunk_texts,
            max_overlap_chars=_DEFAULT_OVERLAP_MAX_CHARS,
        )
        if not section_chunk_texts:
            section_chunk_texts = [section_text]

        section_chunks_total = len(section_chunk_texts)
        for section_chunk_index, chunk_text in enumerate(section_chunk_texts, start=1):
            source_label = str(heading["source_label"]).strip() or f"Seccion {idx + 1}"
            if section_chunks_total > 1:
                source_label = (
                    f"{source_label} (parte {section_chunk_index}/{section_chunks_total})"
                )

            chunks.append(
                {
                    "chunk_id": len(chunks) + 1,
                    "article_id": heading.get("article_id"),
                    "section_id": heading.get("section_id"),
                    "section_key": section_key,
                    "section_chunk_index": section_chunk_index,
                    "section_chunks_total": section_chunks_total,
                    "section_title": heading.get("section_title", ""),
                    "source_label": source_label[:140],
                    "text": chunk_text,
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
    index = build_bm25_index(
        chunks,
        kb_hash=kb_hash,
        kb_updated_at=kb_updated_at,
    )
    return {
        "kb_name": kb_name,
        "kb_hash": kb_hash,
        "chunks": chunks,
        "index": index,
        "chunks_total": len(chunks),
        "kb_updated_at": str(kb_updated_at or ""),
    }


def _set_last_kb_debug(payload: dict[str, Any]) -> None:
    global _LAST_KB_DEBUG
    _LAST_KB_DEBUG = dict(payload)


def get_last_kb_debug() -> dict[str, Any]:
    return dict(_LAST_KB_DEBUG)


def _iter_ngrams(tokens: tuple[str, ...] | list[str], n: int) -> list[str]:
    if n <= 1 or len(tokens) < n:
        return []
    return [" ".join(tokens[idx : idx + n]) for idx in range(0, len(tokens) - n + 1)]


def _clean_heading_phrase(value: str) -> str:
    text = _normalize_for_match(value)
    text = re.sub(
        r"\b(?:seccion|section|articulo|capitulo)\b\s+[0-9a-z.-]+\s*",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    return _normalize_spaces(text)


def _build_vocab_terms(
    token_lists: list[tuple[str, ...]],
    section_titles_normalized: list[str],
) -> dict[str, Any]:
    unigram_counts: Counter[str] = Counter()
    bigram_counts: Counter[str] = Counter()
    trigram_counts: Counter[str] = Counter()
    for tokens in token_lists:
        unigram_counts.update(tokens)
        bigram_counts.update(_iter_ngrams(tokens, 2))
        trigram_counts.update(_iter_ngrams(tokens, 3))

    total_tokens = sum(unigram_counts.values())
    min_count = 2 if total_tokens >= 240 else 1
    top_unigrams = [
        term
        for term, count in unigram_counts.most_common(140)
        if count >= min_count
    ]
    top_bigrams = [
        term
        for term, count in bigram_counts.most_common(100)
        if count >= min_count
    ]
    top_trigrams = [
        term
        for term, count in trigram_counts.most_common(80)
        if count >= min_count
    ]

    ordered_terms: list[str] = []
    seen_terms: set[str] = set()

    def add_term(raw: str) -> None:
        term = _normalize_spaces(raw)
        if not term:
            return
        if term in seen_terms:
            return
        seen_terms.add(term)
        ordered_terms.append(term)

    for title in section_titles_normalized:
        cleaned = _clean_heading_phrase(title)
        if cleaned:
            add_term(cleaned)
    for phrase in top_trigrams:
        add_term(phrase)
    for phrase in top_bigrams:
        add_term(phrase)
    for term in top_unigrams:
        add_term(term)

    vocab_terms = ordered_terms[:220]
    vocab_unigrams = sorted(set(top_unigrams))
    return {
        "vocab_terms": vocab_terms,
        "vocab_unigrams": vocab_unigrams,
    }


def _build_cooc_map(
    token_lists: list[tuple[str, ...]],
    window_size: int = 4,
    max_related: int = 6,
) -> dict[str, list[dict[str, Any]]]:
    token_counts: Counter[str] = Counter()
    pair_counts: dict[str, Counter[str]] = defaultdict(Counter)
    total_tokens = 0

    for tokens in token_lists:
        token_counts.update(tokens)
        total_tokens += len(tokens)
        for idx, token in enumerate(tokens):
            start = max(0, idx - window_size)
            end = min(len(tokens), idx + window_size + 1)
            for ctx_idx in range(start, end):
                if ctx_idx == idx:
                    continue
                related = tokens[ctx_idx]
                if related == token:
                    continue
                pair_counts[token][related] += 1

    if not pair_counts:
        return {}

    min_pair_count = 2 if total_tokens >= 180 else 1
    corpus_size = max(1, total_tokens)
    cooc_map: dict[str, list[dict[str, Any]]] = {}
    for term, related_counter in pair_counts.items():
        ranked: list[tuple[float, int, str, float]] = []
        for related, count in related_counter.items():
            if count < min_pair_count:
                continue
            denom = float(max(1, token_counts[term] * token_counts[related]))
            pmi = math.log((count * corpus_size) / denom)
            normalized = count / float(max(1, token_counts[term]))
            association = pmi + normalized
            ranked.append((association, count, related, pmi))

        if not ranked:
            fallback = related_counter.most_common(max_related)
            cooc_map[term] = [
                {
                    "term": related,
                    "score": round(count / float(max(1, token_counts[term])), 4),
                    "count": int(count),
                    "pmi": 0.0,
                }
                for related, count in fallback
            ]
            continue

        ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
        cooc_map[term] = [
            {
                "term": related,
                "score": round(float(association), 4),
                "count": int(count),
                "pmi": round(float(pmi), 4),
            }
            for association, count, related, pmi in ranked[:max_related]
        ]
    return cooc_map


@st.cache_resource(show_spinner=False)
def _build_index_cached(
    cache_key: str,
    corpus: tuple[str, ...],
    source_labels: tuple[str, ...],
) -> dict[str, Any]:
    _ = cache_key
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

    section_titles: list[str] = []
    section_titles_normalized: list[str] = []
    section_title_tokens: list[list[str]] = []
    title_seen: set[str] = set()
    heading_term_counter: Counter[str] = Counter()
    for raw_title in source_labels:
        title = str(raw_title or "").strip()
        if not title:
            continue
        title_norm = _normalize_for_match(title)
        if not title_norm or title_norm in title_seen:
            continue
        title_seen.add(title_norm)
        section_titles.append(title)
        section_titles_normalized.append(title_norm)
        tokens = _tokenize(title_norm)
        section_title_tokens.append(tokens)
        heading_term_counter.update(tokens)

    vocab_meta = _build_vocab_terms(token_lists, section_titles_normalized)
    cooc_map = _build_cooc_map(token_lists)
    heading_terms = [
        term
        for term, _ in heading_term_counter.most_common(180)
    ]

    return {
        "token_lists": token_lists,
        "token_sets": token_sets,
        "normalized_texts": normalized_texts,
        "token_freqs": token_freqs,
        "doc_lens": doc_lens,
        "avg_doc_len": avg_doc_len,
        "idf": idf,
        "section_titles": section_titles,
        "section_titles_normalized": section_titles_normalized,
        "section_title_tokens": section_title_tokens,
        "heading_terms": heading_terms,
        "vocab_terms": list(vocab_meta.get("vocab_terms", [])),
        "vocab_unigrams": list(vocab_meta.get("vocab_unigrams", [])),
        "cooc_map": cooc_map,
    }


def build_bm25_index(
    chunks: list[dict[str, Any]],
    kb_hash: str = "",
    kb_updated_at: str | int | None = None,
) -> dict[str, Any]:
    if not chunks:
        return {
            "token_lists": [],
            "token_sets": [],
            "normalized_texts": [],
            "token_freqs": [],
            "doc_lens": [],
            "avg_doc_len": 0.0,
            "idf": {},
            "section_titles": [],
            "section_titles_normalized": [],
            "section_title_tokens": [],
            "heading_terms": [],
            "vocab_terms": [],
            "vocab_unigrams": [],
            "cooc_map": {},
        }
    corpus = tuple(str(chunk.get("text", "")) for chunk in chunks)
    source_labels = tuple(str(chunk.get("source_label", "")) for chunk in chunks)
    text_hash = _hash_text("\n".join(corpus))
    resolved_hash = str(kb_hash or text_hash)
    cache_key = f"{resolved_hash}:{str(kb_updated_at or '')}:{len(chunks)}"
    return _build_index_cached(cache_key, corpus, source_labels)


def expand_query_with_kb(
    query: str,
    kb_index: dict[str, Any],
    max_added_terms: int = 8,
) -> dict[str, Any]:
    original_query = str(query or "").strip()
    normalized_query = _normalize_for_match(original_query)
    query_tokens = _tokenize(original_query)
    existing_tokens = set(query_tokens)
    existing_terms = set()
    added_terms: list[str] = []
    expansion_notes: list[dict[str, str]] = []

    def add_term(term: str, source: str, reason: str) -> None:
        if len(added_terms) >= max(1, int(max_added_terms)):
            return
        normalized_term = _normalize_for_match(term)
        if not normalized_term:
            return
        if normalized_term in existing_terms:
            return
        term_tokens = _tokenize(normalized_term)
        if not term_tokens:
            return
        if all(token in existing_tokens for token in term_tokens):
            return
        existing_terms.add(normalized_term)
        existing_tokens.update(term_tokens)
        added_terms.append(normalized_term)
        expansion_notes.append(
            {
                "term": normalized_term,
                "source": source,
                "reason": reason,
            }
        )

    section_titles_norm = list(kb_index.get("section_titles_normalized", []))
    section_title_tokens = list(kb_index.get("section_title_tokens", []))
    heading_terms = list(kb_index.get("heading_terms", []))
    vocab_terms = list(kb_index.get("vocab_terms", []))
    vocab_unigrams = list(kb_index.get("vocab_unigrams", []))
    cooc_map = kb_index.get("cooc_map", {})
    query_token_set = set(query_tokens)

    for title_norm, title_tokens in zip(section_titles_norm, section_title_tokens):
        if len(added_terms) >= max_added_terms:
            break
        title_token_set = set(title_tokens)
        overlap_terms = sorted(query_token_set.intersection(title_token_set))
        if not overlap_terms:
            continue
        cleaned_title = _clean_heading_phrase(title_norm) or title_norm
        add_term(
            cleaned_title,
            "heading_match",
            f"overlap:{','.join(overlap_terms)}",
        )

    if query_tokens and heading_terms:
        for token in query_tokens:
            if len(added_terms) >= max_added_terms:
                break
            if token in heading_terms:
                continue
            close = difflib.get_close_matches(token, heading_terms, n=1, cutoff=0.82)
            if not close:
                continue
            add_term(close[0], "fuzzy_heading", f"token:{token}")

    if normalized_query and section_titles_norm:
        ratios: list[tuple[float, str]] = []
        for title_norm in section_titles_norm:
            ratio = difflib.SequenceMatcher(None, normalized_query, title_norm).ratio()
            if ratio < 0.55:
                continue
            ratios.append((ratio, title_norm))
        ratios.sort(key=lambda item: item[0], reverse=True)
        for ratio, title_norm in ratios[:2]:
            cleaned_title = _clean_heading_phrase(title_norm) or title_norm
            add_term(cleaned_title, "fuzzy_heading", f"title_ratio:{ratio:.2f}")

    if query_tokens and vocab_unigrams:
        for token in query_tokens:
            if len(added_terms) >= max_added_terms:
                break
            close = difflib.get_close_matches(token, vocab_unigrams, n=1, cutoff=0.84)
            if not close:
                continue
            add_term(close[0], "vocab", f"token:{token}")

    for phrase in vocab_terms[:60]:
        if len(added_terms) >= max_added_terms:
            break
        phrase_tokens = set(_tokenize(phrase))
        if len(phrase_tokens) < 2:
            continue
        overlap = sorted(query_token_set.intersection(phrase_tokens))
        if not overlap:
            continue
        add_term(phrase, "vocab", f"overlap:{','.join(overlap[:2])}")

    if isinstance(cooc_map, dict):
        seed_tokens = list(existing_tokens)
        for seed in seed_tokens:
            if len(added_terms) >= max_added_terms:
                break
            related_rows = cooc_map.get(seed, [])
            if not isinstance(related_rows, list):
                continue
            for row in related_rows[:2]:
                if len(added_terms) >= max_added_terms:
                    break
                if isinstance(row, dict):
                    related_term = str(row.get("term", "")).strip()
                else:
                    related_term = str(row).strip()
                if not related_term:
                    continue
                add_term(related_term, "cooc", f"seed:{seed}")

    expanded_query = original_query
    if added_terms:
        expanded_query = f"{original_query} {' '.join(added_terms)}".strip()
    expanded_tokens = _tokenize(expanded_query)
    return {
        "query_original": original_query,
        "query_expanded": expanded_query,
        "expanded_tokens": expanded_tokens,
        "added_terms": added_terms,
        "expansion_notes": expansion_notes,
    }


def expand_query(query: str, kb_index: dict[str, Any] | None = None) -> dict[str, Any]:
    return expand_query_with_kb(query, kb_index or {})


def _compute_bm25_scores(
    query_tokens: list[str],
    index: dict[str, Any],
    k1: float = 1.5,
    b: float = 0.75,
) -> list[float]:
    if not query_tokens:
        return []
    token_freqs = index.get("token_freqs", [])
    doc_lens = index.get("doc_lens", [])
    avg_doc_len = float(index.get("avg_doc_len", 0.0) or 0.0)
    idf = index.get("idf", {})
    query_counts = Counter(query_tokens)

    scores: list[float] = []
    for idx, freqs in enumerate(token_freqs):
        if not isinstance(freqs, dict) or not freqs:
            scores.append(0.0)
            continue
        doc_len = float(doc_lens[idx]) if idx < len(doc_lens) else 0.0
        norm = 1.0 - b + b * (doc_len / avg_doc_len) if avg_doc_len > 0 else 1.0
        score = 0.0
        for term, query_tf in query_counts.items():
            term_tf = float(freqs.get(term, 0.0))
            if term_tf <= 0:
                continue
            idf_score = float(idf.get(term, 0.0))
            denom = term_tf + (k1 * norm)
            if denom <= 0:
                continue
            score += idf_score * ((term_tf * (k1 + 1.0)) / denom) * float(max(1, query_tf))
        scores.append(score)
    return scores


def _normalize_scores(scores: list[float]) -> list[float]:
    if not scores:
        return []
    max_score = max(scores)
    if max_score <= 0:
        return [0.0 for _ in scores]
    return [float(score) / max_score for score in scores]


def _build_query_ngrams(query_tokens: list[str]) -> list[str]:
    ngrams: list[str] = []
    unique = set()
    for size in (3, 2):
        for ngram in _iter_ngrams(query_tokens, size):
            if ngram in unique:
                continue
            unique.add(ngram)
            ngrams.append(ngram)
    return ngrams


def _dedupe_ranked_chunks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for idx, row in enumerate(rows):
        chunk_id = row.get("chunk_id")
        key = f"chunk:{chunk_id}" if str(chunk_id).isdigit() else f"chunk:{idx}"
        existing = deduped.get(key)
        if existing is None or float(row.get("score", 0.0)) > float(existing.get("score", 0.0)):
            deduped[key] = row
    ranked = list(deduped.values())
    ranked.sort(
        key=lambda item: (
            float(item.get("score", 0.0)),
            int(item.get("overlap", 0)),
        ),
        reverse=True,
    )
    return ranked


def _safe_chunk_int(value: Any) -> int | None:
    if str(value).isdigit():
        return int(value)
    return None


def _chunk_text_len(row: dict[str, Any]) -> int:
    return len(str(row.get("text", "")).strip())


def _is_stitch_anchor(row: dict[str, Any]) -> bool:
    match_type = str(row.get("match_type", "")).lower()
    score = float(row.get("score", 0.0))
    overlap = int(row.get("overlap", 0))
    if bool(row.get("strong_match", False)):
        return True
    if "heading" in match_type or "exact" in match_type:
        return score >= 0.16
    return overlap >= 3 and score >= 0.16


def _stitch_section_chunks(
    selected_rows: list[dict[str, Any]],
    all_chunks: list[dict[str, Any]],
    max_context_chars: int | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    if not selected_rows:
        return [], [], 0

    try:
        context_budget = int(max_context_chars or 0)
    except (TypeError, ValueError):
        context_budget = 0
    if context_budget <= 0:
        total = sum(_chunk_text_len(row) for row in selected_rows)
        return selected_rows, [], total

    merged_rows = [dict(row) for row in selected_rows]
    for idx, row in enumerate(merged_rows):
        row["_context_rank"] = float(idx)

    selected_ids = {
        chunk_id
        for chunk_id in (_safe_chunk_int(row.get("chunk_id")) for row in merged_rows)
        if chunk_id is not None
    }

    section_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for doc_index, chunk in enumerate(all_chunks):
        section_key = str(chunk.get("section_key", "")).strip()
        if not section_key:
            continue
        chunk_id = _safe_chunk_int(chunk.get("chunk_id"))
        if chunk_id is None:
            continue
        row = dict(chunk)
        row["_doc_index"] = doc_index
        row["_section_chunk_index"] = int(chunk.get("section_chunk_index") or 0)
        section_map[section_key].append(row)

    for items in section_map.values():
        items.sort(
            key=lambda item: (
                int(item.get("_section_chunk_index", 0)),
                int(item.get("_doc_index", 0)),
            )
        )

    used_chars = sum(_chunk_text_len(row) for row in merged_rows)
    added_rows: list[dict[str, Any]] = []
    if used_chars >= context_budget:
        for row in merged_rows:
            row.pop("_context_rank", None)
        return merged_rows, added_rows, used_chars

    for anchor in list(merged_rows):
        if used_chars >= context_budget:
            break
        if not _is_stitch_anchor(anchor):
            continue

        section_key = str(anchor.get("section_key", "")).strip()
        if not section_key:
            continue
        section_chunks = section_map.get(section_key, [])
        if len(section_chunks) < 2:
            continue

        anchor_chunk_id = _safe_chunk_int(anchor.get("chunk_id"))
        if anchor_chunk_id is None:
            continue
        anchor_idx = next(
            (
                idx
                for idx, row in enumerate(section_chunks)
                if _safe_chunk_int(row.get("chunk_id")) == anchor_chunk_id
            ),
            -1,
        )
        if anchor_idx < 0:
            continue

        anchor_rank = float(anchor.get("_context_rank", 0.0))
        candidate_positions: list[int] = []
        for distance in range(1, len(section_chunks)):
            right = anchor_idx + distance
            left = anchor_idx - distance
            if right < len(section_chunks):
                candidate_positions.append(right)
            if left >= 0:
                candidate_positions.append(left)

        stitched_for_anchor = 0
        for pos in candidate_positions:
            if used_chars >= context_budget:
                break
            candidate = section_chunks[pos]
            candidate_chunk_id = _safe_chunk_int(candidate.get("chunk_id"))
            if candidate_chunk_id is None or candidate_chunk_id in selected_ids:
                continue
            candidate_text_len = _chunk_text_len(candidate)
            if candidate_text_len <= 0:
                continue
            if used_chars + candidate_text_len > context_budget:
                continue

            stitched_for_anchor += 1
            selected_ids.add(candidate_chunk_id)
            used_chars += candidate_text_len
            stitched = dict(candidate)
            stitched["score"] = float(anchor.get("score", 0.0)) * 0.96
            stitched["overlap"] = int(stitched.get("overlap", 0))
            stitched["match_type"] = "stitched_section"
            stitched["strong_match"] = bool(anchor.get("strong_match", False))
            stitched["added_by_stitching"] = True
            stitched["stitch_anchor_chunk_id"] = anchor_chunk_id
            stitched["score_components"] = dict(stitched.get("score_components", {}))
            stitched["_context_rank"] = anchor_rank + (stitched_for_anchor / 100.0)
            merged_rows.append(stitched)
            added_rows.append(stitched)

    merged_rows.sort(key=lambda row: float(row.get("_context_rank", 0.0)))
    for row in merged_rows:
        row.pop("_context_rank", None)
    return merged_rows, added_rows, used_chars


def _debug_chunk_row(item: dict[str, Any], idx: int) -> dict[str, Any]:
    chunk_id = item.get("chunk_id")
    if str(chunk_id).isdigit():
        chunk_id = int(chunk_id)
    source_label = str(item.get("source_label") or item.get("source") or "").strip()
    if not source_label:
        source_label = f"Chunk {idx + 1}"
    text = str(item.get("text", ""))
    return {
        "chunk_id": chunk_id,
        "source_label": source_label,
        "source": source_label,
        "section": str(item.get("section_id", "")).strip(),
        "section_key": str(item.get("section_key", "")).strip(),
        "score": round(float(item.get("score", 0.0)), 4),
        "overlap": int(item.get("overlap", 0)),
        "match_type": str(item.get("match_type", "hybrid")),
        "strong_match": bool(item.get("strong_match", False)),
        "added_by_stitching": bool(item.get("added_by_stitching", False)),
        "stitch_anchor_chunk_id": _safe_chunk_int(item.get("stitch_anchor_chunk_id")),
        "score_components": dict(item.get("score_components", {})),
        "snippet": _normalize_spaces(text)[:220],
    }


def retrieve(
    query: str,
    index: dict[str, Any],
    chunks: list[dict[str, Any]],
    k: int = 4,
    kb_name: str = "",
    min_score: float = 0.0,
    max_context_chars: int | None = None,
) -> list[dict[str, Any]]:
    try:
        context_budget_debug = max(0, int(max_context_chars or 0))
    except (TypeError, ValueError):
        context_budget_debug = 0
    if not query or not chunks:
        _set_last_kb_debug(
            {
                "query": str(query or ""),
                "query_original": str(query or ""),
                "query_expanded": str(query or ""),
                "expansion_notes": [],
                "kb_name": kb_name,
                "chunks_total": len(chunks or []),
                "retrieved_count": 0,
                "reason": "no_query_or_chunks",
                "retrieval_method": "hybrid",
                "min_score": float(min_score),
                "chunks_final": [],
                "chunks_added_by_stitching": [],
                "stitching_added_count": 0,
                "context_chars_used": 0,
                "context_chars_budget": context_budget_debug,
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
                "expansion_notes": [],
                "kb_name": kb_name,
                "chunks_total": len(chunks),
                "retrieved_count": 0,
                "reason": "no_index",
                "retrieval_method": "hybrid",
                "min_score": float(min_score),
                "chunks_final": [],
                "chunks_added_by_stitching": [],
                "stitching_added_count": 0,
                "context_chars_used": 0,
                "context_chars_budget": context_budget_debug,
                "top_candidates": [],
            }
        )
        return []

    expansion_meta = expand_query_with_kb(query, index)
    expanded_query = str(expansion_meta.get("query_expanded", query))
    query_tokens = list(expansion_meta.get("expanded_tokens", []))
    if not query_tokens:
        query_tokens = _tokenize(expanded_query)

    if not query_tokens:
        _set_last_kb_debug(
            {
                "query": query,
                "query_original": str(expansion_meta.get("query_original", query)),
                "query_expanded": expanded_query,
                "expansion_notes": list(expansion_meta.get("expansion_notes", [])),
                "kb_name": kb_name,
                "chunks_total": len(chunks),
                "retrieved_count": 0,
                "reason": "no_query_tokens",
                "retrieval_method": "hybrid",
                "min_score": float(min_score),
                "chunks_final": [],
                "chunks_added_by_stitching": [],
                "stitching_added_count": 0,
                "context_chars_used": 0,
                "context_chars_budget": context_budget_debug,
                "top_candidates": [],
            }
        )
        return []

    query_token_set = set(query_tokens)
    original_tokens = _tokenize(query)
    query_ngrams = _build_query_ngrams(original_tokens)
    query_norm = _normalize_for_match(query)
    normalized_texts = index.get("normalized_texts", [])
    token_sets = index.get("token_sets", [])
    bm25_scores = _compute_bm25_scores(query_tokens, index)
    bm25_norm = _normalize_scores(bm25_scores)

    rows: list[dict[str, Any]] = []
    for idx, chunk in enumerate(chunks):
        text = str(chunk.get("text", ""))
        chunk_norm = (
            normalized_texts[idx]
            if idx < len(normalized_texts)
            else _normalize_for_match(text)
        )
        chunk_tokens = (
            token_sets[idx]
            if idx < len(token_sets)
            else set(_tokenize(text))
        )

        overlap_terms = sorted(query_token_set.intersection(chunk_tokens))
        overlap_norm = len(overlap_terms) / float(max(1, len(query_token_set)))
        bm25_component = bm25_norm[idx] if idx < len(bm25_norm) else 0.0

        exact_ngram_hits = 0
        if chunk_norm and query_ngrams:
            exact_ngram_hits = sum(1 for ngram in query_ngrams if ngram in chunk_norm)
        exact_token_hits = len(set(original_tokens).intersection(chunk_tokens))
        exact_bonus = min(0.36, 0.12 * exact_ngram_hits)
        if exact_token_hits >= max(2, int(math.ceil(len(set(original_tokens)) * 0.6))):
            exact_bonus += 0.06

        source_label = str(chunk.get("source_label") or chunk.get("source") or "")
        source_norm = _normalize_for_match(source_label)
        heading_tokens = set(_tokenize(source_norm))
        heading_overlap_terms = sorted(query_token_set.intersection(heading_tokens))
        heading_overlap = len(heading_overlap_terms) / float(max(1, len(query_token_set)))
        heading_bonus = min(0.28, heading_overlap * 0.28)

        fuzzy_ratio = 0.0
        if source_norm and query_norm:
            fuzzy_ratio = difflib.SequenceMatcher(None, query_norm, source_norm).ratio()
        fuzzy_bonus = 0.0
        if fuzzy_ratio >= 0.72:
            fuzzy_bonus = min(0.24, (fuzzy_ratio - 0.72) * 0.6)

        score = (
            (_SIGNAL_WEIGHTS["bm25"] * bm25_component)
            + (_SIGNAL_WEIGHTS["overlap"] * overlap_norm)
            + exact_bonus
            + heading_bonus
            + fuzzy_bonus
        )
        if score <= 0:
            continue

        match_signals: list[str] = []
        if bm25_component > 0.01:
            match_signals.append("bm25")
        if overlap_norm > 0:
            match_signals.append("overlap")
        if exact_bonus > 0:
            match_signals.append("exact")
        if heading_bonus > 0:
            match_signals.append("heading")
        if fuzzy_bonus > 0:
            match_signals.append("fuzzy")
        match_type = "hybrid"
        if match_signals:
            match_type = "hybrid:" + "+".join(match_signals)

        strong_match = bool(
            exact_ngram_hits > 0
            or exact_bonus >= 0.18
            or len(heading_overlap_terms) >= 2
            or heading_overlap >= 0.40
            or fuzzy_ratio >= 0.88
        )

        rows.append(
            {
                **chunk,
                "score": float(score),
                "overlap": len(overlap_terms),
                "match_type": match_type,
                "matched_terms": overlap_terms,
                "strong_match": strong_match,
                "score_components": {
                    "bm25_norm": round(float(bm25_component), 4),
                    "overlap_norm": round(float(overlap_norm), 4),
                    "exact_bonus": round(float(exact_bonus), 4),
                    "heading_bonus": round(float(heading_bonus), 4),
                    "fuzzy_bonus": round(float(fuzzy_bonus), 4),
                    "fuzzy_ratio": round(float(fuzzy_ratio), 4),
                },
            }
        )

    ranked = _dedupe_ranked_chunks(rows)
    threshold = float(min_score)
    results: list[dict[str, Any]] = []
    for row in ranked:
        if float(row.get("score", 0.0)) < threshold:
            continue
        chunk_id = row.get("chunk_id")
        if str(chunk_id).isdigit():
            chunk_id = int(chunk_id)
        source_label = str(row.get("source_label", "")).strip() or f"Chunk {chunk_id or 1}"
        result_row = {
            **row,
            "chunk_id": chunk_id,
            "source_label": source_label,
            "source": source_label,
            "score": float(row.get("score", 0.0)),
            "overlap": int(row.get("overlap", 0)),
            "match_type": str(row.get("match_type", "hybrid")),
            "strong_match": bool(row.get("strong_match", False)),
            "score_components": dict(row.get("score_components", {})),
        }
        results.append(result_row)
        if len(results) >= max(1, int(k)):
            break

    reason = "hybrid"
    if not ranked:
        reason = "no_hits"
    elif not results:
        reason = "below_min_score"

    stitched_results = list(results)
    stitched_added_rows: list[dict[str, Any]] = []
    context_chars_used = sum(_chunk_text_len(row) for row in stitched_results)
    context_chars_budget = context_budget_debug
    if results and context_chars_budget > 0:
        stitched_results, stitched_added_rows, context_chars_used = _stitch_section_chunks(
            selected_rows=results,
            all_chunks=chunks,
            max_context_chars=context_chars_budget,
        )

    top_candidates = [_debug_chunk_row(item, idx) for idx, item in enumerate(ranked[:8])]
    chunks_final = [_debug_chunk_row(item, idx) for idx, item in enumerate(stitched_results)]
    stitched_debug = [
        _debug_chunk_row(item, idx)
        for idx, item in enumerate(stitched_added_rows)
    ]
    _set_last_kb_debug(
        {
            "query": query,
            "query_original": str(expansion_meta.get("query_original", query)),
            "query_expanded": expanded_query,
            "expansion_notes": list(expansion_meta.get("expansion_notes", [])),
            "kb_name": kb_name,
            "chunks_total": len(chunks),
            "retrieved_count": len(stitched_results),
            "reason": reason,
            "retrieval_method": "hybrid",
            "min_score": threshold,
            "chunks_final": chunks_final,
            "chunks_added_by_stitching": stitched_debug,
            "stitching_added_count": len(stitched_added_rows),
            "context_chars_used": context_chars_used,
            "context_chars_budget": context_chars_budget,
            "top_candidates": top_candidates,
        }
    )
    return stitched_results
