import reflex as rx
from typing import List, Dict, Callable


def quick_reply_button(text: str, on_click: Callable, disabled: bool = False) -> rx.Component:
    """Individual quick reply button."""
    return rx.button(
        text,
        on_click=on_click,
        disabled=disabled,
        variant="outline",
        
        background="white",
        border="1px solid var(--gray-300)",
        color="var(--gray-700)",
        box_shadow="var(--chat-shadow-sm)",
        transition="var(--chat-transition)",
        cursor=rx.cond(disabled, "not-allowed", "pointer"),
        opacity=rx.cond(disabled, 0.5, 1),
        _hover={
            "background": "var(--gray-50)",
            "border_color": "var(--blue-300)",
            "box_shadow": "var(--chat-shadow-md)",
            "transform": "translateY(-1px)",
        },
        _active={
            "transform": "translateY(0)",
        },
        margin_right="0.5rem",
        margin_bottom="0.5rem",
    )


def quick_replies_container(
    replies: List[str],
    on_reply: Callable[[str], None],
    disabled: bool = False,
) -> rx.Component:
    """Container for quick reply buttons."""
    return rx.cond(
        len(replies) > 0,
        rx.vstack(
            rx.text("Sugerencias:", font_size="0.875rem", color="var(--gray-600)", margin_bottom="0.5rem"),
            rx.hstack(
                rx.foreach(
                    replies,
                    lambda reply: quick_reply_button(
                        text=reply,
                        on_click=lambda r=reply: on_reply(r),
                        disabled=disabled,
                    ),
                ),
                spacing="1",
                flex_wrap="wrap",
                width="100%",
            ),
            spacing="1",
            width="100%",
            max_width="640px",
            padding="0.5rem 0",
            animation="fadeIn 0.3s ease-in-out",
        ),
    )


def contextual_quick_replies(
    last_message: str,
    on_reply: Callable[[str], None],
    disabled: bool = False,
) -> rx.Component:
    """Generate contextual quick replies based on last message."""
    
    # Default quick replies - always show these for simplicity
    default_replies = [
        "Contarme más",
        "¿Cómo funciona?",
        "Empezar ahora", 
        "Ver ejemplos"
    ]
    
    # For now, use simple default replies to avoid Var compatibility issues
    # TODO: Implement contextual replies with proper Var handling
    return quick_replies_container(
        replies=default_replies,
        on_reply=on_reply,
        disabled=disabled,
    )