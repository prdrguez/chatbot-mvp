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
    return rx.radio_group.root(
        rx.vstack(
            rx.foreach(
                EvaluacionState.current_options,
                lambda option: rx.radio_group.item(
                    option,
                    value=option,
                    width="100%",
                    white_space="normal",
                    align_items="flex-start",
                ),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        value=EvaluacionState.current_single_value,
        on_change=EvaluacionState.set_current_response,
        width="100%",
    )


def _multi_input() -> rx.Component:
    return rx.vstack(
        rx.foreach(
            EvaluacionState.current_options,
            lambda option: rx.checkbox(
                option,
                is_checked=EvaluacionState.is_checked(option),
                on_change=lambda _: EvaluacionState.toggle_multi(option),
                width="100%",
                white_space="normal",
            ),
        ),
        spacing="2",
        align="start",
        width="100%",
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
        rx.card(
            rx.vstack(
                rx.text(EvaluacionState.current_prompt, size="5", font_weight="600"),
                _question_input(),
                rx.cond(
                    EvaluacionState.error_message != "",
                    rx.text(EvaluacionState.error_message, color="red"),
                    rx.box(),
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            width="100%",
        ),
        rx.card(
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
            width="100%",
        ),
        spacing="3",
        align="start",
        width="100%",
    )


def _finished_view() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("Completado", size="7"),
            rx.vstack(
                rx.text("Puntaje:", font_weight="600"),
                rx.text(EvaluacionState.correct_count, "/", EvaluacionState.total_scored),
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
        ),
        width="100%",
    )


def evaluacion() -> rx.Component:
    return layout(
        rx.container(
            rx.vstack(
                rx.card(
                    rx.vstack(
                        rx.heading("Juego Ético", size="7"),
                        rx.hstack(
                            rx.badge(EvaluacionState.current_section, variant="soft"),
                            rx.badge(EvaluacionState.progress_label, variant="soft"),
                            spacing="2",
                            align="center",
                            width="100%",
                        ),
                        spacing="2",
                        align="start",
                        width="100%",
                    ),
                    width="100%",
                ),
                rx.cond(EvaluacionState.finished, _finished_view(), _in_progress_view()),
                spacing="4",
                align="start",
                width="100%",
            ),
            width="100%",
            max_width="900px",
        )
    )
