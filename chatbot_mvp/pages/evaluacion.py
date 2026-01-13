import reflex as rx

from chatbot_mvp.components.layout import layout
from chatbot_mvp.data.questions import QUESTIONS
from chatbot_mvp.state.evaluacion_state import EvaluacionState


def _in_progress_view() -> rx.Component:
    return rx.vstack(
        rx.text(EvaluacionState.step_label, font_weight="600"),
        rx.text(EvaluacionState.current_question, size="5"),
        rx.input(
            value=EvaluacionState.current_input,
            on_change=EvaluacionState.set_input,
            placeholder="Escribe tu respuesta",
            width="100%",
        ),
        rx.cond(
            EvaluacionState.error_message != "",
            rx.text(EvaluacionState.error_message, color="red"),
            rx.box(),
        ),
        rx.hstack(
            rx.button(
                "Atras",
                on_click=EvaluacionState.prev_step,
                is_disabled=EvaluacionState.current_step == 0,
                variant="outline",
            ),
            rx.button("Siguiente", on_click=EvaluacionState.next_step),
            spacing="3",
        ),
        spacing="3",
        align="start",
        width="100%",
        max_width="640px",
    )


def _summary_item(question: dict[str, str]) -> rx.Component:
    return rx.box(
        rx.text(question["question"], font_weight="600"),
        rx.text(EvaluacionState.answers.get(question["id"], "")),
    )


def _finished_view() -> rx.Component:
    return rx.vstack(
        rx.heading("Completado", size="7"),
        rx.vstack(
            rx.heading("Tu resultado", size="6"),
            rx.text(
                "Score: ",
                EvaluacionState.score,
                "/100",
                font_weight="600",
            ),
            rx.text(EvaluacionState.evaluation_text),
            spacing="2",
            align="start",
            width="100%",
        ),
        rx.vstack(
            rx.button(
                "Generar con IA",
                on_click=EvaluacionState.generate_ai_result,
                is_loading=EvaluacionState.ai_loading,
            ),
            rx.cond(
                EvaluacionState.ai_loading,
                rx.text("Generando..."),
                rx.box(),
            ),
            rx.cond(
                EvaluacionState.ai_error != "",
                rx.text(EvaluacionState.ai_error, color="red"),
                rx.box(),
            ),
            rx.cond(
                EvaluacionState.ai_result != "",
                rx.box(
                    rx.text(EvaluacionState.ai_result, white_space="pre-wrap"),
                    border="1px solid var(--gray-300)",
                    padding="1rem",
                    border_radius="0.5rem",
                    width="100%",
                ),
                rx.box(),
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        rx.vstack(
            rx.foreach(QUESTIONS, _summary_item),
            spacing="3",
            width="100%",
        ),
        rx.button("Reiniciar", on_click=EvaluacionState.start),
        spacing="4",
        align="start",
        width="100%",
        max_width="640px",
    )


def evaluacion() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Evaluación", size="8"),
            rx.cond(EvaluacionState.finished, _finished_view(), _in_progress_view()),
            spacing="4",
            align="start",
            width="100%",
        )
    )
