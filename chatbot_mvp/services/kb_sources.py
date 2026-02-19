from __future__ import annotations

import re
from pathlib import Path
from typing import Any

KB_SOURCES_MAX = 3
MAX_ITEM_LEN = 60
KB_NAME_MAX_LEN = 28

_ANCHOR_RE = re.compile(r"\s*\{#[^}]+\}\s*$")
_PART_RE = re.compile(r"\(\s*parte\s*([0-9]+\s*/\s*[0-9]+)\s*\)", re.IGNORECASE)
_MARKDOWN_HEADER_RE = re.compile(r"^\s*#{1,6}\s*")
_SECTION_PREFIX_RE = re.compile(r"^\s*(?:seccion|section)\s+", re.IGNORECASE)
_LEADING_NUMBER_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)*)\s*[-:.)]?\s*(.*)$")
_STOPWORDS = {
    "a",
    "al",
    "con",
    "de",
    "del",
    "el",
    "en",
    "la",
    "las",
    "los",
    "para",
    "por",
    "se",
    "y",
}


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _truncate(text: str, max_len: int) -> str:
    clean = str(text or "")
    if len(clean) <= max_len:
        return clean
    if max_len <= 1:
        return clean[:max_len]
    return clean[: max_len - 1].rstrip() + "…"


def compact_kb_name(kb_name: str, max_len: int = KB_NAME_MAX_LEN) -> str:
    raw_name = str(kb_name or "").strip()
    if not raw_name:
        return ""
    file_name = Path(raw_name.replace("\\", "/")).name
    if len(file_name) <= max_len:
        return file_name

    if "." not in file_name:
        return _truncate(file_name, max_len)

    stem, extension = file_name.rsplit(".", maxsplit=1)
    extension_suffix = f".{extension}"
    if len(extension_suffix) >= max_len - 1:
        return _truncate(file_name, max_len)

    head_len = max_len - len(extension_suffix) - 1
    if head_len <= 0:
        return _truncate(file_name, max_len)
    return f"{stem[:head_len].rstrip()}…{extension_suffix}"


def compact_section_label(section: str, part: str = "") -> str:
    raw = _normalize_spaces(str(section or ""))
    if not raw:
        return ""

    clean = _ANCHOR_RE.sub("", raw).strip()
    part_match = _PART_RE.search(clean)
    part_value = part.strip()
    if part_match:
        part_value = part_match.group(1).replace(" ", "")
        clean = _PART_RE.sub("", clean).strip()

    clean = _MARKDOWN_HEADER_RE.sub("", clean)
    clean = _SECTION_PREFIX_RE.sub("", clean)
    clean = _normalize_spaces(clean)

    number = ""
    title = clean
    number_match = _LEADING_NUMBER_RE.match(clean)
    if number_match:
        number = number_match.group(1).strip()
        title = number_match.group(2).strip()

    words = [token for token in re.split(r"[^A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ]+", title) if token]
    compact_words = [word for word in words if word.lower() not in _STOPWORDS]
    if len(compact_words) >= 2:
        title_short = " ".join(compact_words[:2])
    elif compact_words:
        title_short = compact_words[0]
    else:
        title_short = " ".join(words[:2]).strip()

    if number:
        compact = f"§{number}"
        if title_short:
            compact = f"{compact} {title_short}"
    elif title_short:
        compact = f"§ {title_short}"
    else:
        compact = f"§ {clean}".strip()

    if part_value:
        compact = f"{compact} ({part_value})"
    return _normalize_spaces(compact)


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _build_compact_item(source: dict[str, Any], max_item_len: int) -> str:
    kb_short = compact_kb_name(str(source.get("kb_name", "")))
    section_short = compact_section_label(
        str(source.get("section", "")),
        part=str(source.get("part", "")),
    )
    if kb_short and section_short:
        label = f"{kb_short} {section_short}"
    else:
        label = kb_short or section_short or str(source.get("source_label", "")).strip()
    return _truncate(_normalize_spaces(label), max_item_len)


def build_compact_sources_view(
    sources: list[dict[str, Any]],
    max_sources: int = KB_SOURCES_MAX,
    max_item_len: int = MAX_ITEM_LEN,
) -> dict[str, Any]:
    normalized_rows: list[dict[str, Any]] = []
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            continue
        compact_item = _build_compact_item(source, max_item_len=max_item_len)
        if not compact_item:
            continue
        normalized_rows.append(
            {
                "index": index,
                "compact": compact_item,
                "score": _to_float(source.get("score", 0.0)),
                "source": source,
            }
        )

    if not normalized_rows:
        return {
            "line": "",
            "compact_rows": [],
            "hidden_rows": [],
        }

    best_by_compact: dict[str, dict[str, Any]] = {}
    hidden_rows: list[dict[str, Any]] = []
    for row in normalized_rows:
        key = row["compact"]
        existing = best_by_compact.get(key)
        if existing is None:
            best_by_compact[key] = row
            continue
        if row["score"] > existing["score"]:
            hidden_rows.append(existing)
            best_by_compact[key] = row
        else:
            hidden_rows.append(row)

    unique_rows = list(best_by_compact.values())
    unique_rows.sort(
        key=lambda row: (row["score"], -int(row["index"])),
        reverse=True,
    )

    resolved_max = max(1, int(max_sources))
    compact_rows = unique_rows[:resolved_max]
    hidden_rows.extend(unique_rows[resolved_max:])

    line_parts = [f"[{idx}] {row['compact']}" for idx, row in enumerate(compact_rows, start=1)]
    line = ""
    if line_parts:
        line = "Fuentes: " + "; ".join(line_parts)

    return {
        "line": line,
        "compact_rows": compact_rows,
        "hidden_rows": hidden_rows,
    }


def format_source_detail(source: dict[str, Any], index: int) -> str:
    kb_name = str(source.get("kb_name", "")).strip()
    section = str(source.get("section", "")).strip()
    score = _to_float(source.get("score", 0.0))
    method = str(source.get("method", "")).strip()

    if kb_name and section:
        head = f"[{index}] {kb_name} | {section}"
    else:
        head = f"[{index}] {kb_name or section}".strip()

    detail_parts = [head]
    detail_parts.append(f"score={score:.4f}")
    if method:
        detail_parts.append(f"method={method}")
    return " | ".join(detail_parts)
