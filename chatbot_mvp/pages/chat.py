import reflex as rx

from chatbot_mvp.components.layout import layout


def chat() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Chat", size="8"),
            rx.text("Chat natural (MVP) - próximamente"),
            spacing="3",
            align="start",
        )
    )
