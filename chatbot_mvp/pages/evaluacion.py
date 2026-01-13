import reflex as rx

from chatbot_mvp.components.layout import layout


def evaluacion() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Evaluación", size="8"),
            rx.text("Wizard de preguntas (MVP) - próximamente"),
            spacing="3",
            align="start",
        )
    )
