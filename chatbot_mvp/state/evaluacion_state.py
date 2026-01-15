from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import reflex as rx

from chatbot_mvp.config.settings import is_demo_mode
from chatbot_mvp.data.juego_etico import QUESTIONS


class EvaluacionState(rx.State):
    current_index: int = 0
    responses: dict[str, Any] = {}
    error_message: str = ""
    finished: bool = False
    score: int = 0
    level: str = ""
    ai_simulated_text: str = ""

    @rx.var
    def progress_label(self) -> str:
        return f"Pregunta {self.current_index + 1} de {len(QUESTIONS)}"

    @rx.var
    def current_question(self) -> dict[str, Any]:
        return QUESTIONS[self.current_index]

    @rx.var
    def current_section(self) -> str:
        return self.current_question["section"]

    @rx.var
    def current_prompt(self) -> str:
        return self.current_question["prompt"]

    @rx.var
    def current_type(self) -> str:
        return self.current_question["type"]

    @rx.var
    def current_options(self) -> list[str]:
        return self.current_question.get("options", [])

    @rx.var
    def current_text_value(self) -> str:
        value = self.responses.get(self.current_question["id"])
        return value if isinstance(value, str) else ""

    @rx.var
    def current_single_value(self) -> str:
        value = self.responses.get(self.current_question["id"])
        return value if isinstance(value, str) else ""

    @rx.var
    def current_multi_values(self) -> list[str]:
        value = self.responses.get(self.current_question["id"])
        return value if isinstance(value, list) else []

    @rx.var
    def current_consent_value(self) -> bool:
        value = self.responses.get(self.current_question["id"])
        return bool(value)

    @rx.var
    def current_placeholder(self) -> str:
        return self.current_question.get("placeholder", "Escribe tu respuesta")

    @rx.var
    def evaluation_text(self) -> str:
        return self.ai_simulated_text

    def start(self) -> None:
        self.current_index = 0
        self.responses = {}
        self.error_message = ""
        self.finished = False
        self.score = 0
        self.level = ""
        self.ai_simulated_text = ""

    def set_current_response(self, value: Any) -> None:
        question_id = QUESTIONS[self.current_index]["id"]
        self.responses = {**self.responses, question_id: value}
        if self.error_message:
            self.error_message = ""

    def toggle_multi(self, option: str) -> None:
        question_id = QUESTIONS[self.current_index]["id"]
        current = self.responses.get(question_id)
        if not isinstance(current, list):
            current = []
        if option in current:
            current = [value for value in current if value != option]
        else:
            current = [*current, option]
        self.responses = {**self.responses, question_id: current}
        if self.error_message:
            self.error_message = ""

    def is_checked(self, option: str) -> bool:
        question_id = QUESTIONS[self.current_index]["id"]
        current = self.responses.get(question_id)
        if not isinstance(current, list):
            return False
        return option in current

    def next_step(self) -> None:
        question = QUESTIONS[self.current_index]
        response = self.responses.get(question["id"])
        if not self._is_valid_response(question, response):
            self.error_message = "Completa la respuesta antes de continuar."
            return

        self.error_message = ""
        if self.current_index >= len(QUESTIONS) - 1:
            self.finish()
            return

        self.current_index += 1

    def prev_step(self) -> None:
        if self.current_index <= 0:
            return
        self.current_index -= 1
        self.error_message = ""

    def finish(self) -> None:
        score = 0
        for question in QUESTIONS:
            if not question.get("scored"):
                continue
            correct = question.get("correct")
            if not correct:
                continue
            response = self.responses.get(question["id"])
            if response == correct:
                score += 1

        level, ai_text = self._score_to_level(score)
        self.score = score
        self.level = level
        self.ai_simulated_text = ai_text
        self.finished = True
        self.error_message = ""
        self._save_submission()

    def _is_valid_response(self, question: dict[str, Any], response: Any) -> bool:
        if not question.get("required"):
            return True
        question_type = question.get("type")
        if question_type == "consent":
            return response is True
        if question_type in {"text", "single"}:
            return isinstance(response, str) and response.strip() != ""
        if question_type == "multi":
            return isinstance(response, list) and len(response) > 0
        return response is not None

    def _score_to_level(self, score: int) -> tuple[str, str]:
        if score <= 5:
            level = "bajo"
            text = (
                "Respuesta IA simulada: Tu nivel es bajo. Te recomendamos revisar los "
                "principios de justicia y sesgo algoritmico antes de continuar."
            )
        elif score <= 11:
            level = "medio"
            text = (
                "Respuesta IA simulada: Tu nivel es medio. Comprendes conceptos clave, "
                "pero aun puedes profundizar en ejemplos y mecanismos de mitigacion."
            )
        else:
            level = "alto"
            text = (
                "Respuesta IA simulada: Tu nivel es alto. Demuestras buen dominio de "
                "criterios eticos y practicas para una IA justa."
            )
        return level, text

    def _save_submission(self) -> None:
        base_dir = Path(__file__).resolve().parents[2]
        data_dir = base_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "submission_id": str(uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "demo_mode": is_demo_mode(),
            "responses": self.responses,
            "score": self.score,
            "level": self.level,
        }
        with (data_dir / "submissions.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
