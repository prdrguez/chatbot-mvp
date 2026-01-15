import reflex as rx

from chatbot_mvp.config.settings import is_demo_mode


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
                    rx.link("Admin", href="/admin", opacity="0.7"),
                    rx.box(),
                ),
                spacing="4",
            ),
            justify="between",
            align="center",
            width="100%",
        ),
        padding="1.25rem 2rem",
        border_bottom="1px solid var(--gray-200)",
    )

    return rx.box(
        header,
        rx.box(content, padding="2rem"),
        width="100%",
    )
