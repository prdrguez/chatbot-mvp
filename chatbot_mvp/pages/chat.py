import reflex as rx

from chatbot_mvp.components.layout import layout
from chatbot_mvp.components.typing_indicator import typing_indicator, skeleton_loader
from chatbot_mvp.state.chat_state import ChatState
from chatbot_mvp.ui.tokens import (
    CHAT_INPUT_STYLE,
    CHAT_SEND_BUTTON_STYLE,
)

CHAT_APP_STYLE = {
    "background": "rgba(2, 6, 23, 0.96)",
}
CHAT_TOPBAR_STYLE = {
    "padding": "1rem 1.5rem",
    "border_bottom": "1px solid rgba(148, 163, 184, 0.15)",
    "background": "rgba(2, 6, 23, 0.98)",
}
CHAT_MESSAGES_STYLE = {
    "padding": "1.5rem 1.75rem",
    "overflow_y": "auto",
}
CHAT_COMPOSER_STYLE = {
    "padding": "1rem 1.5rem",
    "border_top": "1px solid rgba(148, 163, 184, 0.15)",
    "background": "rgba(2, 6, 23, 0.98)",
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
    return rx.vstack(
        rx.text(
            rx.cond(is_user, "Tú", "Asistente"),
            size="1",
            weight="medium",
            color=rx.cond(is_user, "var(--teal-8)", "var(--gray-400)"),
        ),
        rx.text(
            message["content"],
            white_space="pre-wrap",
            word_break="break-word",
            color="var(--gray-50)",
        ),
        spacing="1",
        align="start",
        width="100%",
        padding="0.85rem 0",
        border_bottom="1px solid rgba(148, 163, 184, 0.2)",
    )


from chatbot_mvp.components.chat_sidebar import chat_sidebar

def chat() -> rx.Component:
    return layout(
        rx.box(
            rx.hstack(
                chat_sidebar(),
                rx.box(
                    rx.vstack(
                        rx.box(
                            rx.hstack(
                                rx.heading("Chat", size="6", color="var(--gray-50)"),
                                rx.hstack(
                                    rx.button(
                                        "Exportar",
                                        on_click=lambda: ChatState.export_session("json"),
                                        variant="outline",
                                        size="2",
                                    ),
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
                            ),
                            width="100%",
                            **CHAT_TOPBAR_STYLE,
                        ),
                        rx.box(
                            rx.vstack(
                                rx.foreach(ChatState.messages, _message_row),
                                rx.cond(ChatState.typing, typing_indicator()),
                                rx.cond(ChatState.loading, skeleton_loader()),
                                spacing="3",
                                width="100%",
                            ),
                            width="100%",
                            flex="1",
                            min_height="0",
                            **CHAT_MESSAGES_STYLE,
                        ),
                        rx.cond(
                            ChatState.last_error != "",
                            rx.box(
                                rx.callout(
                                    ChatState.last_error,
                                    icon="triangle_alert",
                                    color_scheme="orange",
                                    width="100%",
                                    style={
                                        "background": "rgba(124, 45, 18, 0.92)",
                                        "color": "var(--gray-50)",
                                        "border": "1px solid rgba(251, 191, 36, 0.4)",
                                    },
                                ),
                                padding="0 1.5rem 1rem",
                            ),
                            rx.box(),
                        ),
                        rx.box(
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
                            ),
                            width="100%",
                            **CHAT_COMPOSER_STYLE,
                        ),
                        spacing="0",
                        align="stretch",
                        width="100%",
                        height="100%",
                        min_height="0",
                    ),
                    flex="1",
                    min_width="0",
                    height="100%",
                    overflow="hidden",
                ),
                width="100%",
                height="100%",
                min_height="0",
                align_items="stretch",
                spacing="0",
                flex="1",
            ),
            **CHAT_APP_STYLE,
            width="100%",
            height="100vh",
            min_height="0",
            overflow="hidden",
            display="flex",
            flex_direction="column",
        ),
        hide_header=True,
        full_width=True,
    )
