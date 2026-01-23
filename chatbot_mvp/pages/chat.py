import reflex as rx

from chatbot_mvp.components.layout import layout
from chatbot_mvp.components.typing_indicator import typing_indicator, skeleton_loader
from chatbot_mvp.components.quick_replies import contextual_quick_replies
from chatbot_mvp.state.chat_state import ChatState
from chatbot_mvp.ui.tokens import (
    CHAT_SURFACE_STYLE,
    CHAT_MESSAGE_USER_STYLE,
    CHAT_MESSAGE_ASSISTANT_STYLE,
    CHAT_INPUT_STYLE,
    CHAT_SEND_BUTTON_STYLE,
)


def _message_row(message: dict[str, str]) -> rx.Component:
    is_user = message["role"] == "user"
    return rx.hstack(
        rx.box(
            rx.text(message["content"], white_space="pre-wrap"),
            padding="0.75rem 1rem",
            border_radius="0.75rem",
            max_width="75%",
            background=rx.cond(is_user, "var(--chat-user-bg)", "var(--chat-assistant-bg)"),
            color=rx.cond(is_user, "white", "var(--gray-800)"),
            box_shadow=rx.cond(is_user, "var(--chat-shadow-md)", "var(--chat-shadow-sm)"),
            transition="var(--chat-transition)",
        ),
        justify=rx.cond(is_user, "end", "start"),
        width="100%",
        animation="fadeIn 0.3s ease-in-out",
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
                    rx.cond(ChatState.typing, typing_indicator()),
                    rx.cond(ChatState.loading, skeleton_loader()),
                    spacing="3",
                    width="100%",
                ),
                **CHAT_SURFACE_STYLE,
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
                    placeholder="Escribe tu mensaje...",
                    width="100%",
                    box_shadow="var(--chat-shadow-sm)",
                    border="var(--chat-border-modern)",
                    transition="var(--chat-transition)",
                    disabled=ChatState.loading,
                    opacity=rx.cond(ChatState.loading, 0.6, 1),
                ),
                rx.button(
                    "Enviar", 
                    on_click=ChatState.send_message,
                    background="var(--chat-bg-gradient)",
                    box_shadow="var(--chat-shadow-sm)",
                    transition="var(--chat-transition)",
                    disabled=ChatState.loading,
                    opacity=rx.cond(ChatState.loading, 0.6, 1),
                    loading=ChatState.loading,
                ),
                spacing="2",
                width="100%",
                max_width="640px",
            ),
            # Add contextual quick replies after the input area
            rx.cond(
                ChatState.messages,
                contextual_quick_replies(
                    last_message=ChatState.messages[-1]["content"],
                    on_reply=lambda reply: ChatState.handle_quick_reply(reply),
                    disabled=ChatState.loading,
                ),
            ),
            spacing="4",
            align="start",
            width="100%",
        )
    )
