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

CHAT_SURFACE_DARK_STYLE = {
    **CHAT_SURFACE_STYLE,
    "background": "rgba(15, 23, 42, 0.92)",
    "border": "1px solid rgba(148, 163, 184, 0.25)",
    "box_shadow": "0 12px 40px rgba(0,0,0,0.25)",
}

CHAT_INPUT_LEGIBLE_STYLE = {
    **CHAT_INPUT_STYLE,
    "background": "rgba(15, 23, 42, 0.9)",
    "color": "var(--gray-50)",
    "border": "1px solid rgba(148, 163, 184, 0.6)",
    "_placeholder": {"color": "rgba(226, 232, 240, 0.7)"},
}


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


from chatbot_mvp.components.chat_sidebar import chat_sidebar

def chat() -> rx.Component:
    return layout(
        rx.hstack(
            chat_sidebar(),
            rx.vstack(
                rx.hstack(
                    rx.heading("Chat", size="8"),
                    rx.hstack(
                        rx.button("Exportar", on_click=lambda: ChatState.export_session("json"), variant="outline", size="2"),
                        rx.button(
                            "Nuevo Chat",
                            on_click=ChatState.clear_chat,
                            variant="soft",
                            size="2",
                        ),
                        spacing="2",
                    ),
                    justify="between",
                    align="center",
                    width="100%",
                    max_width="800px",
                ),
                rx.box(
                    rx.vstack(
                        rx.foreach(ChatState.messages, _message_row),
                        rx.cond(ChatState.typing, typing_indicator()),
                        rx.cond(ChatState.loading, skeleton_loader()),
                        spacing="3",
                        width="100%",
                    ),
                    **CHAT_SURFACE_DARK_STYLE,
                    width="100%",
                    max_width="800px",
                    flex="1",
                    min_height="0",
                    overflow_y="auto",
                ),
                rx.cond(
                    ChatState.last_error != "",
                    rx.callout(
                        ChatState.last_error,
                        icon="triangle_alert",
                        color_scheme="orange",
                        width="100%",
                        max_width="800px",
                        style={
                            "background": "rgba(124, 45, 18, 0.92)",
                            "color": "var(--gray-50)",
                            "border": "1px solid rgba(251, 191, 36, 0.4)",
                        },
                    ),
                    rx.box(),
                ),
                rx.hstack(
                    rx.input(
                        value=ChatState.current_input,
                        on_change=ChatState.set_input,
                        on_key_down=ChatState.handle_key_down,
                        placeholder="Escribe tu mensaje...",
                        width="100%",
                        disabled=ChatState.loading,
                        style=CHAT_INPUT_LEGIBLE_STYLE,
                    ),
                    rx.button(
                        rx.icon("send", size=18),
                        on_click=ChatState.send_message,
                        **CHAT_SEND_BUTTON_STYLE,
                        loading=ChatState.loading,
                        disabled=ChatState.loading,
                    ),
                    spacing="2",
                    width="100%",
                    max_width="800px",
                    margin_top="auto",
                ),
                spacing="6",
                align="center",
                width="100%",
                height="100%",
                min_height="0",
                display="flex",
                flex_direction="column",
                flex="1",
                padding="2rem 1rem",
            ),
            width="100%",
            align_items="stretch",
            spacing="0",
            height="100%",
            min_height="0",
            style={
                "height": "calc(100vh - 72px)",
                "overflow": "hidden",
            },
        )
    )
