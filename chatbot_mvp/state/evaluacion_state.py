import reflex as rx

from chatbot_mvp.data.questions import QUESTIONS
from chatbot_mvp.services.openai_client import generate_evaluation


class EvaluacionState(rx.State):
    current_step: int = 0
    answers: dict[str, str] = {}
    current_input: str = ""
    finished: bool = False
    error_message: str = ""
    ai_result: str = ""
    ai_loading: bool = False
    ai_error: str = ""

    @rx.var
    def step_label(self) -> str:
        return f"Paso {self.current_step + 1} de {len(QUESTIONS)}"

    @rx.var
    def current_question(self) -> str:
        return QUESTIONS[self.current_step]["question"]

    @rx.var
    def score(self) -> int:
        if not self.answers:
            return 0

        total_words = sum(len(answer.split()) for answer in self.answers.values())
        avg_words = total_words / len(QUESTIONS)
        score = int(avg_words * 10)
        return max(0, min(100, score))

    @rx.var
    def evaluation_text(self) -> str:
        if self.score < 40:
            return (
                "Tu resultado es bajo. Conviene definir objetivos mas claros "
                "y ampliar detalles para orientar mejor la evaluacion."
            )
        if self.score < 70:
            return (
                "Tu resultado es medio. Tienes una base clara; sumar ejemplos "
                "concretos podria fortalecer la definicion."
            )
        return (
            "Tu resultado es alto. Las respuestas son consistentes y detalladas, "
            "con buena claridad de objetivos."
        )

    def start(self) -> None:
        self.current_step = 0
        self.answers = {}
        self.current_input = ""
        self.finished = False
        self.error_message = ""
        self.ai_result = ""
        self.ai_loading = False
        self.ai_error = ""

    def set_input(self, value: str) -> None:
        self.current_input = value
        if self.error_message:
            self.error_message = ""

    def next_step(self) -> None:
        value = self.current_input.strip()
        if not value:
            self.error_message = "Completa la respuesta antes de continuar."
            return

        question_id = QUESTIONS[self.current_step]["id"]
        self.answers = {**self.answers, question_id: value}
        self.error_message = ""

        if self.current_step >= len(QUESTIONS) - 1:
            self.finish()
            return

        self.current_step += 1
        next_question_id = QUESTIONS[self.current_step]["id"]
        self.current_input = self.answers.get(next_question_id, "")

    def prev_step(self) -> None:
        if self.current_step <= 0:
            return

        self.current_step -= 1
        question_id = QUESTIONS[self.current_step]["id"]
        self.current_input = self.answers.get(question_id, "")
        self.error_message = ""

    def finish(self) -> None:
        self.finished = True
        self.current_input = ""

    @rx.event(background=True)
    async def generate_ai_result(self) -> None:
        async with self:
            self.ai_loading = True
            self.ai_error = ""
            self.ai_result = ""
            answers_copy = dict(self.answers)

        result = generate_evaluation(answers_copy)

        async with self:
            if result.startswith("Error al generar con IA:"):
                self.ai_error = result
                self.ai_result = ""
            else:
                self.ai_result = result
            self.ai_loading = False
