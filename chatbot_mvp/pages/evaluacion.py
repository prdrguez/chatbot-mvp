import reflex as rx

from chatbot_mvp.components.layout import layout
from chatbot_mvp.state.evaluacion_state import EvaluacionState


def _consent_input() -> rx.Component:
    return rx.checkbox(
        EvaluacionState.current_options[0],
        is_checked=EvaluacionState.current_consent_value,
        on_change=EvaluacionState.set_current_response,
    )


def _text_input() -> rx.Component:
    return rx.input(
        value=EvaluacionState.current_text_value,
        on_change=EvaluacionState.set_current_response,
        placeholder=EvaluacionState.current_placeholder,
        width="100%",
    )


def _single_input() -> rx.Component:
    return rx.radio_group(
        items=EvaluacionState.current_options,
        value=EvaluacionState.current_single_value,
        on_change=EvaluacionState.set_current_response,
        spacing="2",
    )


def _multi_input() -> rx.Component:
    return rx.vstack(
        rx.foreach(
            EvaluacionState.current_options,
            lambda option: rx.checkbox(
                option,
                is_checked=EvaluacionState.is_checked(option),
                on_change=lambda _: EvaluacionState.toggle_multi(option),
            ),
        ),
        spacing="2",
        align="start",
    )


def _question_input() -> rx.Component:
    return rx.cond(
        EvaluacionState.current_type == "consent",
        _consent_input(),
        rx.cond(
            EvaluacionState.current_type == "text",
            _text_input(),
            rx.cond(
                EvaluacionState.current_type == "single",
                _single_input(),
                _multi_input(),
            ),
        ),
    )


def _in_progress_view() -> rx.Component:
    return rx.vstack(
        rx.text(EvaluacionState.current_section, font_weight="600"),
        rx.text(EvaluacionState.progress_label, font_weight="500"),
        rx.text(EvaluacionState.current_prompt, size="5"),
        _question_input(),
        rx.cond(
            EvaluacionState.error_message != "",
            rx.text(EvaluacionState.error_message, color="red"),
            rx.box(),
        ),
        rx.hstack(
            rx.button(
                "Atras",
                on_click=EvaluacionState.prev_step,
                is_disabled=EvaluacionState.current_index == 0,
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


def _finished_view() -> rx.Component:
    return rx.vstack(
        rx.heading("Completado", size="7"),
        rx.vstack(
            rx.text("Score:", font_weight="600"),
            rx.text(EvaluacionState.score),
            rx.text("Nivel:", font_weight="600"),
            rx.text(EvaluacionState.level),
            spacing="1",
            align="start",
            width="100%",
        ),
        rx.box(
            rx.text(EvaluacionState.ai_simulated_text, white_space="pre-wrap"),
            border="1px solid var(--gray-300)",
            padding="1rem",
            border_radius="0.5rem",
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
            rx.heading("Juego Ético: ¿Puede la IA ser justa?", size="8"),
            rx.cond(EvaluacionState.finished, _finished_view(), _in_progress_view()),
            spacing="4",
            align="start",
            width="100%",
        )
    )
