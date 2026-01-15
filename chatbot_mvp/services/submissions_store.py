import json
from pathlib import Path
from typing import Any

SUBMISSIONS_PATH = "data/submissions.jsonl"
_DEFAULT_TOTAL_SCORED = 15


def read_submissions() -> list[dict[str, Any]]:
    path = Path(SUBMISSIONS_PATH)
    if not path.exists():
        return []

    submissions: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            content = line.strip()
            if not content:
                continue
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                submissions.append(data)
    return submissions


def summarize(submissions: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(submissions)
    by_level: dict[str, int] = {}
    breakdowns: dict[str, dict[str, int]] = {
        "edad": {},
        "genero": {},
        "ciudad": {},
        "frecuencia_ia": {},
        "nivel_educativo": {},
        "ocupacion": {},
        "area": {},
    }
    emociones: dict[str, int] = {}

    total_correct = 0
    total_total = 0
    total_percent = 0

    for submission in submissions:
        level = submission.get("level")
        if isinstance(level, str) and level:
            by_level[level] = by_level.get(level, 0) + 1

        correct_count = submission.get("correct_count")
        if not isinstance(correct_count, int):
            correct_count = submission.get("score")
        if not isinstance(correct_count, int):
            correct_count = 0

        total_scored = submission.get("total_scored")
        if not isinstance(total_scored, int):
            total_scored = _DEFAULT_TOTAL_SCORED

        score_percent = submission.get("score_percent")
        if not isinstance(score_percent, int):
            score_percent = int((correct_count / total_scored) * 100) if total_scored else 0

        total_correct += correct_count
        total_total += total_scored
        total_percent += score_percent

        responses = submission.get("responses")
        if not isinstance(responses, dict):
            continue

        _count_value(breakdowns["edad"], responses.get("demo_age"))
        _count_value(breakdowns["genero"], responses.get("demo_gender"))
        _count_value(breakdowns["ciudad"], responses.get("context_city"))
        _count_value(breakdowns["frecuencia_ia"], responses.get("context_frequency"))
        _count_value(breakdowns["nivel_educativo"], responses.get("context_education"))
        _count_value(breakdowns["ocupacion"], responses.get("context_role"))
        _count_value(breakdowns["area"], responses.get("context_area"))

        emotions = responses.get("context_emotions")
        if isinstance(emotions, list):
            for emotion in emotions:
                _count_value(emociones, emotion)

    avg_correct = round(total_correct / total, 2) if total else 0
    avg_total = round(total_total / total, 2) if total else 0
    avg_percent = round(total_percent / total, 2) if total else 0

    return {
        "total": total,
        "by_level": by_level,
        "avg_correct": avg_correct,
        "avg_total": avg_total,
        "avg_percent": avg_percent,
        "breakdowns": breakdowns,
        "emociones": emociones,
    }


def _count_value(counter: dict[str, int], value: Any) -> None:
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            counter[cleaned] = counter.get(cleaned, 0) + 1
