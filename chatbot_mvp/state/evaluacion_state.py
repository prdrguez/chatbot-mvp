import reflex as rx

from chatbot_mvp.data.questions import QUESTIONS


class EvaluacionState(rx.State):
    current_step: int = 0
    answers: dict[str, str] = {}
    current_input: str = ""
    finished: bool = False
    error_message: str = ""

    @rx.var
    def step_label(self) -> str:
        return f"Paso {self.current_step + 1} de {len(QUESTIONS)}"

    @rx.var
    def current_question(self) -> str:
        return QUESTIONS[self.current_step]["question"]

    def start(self) -> None:
        self.current_step = 0
        self.answers = {}
        self.current_input = ""
        self.finished = False
        self.error_message = ""

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
