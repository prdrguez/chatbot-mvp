from __future__ import annotations

import asyncio
import logging
from typing import Any

import reflex as rx

from chatbot_mvp.config.settings import is_demo_mode
from chatbot_mvp.data.juego_etico import QUESTIONS
from chatbot_mvp.services.submissions_store import append_submission

logger = logging.getLogger(__name__)

CONSENT_QUESTION = next(
    (question for question in QUESTIONS if question.get("type") == "consent"),
    None,
)
NON_CONSENT_QUESTIONS = [
    question for question in QUESTIONS if question.get("type") != "consent"
]


class EvaluacionState(rx.State):
    current_index: int = 0
    responses: dict[str, Any] = {}
    error_message: str = ""
    finished: bool = False
    processing_result: bool = False
    show_loading: bool = False
    score: int = 0
    correct_count: int = 0
    total_scored: int = 0
    score_percent: int = 0
    level: str = ""
    ai_simulated_text: str = ""
    eval_stream_active: bool = False
    eval_stream_text: str = ""
    consent_checked: bool = False
    consent_given: bool = False

    @rx.var
    def progress_label(self) -> str:
        return f"Pregunta {self.current_index + 1} de {len(NON_CONSENT_QUESTIONS)}"

    @rx.var
    def is_last_question(self) -> bool:
        return self.current_index >= len(NON_CONSENT_QUESTIONS) - 1

    @rx.var
    def current_question(self) -> dict[str, Any]:
        return NON_CONSENT_QUESTIONS[self.current_index]

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
        self.processing_result = False
        self.show_loading = False
        self.score = 0
        self.correct_count = 0
        self.total_scored = 0
        self.score_percent = 0
        self.level = ""
        self.ai_simulated_text = ""
        self.eval_stream_active = False
        self.eval_stream_text = ""
        self.consent_checked = False
        self.consent_given = False

    def ensure_initialized(self) -> None:
        if self.finished:
            return
        if self.current_index != 0:
            return
        if self.responses:
            return
        self.start()

    def set_current_response(self, value: Any) -> None:
        question_id = NON_CONSENT_QUESTIONS[self.current_index]["id"]
        self.responses = {**self.responses, question_id: value}
        if self.error_message:
            self.error_message = ""

    def set_consent_checked(self, value: bool) -> None:
        self.consent_checked = bool(value)
        if self.error_message:
            self.error_message = ""

    def toggle_multi(self, option: str) -> None:
        question_id = NON_CONSENT_QUESTIONS[self.current_index]["id"]
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

    def set_multi_option(self, option: str, checked: bool) -> None:
        question_id = NON_CONSENT_QUESTIONS[self.current_index]["id"]
        current = self.responses.get(question_id)
        if not isinstance(current, list):
            current = []
        if checked and option not in current:
            current = [*current, option]
        elif not checked and option in current:
            current = [value for value in current if value != option]
        self.responses = {**self.responses, question_id: current}
        if self.error_message:
            self.error_message = ""

    def is_checked(self, option: str) -> bool:
        question_id = NON_CONSENT_QUESTIONS[self.current_index]["id"]
        current = self.responses.get(question_id)
        if not isinstance(current, list):
            return False
        return option in current

    def next_step(self) -> None:
        if not self.consent_given:
            if not self.consent_checked:
                self.error_message = "Completa la respuesta antes de continuar."
                return
            self.error_message = ""
            self.consent_given = True
            return

        question = NON_CONSENT_QUESTIONS[self.current_index]
        response = self.responses.get(question["id"])
        if not self._is_valid_response(question, response):
            self.error_message = "Completa la respuesta antes de continuar."
            return

        self.error_message = ""
        if self.current_index >= len(NON_CONSENT_QUESTIONS) - 1:
            self.finish()
            # Lanzar el streaming correctamente en Reflex
            return type(self).stream_evaluation_text(self.ai_simulated_text)

        self.current_index += 1
        self.processing_result = False
        self.show_loading = False

    def prev_step(self) -> None:
        if self.current_index <= 0:
            self.consent_given = False
            self.error_message = ""
            self.processing_result = False
            self.show_loading = False
            return
        self.current_index -= 1
        self.error_message = ""
        self.processing_result = False
        self.show_loading = False

    def finish(self) -> None:
        self.processing_result = True
        self.show_loading = True
        if self.eval_stream_active:
            self.eval_stream_active = False
            self.eval_stream_text = ""
        score = 0
        total_scored = 0
        for question in QUESTIONS:
            if not question.get("scored"):
                continue
            correct = question.get("correct")
            if not correct:
                continue
            total_scored += 1
            response = self.responses.get(question["id"])
            if not isinstance(response, str):
                continue
            normalized = self.normalize_choice(response)
            if normalized == correct:
                score += 1

        level, simulated_text = self._score_to_level(score)
        self.score = score
        self.correct_count = score
        self.total_scored = total_scored
        self.score_percent = int((score / total_scored) * 100) if total_scored else 0
        self.level = level
        self.ai_simulated_text = simulated_text

        evaluation_payload = self._build_evaluation_payload()
        try:
            from chatbot_mvp.config.settings import get_runtime_ai_provider

            provider = get_runtime_ai_provider()
            if provider == "groq":
                from chatbot_mvp.services.groq_client import (
                    generate_evaluation_feedback,
                )
            else:
                from chatbot_mvp.services.gemini_client import (
                    generate_evaluation_feedback,
                )

            ai_text = generate_evaluation_feedback(evaluation_payload)
            if ai_text:
                self.ai_simulated_text = ai_text
        except Exception as exc:
            logger.warning("Evaluation feedback failed: %s", exc)

        self.finished = True
        self.error_message = ""
        logger.info(
            "Evaluacion finished: score=%s, answers_count=%s",
            self.score,
            len(self.responses),
        )
        self._save_submission()
        # No lanzar streaming aquí; lo haremos desde next_step
        # Limpiar asteriscos markdown del texto
        clean_text = self.ai_simulated_text.replace("**", "").replace("*", "")
        self.ai_simulated_text = clean_text

    @rx.event(background=True)
    async def stream_evaluation_text(self, full_text: str) -> None:
        logger.info(f"stream_evaluation_text started with text: {len(full_text)} chars")
        # Esperar 2 segundos para que se vea la pantalla de "Analizando..."
        await asyncio.sleep(2.0)
        
        # SIEMPRE desactivar show_loading después de la espera
        async with self:
            self.show_loading = False
            if full_text:
                self.eval_stream_active = True
                self.eval_stream_text = ""
        
        # Si no hay texto, terminar aquí
        if not full_text:
            async with self:
                self.eval_stream_active = False
                self.eval_stream_text = ""
            return

        # Streaming del texto
        chunk_size = 6
        delay = 0.1
        for idx in range(0, len(full_text), chunk_size):
            async with self:
                if not self.eval_stream_active:
                    return
                self.eval_stream_text = full_text[: idx + chunk_size]
            await asyncio.sleep(delay)

        async with self:
            self.eval_stream_text = full_text
            self.eval_stream_active = False
            self.processing_result = False

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

    def normalize_choice(self, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            return ""
        for letter in ("A", "B", "C", "D"):
            if normalized.upper().startswith(letter):
                return letter
            if f"{letter})" in normalized or f"{letter}." in normalized:
                return letter
        return ""

    def _score_to_level(self, score: int) -> tuple[str, str]:
        if score <= 5:
            level = "Bajo"
            text = (
                "Respuesta IA simulada: Tu nivel es bajo. Te recomendamos revisar los "
                "principios de justicia y sesgo algoritmico antes de continuar."
            )
        elif score <= 10:
            level = "Medio"
            text = (
                "Respuesta IA simulada: Tu nivel es medio. Comprendes conceptos clave, "
                "pero aun puedes profundizar en ejemplos y mecanismos de mitigacion."
            )
        else:
            level = "Alto"
            text = (
                "Respuesta IA simulada: Tu nivel es alto. Demuestras buen dominio de "
                "criterios eticos y practicas para una IA justa."
            )
        return level, text

    def _build_evaluation_payload(self) -> dict[str, Any]:
        questions_payload: list[dict[str, Any]] = []
        for question in NON_CONSENT_QUESTIONS:
            question_id = question.get("id")
            response = self.responses.get(question_id)
            if isinstance(response, list):
                answer_text = ", ".join([str(item) for item in response if item])
            elif isinstance(response, bool):
                answer_text = "Acepto" if response else "No acepto"
            elif response is None:
                answer_text = ""
            else:
                answer_text = str(response)
            
            questions_payload.append(
                {
                    "id": question_id,
                    "section": question.get("section", ""),
                    "prompt": question.get("prompt", ""),
                    "answer": answer_text,
                    "type": question.get("type", ""),
                    "scored": bool(question.get("scored")),
                }
            )
        
        return {
            "summary": {
                "score": self.score,
                "correct_count": self.correct_count,
                "total_scored": self.total_scored,
                "score_percent": self.score_percent,
                "level": self.level,
            },
            "questions": questions_payload,
        }

    def _save_submission(self) -> None:
        append_submission(
            answers={**self.responses, "consent_given": self.consent_given},
            score=self.score,
            level=self.level,
            demo_mode=is_demo_mode(),
            correct_count=self.correct_count,
            total_scored=self.total_scored,
            score_percent=self.score_percent,
            ai_feedback=self.ai_simulated_text,
        )
