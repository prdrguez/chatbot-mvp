import reflex as rx

from chatbot_mvp.components.layout import layout
from chatbot_mvp.state.evaluacion_state import EvaluacionState
from chatbot_mvp.ui.evaluacion_tokens import (
    EVAL_BADGE_ROW_STYLE,
    EVAL_BUTTON_ROW_STYLE,
    EVAL_CARD_HEADER_STYLE,
    EVAL_CARD_STYLE,
    EVAL_CHECKBOX_STYLE,
    EVAL_CONTAINER_STYLE,
    EVAL_ERROR_TEXT_STYLE,
    EVAL_INPUT_PROPS,
    EVAL_LABEL_STACK_STYLE,
    EVAL_OPTION_STACK_STYLE,
    EVAL_PROGRESS_STACK_STYLE,
    EVAL_PRIMARY_BUTTON_PROPS,
    EVAL_PROMPT_TEXT_STYLE,
    EVAL_RADIO_ITEM_STYLE,
    EVAL_RESULT_BOX_STYLE,
    EVAL_SECTION_STACK_STYLE,
    EVAL_SECONDARY_BUTTON_PROPS,
    EVAL_SUBTITLE_STYLE,
    EVAL_TITLE_STYLE,
)


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
        **EVAL_INPUT_PROPS,
    )


def _single_input() -> rx.Component:
    return rx.radio_group.root(
        rx.vstack(
            rx.foreach(
                EvaluacionState.current_options,
                lambda option: rx.radio_group.item(
                    option,
                    value=option,
                    **EVAL_RADIO_ITEM_STYLE,
                ),
            ),
            **EVAL_OPTION_STACK_STYLE,
        ),
        value=EvaluacionState.current_single_value,
        on_change=EvaluacionState.set_current_response,
        **EVAL_INPUT_PROPS,
    )


def _multi_input() -> rx.Component:
    return rx.vstack(
        rx.foreach(
            EvaluacionState.current_options,
            lambda option: rx.checkbox(
                option,
                is_checked=EvaluacionState.is_checked(option),
                on_change=lambda _: EvaluacionState.toggle_multi(option),
                **EVAL_CHECKBOX_STYLE,
            ),
        ),
        **EVAL_OPTION_STACK_STYLE,
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
                rx.text(EvaluacionState.current_prompt, **EVAL_PROMPT_TEXT_STYLE),
                _question_input(),
                rx.cond(
                    EvaluacionState.error_message != "",
                    rx.text(EvaluacionState.error_message, **EVAL_ERROR_TEXT_STYLE),
                    rx.box(),
                ),
                **EVAL_PROGRESS_STACK_STYLE,
            ),
            **EVAL_CARD_STYLE,
        ),
        rx.card(
            rx.hstack(
                rx.button(
                    "Atras",
                    on_click=EvaluacionState.prev_step,
                    is_disabled=EvaluacionState.current_index == 0,
                    **EVAL_SECONDARY_BUTTON_PROPS,
                ),
                rx.button(
                    "Siguiente",
                    on_click=EvaluacionState.next_step,
                    **EVAL_PRIMARY_BUTTON_PROPS,
                ),
                **EVAL_BUTTON_ROW_STYLE,
            ),
            **EVAL_CARD_STYLE,
        ),
        **EVAL_PROGRESS_STACK_STYLE,
    )


def _finished_view() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("Completado", **EVAL_TITLE_STYLE),
            rx.vstack(
                rx.text("Puntaje:", **EVAL_SUBTITLE_STYLE),
                rx.text(EvaluacionState.correct_count, "/", EvaluacionState.total_scored),
                rx.text("Nivel:", **EVAL_SUBTITLE_STYLE),
                rx.text(EvaluacionState.level),
                **EVAL_LABEL_STACK_STYLE,
            ),
            rx.box(
                rx.text(EvaluacionState.ai_simulated_text, white_space="pre-wrap"),  # unique
                **EVAL_RESULT_BOX_STYLE,
            ),
            rx.button(
                "Reiniciar",
                on_click=EvaluacionState.start,
                **EVAL_PRIMARY_BUTTON_PROPS,
            ),
            **EVAL_SECTION_STACK_STYLE,
        ),
        **EVAL_CARD_STYLE,
    )


def evaluacion() -> rx.Component:
    return layout(
        rx.container(
            rx.vstack(
                rx.card(
                    rx.vstack(
                        rx.heading("Juego Ético", **EVAL_TITLE_STYLE),
                        rx.hstack(
                            rx.badge(EvaluacionState.current_section, variant="soft"),
                            rx.badge(EvaluacionState.progress_label, variant="soft"),
                            **EVAL_BADGE_ROW_STYLE,
                        ),
                        **EVAL_CARD_HEADER_STYLE,
                    ),
                    **EVAL_CARD_STYLE,
                ),
                rx.cond(EvaluacionState.finished, _finished_view(), _in_progress_view()),
                **EVAL_SECTION_STACK_STYLE,
            ),
            **EVAL_CONTAINER_STYLE,
        )
    )
