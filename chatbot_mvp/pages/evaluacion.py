import reflex as rx

from chatbot_mvp.components.layout import layout
from chatbot_mvp.state.evaluacion_state import (
    CONSENT_QUESTION,
    EvaluacionState,
)
from chatbot_mvp.ui.evaluacion_tokens import (
    EVAL_BADGE_ROW_STYLE,
    EVAL_BUTTON_ROW_STYLE,
    EVAL_CARD_HEADER_STYLE,
    EVAL_CARD_STYLE,
    EVAL_CHOICE_GROUP_STYLE,
    EVAL_CHOICE_ITEM_STYLE,
    EVAL_CONTAINER_STYLE,
    EVAL_ERROR_TEXT_STYLE,
    EVAL_INPUT_PROPS,
    EVAL_LABEL_STACK_STYLE,
    EVAL_MULTI_CHECKBOX_STYLE,
    EVAL_MULTI_HINT_BOX_STYLE,
    EVAL_MULTI_HINT_TEXT_STYLE,
    EVAL_PROGRESS_STACK_STYLE,
    EVAL_PRIMARY_BUTTON_PROPS,
    EVAL_PROMPT_TEXT_STYLE,
    EVAL_RESULT_BOX_STYLE,
    EVAL_SECTION_STACK_STYLE,
    EVAL_SECONDARY_BUTTON_PROPS,
    EVAL_SUBTITLE_STYLE,
    EVAL_TITLE_STYLE,
)


def _consent_input() -> rx.Component:
    return rx.hstack(
        rx.checkbox(
            is_checked=EvaluacionState.consent_checked,
            on_change=EvaluacionState.set_consent_checked,
            size="2",
        ),
        rx.text(
            CONSENT_QUESTION["options"][0],
            color="var(--gray-50)",
            size="2",
        ),
        spacing="2",
        align="center",
    )


def _text_input() -> rx.Component:
    return rx.input(
        value=EvaluacionState.current_text_value,
        on_change=EvaluacionState.set_current_response,
        placeholder=EvaluacionState.current_placeholder,
        color="var(--gray-50)",
        background="rgba(255, 255, 255, 0.08)",
        border="1px solid rgba(255, 255, 255, 0.12)",
        _placeholder={"color": "var(--gray-400)"},
        _focus={"border": "1px solid rgba(96, 165, 250, 0.5)"},
        **EVAL_INPUT_PROPS,
    )


def _single_input() -> rx.Component:
    return rx.radio_group.root(
        rx.vstack(
            rx.foreach(
                EvaluacionState.current_options,
                lambda option: rx.hstack(
                    rx.radio_group.item(value=option),
                    rx.text(option, color="var(--gray-900)", size="2"),
                    spacing="2",
                    align="center",
                ),
            ),
            spacing="2",
            align="stretch",
        ),
        value=EvaluacionState.current_single_value,
        on_change=EvaluacionState.set_current_response,
        size="2",
    )


def _multi_input() -> rx.Component:
    return rx.vstack(
        rx.foreach(
            EvaluacionState.current_options,
            lambda option: rx.hstack(
                rx.checkbox(
                    is_checked=EvaluacionState.is_checked(option),
                    on_change=lambda checked: EvaluacionState.set_multi_option(
                        option, checked
                    ),
                    size="2",
                ),
                rx.text(option, color="var(--gray-900)", size="2"),
                spacing="2",
                align="center",
            ),
        ),
        spacing="2",
        align="stretch",
    )


def _question_input() -> rx.Component:
    return rx.cond(
        EvaluacionState.current_type == "text",
        _text_input(),
        rx.cond(
            EvaluacionState.current_type == "single",
            _single_input(),
            _multi_input(),
        ),
    )


