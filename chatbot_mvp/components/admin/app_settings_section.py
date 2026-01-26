import reflex as rx

from chatbot_mvp.state.admin_state import AdminState


def admin_app_settings_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("Ajustes", size="5", color="var(--gray-50)"),
            rx.vstack(
                rx.text("Proveedor de IA", size="2", weight="medium", color="var(--gray-300)"),
                rx.select.root(
                    rx.select.trigger(placeholder="Selecciona proveedor"),
                    rx.select.content(
                        rx.select.item("Gemini", value="gemini"),
                        rx.select.item("Groq", value="groq"),
                    ),
                    value=AdminState.selected_ai_provider,
                    on_change=AdminState.set_selected_ai_provider,
                    size="2",
                ),
                spacing="2",
                align="start",
                width="100%",
            ),
            rx.hstack(
                rx.button("Guardar", on_click=AdminState.save_ai_provider, variant="solid", size="2"),
                rx.text(
                    "Activo: ",
                    rx.text.strong(AdminState.active_ai_provider),
                    size="2",
                    color="var(--gray-300)",
                ),
                spacing="3",
                align="center",
            ),
            rx.vstack(
                rx.cond(
                    AdminState.provider_message != "",
                    rx.callout(
                        AdminState.provider_message,
                        icon="info",
                        color_scheme="green",
                        width="100%",
                    ),
                ),
                rx.cond(
                    AdminState.provider_error != "",
                    rx.callout(
                        AdminState.provider_error,
                        icon="triangle_alert",
                        color_scheme="red",
                        width="100%",
                    ),
                ),
                rx.cond(
                    AdminState.groq_key_missing,
                    rx.callout(
                        "Falta GROQ_API_KEY para usar Groq.",
                        icon="triangle_alert",
                        color_scheme="orange",
                        width="100%",
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            spacing="4",
            align="start",
            width="100%",
        ),
        width="100%",
        background="rgba(17, 17, 17, 0.98)",
        border="1px solid rgba(255, 255, 255, 0.08)",
    )
