import reflex as rx

from chatbot_mvp.config.settings import is_demo_mode


def layout(content: rx.Component) -> rx.Component:
    header = rx.box(
        rx.hstack(
            rx.heading("Chatbot MVP", size="6"),
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

    banner = None
    if is_demo_mode():
        banner = rx.box(
            rx.text("MODO DEMO: respuestas simuladas (sin costos)."),
            width="100%",
            padding="0.5rem 2rem",
            background="var(--yellow-100)",
            border_bottom="1px solid var(--gray-200)",
        )

    return rx.box(
        banner,
        header,
        rx.box(content, padding="2rem"),
        width="100%",
    )
