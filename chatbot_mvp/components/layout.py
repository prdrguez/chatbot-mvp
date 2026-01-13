import reflex as rx


def layout(content: rx.Component) -> rx.Component:
    header = rx.box(
        rx.hstack(
            rx.heading("Chatbot MVP", size="6"),
            rx.hstack(
                rx.link("Inicio", href="/"),
                rx.link("Evaluación", href="/evaluacion"),
                rx.link("Chat", href="/chat"),
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