def _consent_view() -> rx.Component:
    return rx.vstack(
        rx.card(
            rx.vstack(
                rx.text(
                    CONSENT_QUESTION["prompt"],
                    **EVAL_PROMPT_TEXT_STYLE,
                ),
                _consent_input(),
                rx.cond(
                    EvaluacionState.error_message != "",
                    rx.text(EvaluacionState.error_message, **EVAL_ERROR_TEXT_STYLE),
                    rx.box(),
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            **EVAL_CARD_STYLE,
        ),
        rx.card(
            rx.hstack(
                rx.button(
                    "Continuar",
                    on_click=EvaluacionState.next_step,
                    **EVAL_PRIMARY_BUTTON_PROPS,
                ),
                **EVAL_BUTTON_ROW_STYLE,
            ),
            **EVAL_CARD_STYLE,
        ),
        **EVAL_PROGRESS_STACK_STYLE,
    )


def _in_progress_view() -> rx.Component:
    return rx.vstack(
        rx.card(
            rx.vstack(
                rx.text(EvaluacionState.current_prompt, **EVAL_PROMPT_TEXT_STYLE),
                rx.cond(
                    EvaluacionState.current_type == "multi",
                    rx.box(
                        rx.text(
                            "Podés elegir más de una opción.",
                            **EVAL_MULTI_HINT_TEXT_STYLE,
                        ),
                        **EVAL_MULTI_HINT_BOX_STYLE,
                    ),
                    rx.box(),
                ),
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
                rx.cond(
                    EvaluacionState.is_last_question,
                    rx.button(
                        rx.cond(
                            EvaluacionState.processing_result,
                            rx.hstack(
                                rx.spinner(size="1"),
                                rx.text("Analizando..."),
                                spacing="2",
                            ),
                            "Finalizar",
                        ),
                        on_click=EvaluacionState.next_step,
                        is_disabled=EvaluacionState.processing_result,
                        **EVAL_PRIMARY_BUTTON_PROPS,
                    ),
                    rx.button(
                        "Siguiente",
                        on_click=EvaluacionState.next_step,
                        **EVAL_PRIMARY_BUTTON_PROPS,
                    ),
                ),
                **EVAL_BUTTON_ROW_STYLE,
            ),
            **EVAL_CARD_STYLE,
        ),
        **EVAL_PROGRESS_STACK_STYLE,
    )


def _loading_analysis_view() -> rx.Component:
    """Pantalla intermedia mientras se analiza la evaluación."""
    return rx.card(
        rx.vstack(
            rx.spinner(size="3", color="var(--teal-9)"),
            rx.text(
                "Analizando tu evaluación...",
                size="4",
                color="var(--gray-50)",
                font_weight="600",
            ),
            spacing="4",
            align="center",
            justify="center",
        ),
        padding="4rem 2rem",
        **EVAL_CARD_STYLE,
    )


def _finished_view() -> rx.Component:
    result_box_style = {
        **EVAL_RESULT_BOX_STYLE,
        "background": "rgba(17, 17, 17, 0.98)",
        "border": "1px solid rgba(255, 255, 255, 0.08)",
        "padding": "1.5rem",
    }
    display_text = rx.cond(
        EvaluacionState.eval_stream_active,
        EvaluacionState.eval_stream_text + "▍",
        EvaluacionState.ai_simulated_text,
    )
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
                rx.text(
                    display_text,
                    white_space="pre-wrap",
                    color="var(--gray-50)",
                    line_height="1.6",
                ),
                **result_box_style,
            ),
            rx.hstack(
                rx.button(
                    "Reiniciar",
                    on_click=EvaluacionState.start,
                    **EVAL_PRIMARY_BUTTON_PROPS,
                ),
                rx.link(
                    rx.button(
                        "Ir a Inicio",
                        **EVAL_SECONDARY_BUTTON_PROPS,
                    ),
                    href="/",
                    text_decoration="none",
                ),
                spacing="3",
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
                        rx.text(
                            "El AI Act no busca frenar la innovación, sino garantizar que la inteligencia artificial se desarrolle al servicio de las personas, con equidad, transparencia y responsabilidad.",
                            color="var(--gray-300)",
                            size="3",
                        ),
                        rx.cond(
                            EvaluacionState.consent_given,
                            rx.hstack(
                                rx.badge(EvaluacionState.current_section, variant="soft"),
                                rx.badge(EvaluacionState.progress_label, variant="soft"),
                                **EVAL_BADGE_ROW_STYLE,
                            ),
                            rx.box(),
                        ),
                        **EVAL_CARD_HEADER_STYLE,
                    ),
                    **EVAL_CARD_STYLE,
                ),
                rx.cond(
                    EvaluacionState.finished,
                    rx.cond(
                        EvaluacionState.show_loading,
                        _loading_analysis_view(),
                        _finished_view(),
                    ),
                    rx.cond(
                        EvaluacionState.consent_given,
                        _in_progress_view(),
                        _consent_view(),
                    ),
                ),
                **EVAL_SECTION_STACK_STYLE,
            ),
            **EVAL_CONTAINER_STYLE,
        ),
        active_route="/evaluacion",
    )
