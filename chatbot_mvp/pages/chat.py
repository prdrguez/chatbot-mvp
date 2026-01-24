import reflex as rx

from chatbot_mvp.components.layout import layout
from chatbot_mvp.components.typing_indicator import typing_indicator, skeleton_loader
from chatbot_mvp.state.chat_state import ChatState
from chatbot_mvp.ui.tokens import (
    CHAT_SURFACE_STYLE,
    CHAT_MESSAGE_USER_STYLE,
    CHAT_MESSAGE_ASSISTANT_STYLE,
    CHAT_INPUT_STYLE,
    CHAT_SEND_BUTTON_STYLE,
)

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
                        rx.cond(
                            ChatState.has_messages,
                            rx.hstack(
                                rx.button(
                                    "Exportar JSON",
                                    on_click=ChatState.do_export_json,
                                    variant="outline",
                                    size="2",
                                ),
                                rx.button(
                                    "Exportar CSV",
                                    on_click=ChatState.do_export_csv,
                                    variant="outline",
                                    size="2",
                                ),
                                spacing="2",
                            ),
                            rx.box(),
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
                    **CHAT_SURFACE_STYLE,
                    width="100%",
                    max_width="800px",
                    min_height="400px",
                    max_height="60vh",
                    overflow_y="auto",
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
                ),
                rx.cond(
                    ChatState.export_error != "",
                    rx.callout(
                        ChatState.export_error,
                        icon="triangle_alert",
                        color_scheme="red",
                        width="100%",
                        max_width="800px",
                    ),
                    rx.box(),
                ),
                rx.cond(
                    ChatState.export_content != "",
                    rx.vstack(
                        rx.text(
                            f"Export {ChatState.export_format}",
                            size="2",
                            weight="medium",
                        ),
                        rx.box(
                            rx.text(
                                ChatState.export_content,
                                white_space="pre-wrap",
                                font_family="monospace",
                                font_size="0.85rem",
                            ),
                            padding="0.75rem",
                            border="1px solid var(--gray-300)",
                            border_radius="0.5rem",
                            background="white",
                            max_height="260px",
                            overflow_y="auto",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                        max_width="800px",
                    ),
                    rx.box(),
                ),
                spacing="6",
                align="center",
                width="100%",
                padding="2rem 1rem",
            ),
            width="100%",
            align_items="stretch",
            spacing="0",
        )
    )
