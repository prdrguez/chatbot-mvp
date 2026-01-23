import reflex as rx

from chatbot_mvp.ui.tokens import CHAT_MESSAGE_ASSISTANT_STYLE


def typing_indicator() -> rx.Component:
    """Component that shows when the assistant is typing."""
    return rx.hstack(
        rx.box(
            rx.hstack(
                # Typing dots animation
                rx.box(
                    width="8px",
                    height="8px",
                    border_radius="50%",
                    background="var(--gray-400)",
                    margin_right="4px",
                    animation="typing 1.4s ease-in-out infinite",
                ),
                rx.box(
                    width="8px",
                    height="8px",
                    border_radius="50%",
                    background="var(--gray-400)",
                    margin_right="4px",
                    animation="typing 1.4s ease-in-out 0.2s infinite",
                ),
                rx.box(
                    width="8px",
                    height="8px",
                    border_radius="50%",
                    background="var(--gray-400)",
                    animation="typing 1.4s ease-in-out 0.4s infinite",
                ),
                align="center",
            ),
            padding="0.75rem 1rem",
            border_radius="0.75rem",
            max_width="75%",
            **CHAT_MESSAGE_ASSISTANT_STYLE,
        ),
        justify="start",
        width="100%",
        class_name="chat-typing",
    )


def skeleton_loader() -> rx.Component:
    """Skeleton loader for chat messages."""
    return rx.hstack(
        rx.box(
            rx.vstack(
                # Title skeleton
                rx.box(
                    height="16px",
                    width="60%",
                    background="var(--gray-200)",
                    border_radius="4px",
                    margin_bottom="8px",
                ),
                # Content skeleton lines
                rx.box(
                    height="14px",
                    width="100%",
                    background="var(--gray-200)",
                    border_radius="4px",
                    margin_bottom="6px",
                ),
                rx.box(
                    height="14px",
                    width="80%",
                    background="var(--gray-200)",
                    border_radius="4px",
                ),
                spacing="1",
                width="100%",
            ),
            padding="0.75rem 1rem",
            border_radius="0.75rem",
            max_width="75%",
            **CHAT_MESSAGE_ASSISTANT_STYLE,
        ),
        justify="start",
        width="100%",
        animation="fadeIn 0.3s ease-in-out",
    )