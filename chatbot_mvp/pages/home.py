import reflex as rx

from chatbot_mvp.components.layout import layout


def home() -> rx.Component:
    return layout(
        rx.vstack(
            rx.text("Bienvenido/a al MVP", size="5"),
            rx.hstack(
                rx.link(rx.button("Ir a Evaluación"), href="/evaluacion"),
                rx.link(rx.button("Ir a Chat"), href="/chat"),
                spacing="4",
            ),
            spacing="4",
            align="start",
        )
    )
