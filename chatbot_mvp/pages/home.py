import reflex as rx

from chatbot_mvp.components.layout import layout


def home() -> rx.Component:
    return layout(
        rx.vstack(
            rx.text("Bienvenido/a al MVP", size="5"),
            rx.text(
                "La inteligencia artificial puede ayudarnos a tomar mejores decisiones, "
                "ampliar oportunidades y resolver desafíos complejos. Este espacio busca "
                "explorar su potencial con una mirada humana, ética y responsable.",
                color="var(--gray-300)",
                max_width="720px",
            ),
            spacing="4",
            align="start",
        ),
        active_route="/",
    )
