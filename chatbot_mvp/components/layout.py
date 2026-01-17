import reflex as rx

from chatbot_mvp.config.settings import is_demo_mode
from chatbot_mvp.state.theme_state import ThemeState
from chatbot_mvp.ui.tokens import CONTENT_BOX_STYLE, HEADER_BOX_STYLE


def layout(content: rx.Component) -> rx.Component:
    header = rx.box(
        rx.hstack(
            rx.hstack(
                rx.heading("Chatbot MVP", size="6"),
                rx.cond(
                    is_demo_mode(),
                    rx.hstack(
                        rx.badge("DEMO", variant="soft", color_scheme="yellow"),
                        rx.badge("sin costos", variant="soft", color_scheme="yellow"),
                        spacing="2",
                        align="center",
                    ),
                    rx.box(),
                ),
                spacing="3",
                align="center",
            ),
            rx.hstack(
                rx.link("Inicio", href="/"),
                rx.link("Evaluación", href="/evaluacion"),
                rx.link("Chat", href="/chat"),
                rx.cond(
                    is_demo_mode(),
                    rx.link("UI", href="/ui"),
                    rx.box(),
                ),
                rx.cond(
                    is_demo_mode(),
                    rx.link("Admin", href="/admin", opacity="0.7"),
                    rx.box(),
                ),
                spacing="4",
            ),
            justify="between",
            align="center",
            width="100%",
        ),
        **HEADER_BOX_STYLE,
    )

    return rx.box(
        header,
        rx.box(content, **CONTENT_BOX_STYLE),
        style=ThemeState.applied_overrides,
        width="100%",
    )
