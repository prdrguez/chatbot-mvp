import reflex as rx

from chatbot_mvp.config.settings import is_demo_mode, get_admin_password
from chatbot_mvp.state.theme_state import ThemeState
from chatbot_mvp.ui.tokens import CONTENT_BOX_STYLE, HEADER_BOX_STYLE


def layout(content: rx.Component) -> rx.Component:
    # Load theme on layout render
    ThemeState.load_theme()
    
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
                    get_admin_password(),  # Show admin link only if password is configured
                    rx.link("Admin", href="/admin"),
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

    return rx.vstack(
        header,
        rx.center(
            rx.box(
                content,
                **CONTENT_BOX_STYLE,
                width="100%",
                max_width="1200px",
            ),
            width="100%",
            flex="1",
        ),
        style=ThemeState.applied_theme,
        width="100%",
        min_height="100vh",
        spacing="0",
    )
    
