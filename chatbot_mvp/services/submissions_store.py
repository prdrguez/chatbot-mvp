import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from chatbot_mvp.data.juego_etico import (
    QUESTIONNAIRE_ID,
    QUESTIONNAIRE_VERSION,
    SCHEMA_VERSION,
    SCORING_VERSION,
    questions_fingerprint,
)

SUBMISSIONS_PATH = "data/submissions.jsonl"
EXPORT_DIR = "exports"
_DEFAULT_TOTAL_SCORED = 15


def append_submission(
    *,
    answers: dict[str, Any],
    score: Any,
    level: str,
    demo_mode: bool,
    correct_count: int | None = None,
    total_scored: int | None = None,
    score_percent: int | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "questionnaire_id": QUESTIONNAIRE_ID,
        "questionnaire_version": QUESTIONNAIRE_VERSION,
        "scoring_version": SCORING_VERSION,
        "questions_fingerprint": questions_fingerprint(),
        "created_at": _utc_now_iso(),
        "answers": answers,
        "score": score,
        "level": level,
        "context": {"demo_mode": demo_mode},
    }
    if isinstance(correct_count, int):
        payload["correct_count"] = correct_count
    if isinstance(total_scored, int):
        payload["total_scored"] = total_scored
    if isinstance(score_percent, int):
        payload["score_percent"] = score_percent

    path = Path(SUBMISSIONS_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return payload


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
    questionnaire_counts: dict[tuple[str, int, int], int] = {}

    for submission in submissions:
        questionnaire_key = _questionnaire_key(submission)
        questionnaire_counts[questionnaire_key] = (
            questionnaire_counts.get(questionnaire_key, 0) + 1
        )

        level = submission.get("level")
        if isinstance(level, str) and level:
            by_level[level] = by_level.get(level, 0) + 1

        correct_count, total_scored, score_percent = _extract_score_values(submission)

        total_correct += correct_count
        total_total += total_scored
        total_percent += score_percent

        responses = _extract_answers(submission)
        if not responses:
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

    questionnaire_mode = _mode_questionnaire(questionnaire_counts)

    return {
        "total": total,
        "by_level": by_level,
        "avg_correct": avg_correct,
        "avg_total": avg_total,
        "avg_percent": avg_percent,
        "breakdowns": breakdowns,
        "emociones": emociones,
        "questionnaire_mode": questionnaire_mode,
    }


def ensure_export_dir() -> None:
    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)


def export_json(submissions: list[dict[str, Any]]) -> str:
    ensure_export_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(EXPORT_DIR) / f"submissions_{timestamp}.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(submissions, handle, indent=2, ensure_ascii=False)
    return str(path)


def export_csv(submissions: list[dict[str, Any]]) -> str:
    ensure_export_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(EXPORT_DIR) / f"submissions_{timestamp}.csv"
    fieldnames = [
        "created_at",
        "age_range",
        "gender",
        "city",
        "ia_frequency",
        "education_level",
        "occupation",
        "area",
        "emotions",
        "score_level",
        "correct_count",
        "total_scored",
        "percent",
        "answers_json",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for submission in submissions:
            responses = _extract_answers(submission)

            emotions = responses.get("context_emotions")
            if not isinstance(emotions, list):
                emotions = []

            correct_count, total_scored, score_percent = _extract_score_values(submission)

            writer.writerow(
                {
                    "created_at": submission.get("created_at")
                    or submission.get("timestamp")
                    or "",
                    "age_range": responses.get("demo_age", ""),
                    "gender": responses.get("demo_gender", ""),
                    "city": responses.get("context_city", ""),
                    "ia_frequency": responses.get("context_frequency", ""),
                    "education_level": responses.get("context_education", ""),
                    "occupation": responses.get("context_role", ""),
                    "area": responses.get("context_area", ""),
                    "emotions": "|".join([str(item) for item in emotions if item]),
                    "score_level": submission.get("level", ""),
                    "correct_count": correct_count,
                    "total_scored": total_scored,
                    "percent": score_percent,
                    "answers_json": json.dumps(responses, ensure_ascii=False),
                }
            )
    return str(path)


def _count_value(counter: dict[str, int], value: Any) -> None:
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            counter[cleaned] = counter.get(cleaned, 0) + 1


def _extract_answers(submission: dict[str, Any]) -> dict[str, Any]:
    responses = submission.get("responses")
    if not isinstance(responses, dict):
        responses = submission.get("answers")
    return responses if isinstance(responses, dict) else {}


def _extract_score_values(submission: dict[str, Any]) -> tuple[int, int, int]:
    correct_count = submission.get("correct_count")
    total_scored = submission.get("total_scored")
    score_percent = submission.get("score_percent")
    score = submission.get("score")

    if isinstance(score, dict):
        if not isinstance(correct_count, int):
            correct_count = score.get("correct_count")
        if not isinstance(total_scored, int):
            total_scored = score.get("total_scored")
        if not isinstance(score_percent, int):
            score_percent = score.get("score_percent")
        if not isinstance(correct_count, int):
            score_value = score.get("score")
            if isinstance(score_value, int):
                correct_count = score_value

    if not isinstance(correct_count, int):
        if isinstance(score, int):
            correct_count = score
        else:
            correct_count = 0

    if not isinstance(total_scored, int):
        total_scored = _DEFAULT_TOTAL_SCORED

    if not isinstance(score_percent, int):
        score_percent = int((correct_count / total_scored) * 100) if total_scored else 0

    return correct_count, total_scored, score_percent


def _mode_questionnaire(
    counts: dict[tuple[str, int, int], int],
) -> dict[str, Any]:
    if not counts:
        return {}
    key = max(counts.items(), key=lambda item: item[1])[0]
    questionnaire_id, questionnaire_version, schema_version = key
    return {
        "questionnaire_id": questionnaire_id,
        "questionnaire_version": questionnaire_version,
        "schema_version": schema_version,
    }


def _questionnaire_key(submission: dict[str, Any]) -> tuple[str, int, int]:
    questionnaire_id = submission.get("questionnaire_id") or "legacy"
    questionnaire_version = submission.get("questionnaire_version")
    if not isinstance(questionnaire_version, int):
        questionnaire_version = 0
    schema_version = submission.get("schema_version")
    if not isinstance(schema_version, int):
        schema_version = 0
    return str(questionnaire_id), questionnaire_version, schema_version


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
