import reflex as rx

from chatbot_mvp.components.layout import layout
from chatbot_mvp.state.chat_state import ChatState


def _message_row(message: dict[str, str]) -> rx.Component:
    is_user = message["role"] == "user"
    return rx.hstack(
        rx.box(
            rx.text(message["content"], white_space="pre-wrap"),
            background=rx.cond(is_user, "var(--blue-100)", "var(--gray-100)"),
            padding="0.75rem 1rem",
            border_radius="0.75rem",
            max_width="75%",
        ),
        justify=rx.cond(is_user, "end", "start"),
        width="100%",
    )


def chat() -> rx.Component:
    return layout(
        rx.vstack(
            rx.hstack(
                rx.heading("Chat", size="8"),
                rx.button(
                    "Reiniciar chat",
                    on_click=ChatState.clear_chat,
                    variant="outline",
                ),
                justify="between",
                align="center",
                width="100%",
                max_width="640px",
            ),
            rx.box(
                rx.vstack(
                    rx.foreach(ChatState.messages, _message_row),
                    spacing="3",
                    width="100%",
                ),
                border="1px solid var(--gray-200)",
                border_radius="0.75rem",
                padding="1rem",
                width="100%",
                max_width="640px",
                min_height="320px",
                max_height="420px",
                overflow_y="auto",
            ),
            rx.hstack(
                rx.input(
                    value=ChatState.current_input,
                    on_change=ChatState.set_input,
                    placeholder="Escribe tu mensaje",
                    width="100%",
                ),
                rx.button("Enviar", on_click=ChatState.send_message),
                spacing="2",
                width="100%",
                max_width="640px",
            ),
            spacing="4",
            align="start",
            width="100%",
        )
    )
