import reflex as rx

from chatbot_mvp.components.layout import layout


def home() -> rx.Component:
    return layout(
        rx.vstack(
            rx.text(
                "La inteligencia artificial es una herramienta para amplificar lo mejor de las personas: ayuda a analizar información, automatizar tareas repetitivas y mejorar decisiones. Bien usada, puede aumentar productividad, reducir errores y liberar tiempo para lo creativo y lo importante: aprender, cuidar y construir soluciones más justas y eficientes.",
                color="var(--gray-300)",
                size="3",
                max_width="720px",
            ),
            spacing="4",
            align="start",
        ),
        active_route="/",
    )
