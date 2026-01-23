import reflex as rx
from chatbot_mvp.state.admin_state import AdminState

def admin_export_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.button(
                    "Refrescar Datos",
                    on_click=AdminState.load_summary,
                    is_loading=AdminState.loading,
                    variant="soft",
                ),
                rx.button("Exportar JSON", on_click=AdminState.do_export_json, variant="outline"),
                rx.button("Exportar CSV", on_click=AdminState.do_export_csv, variant="outline"),
                spacing="3",
                align="center",
            ),
            rx.vstack(
                rx.cond(
                    AdminState.export_message != "",
                    rx.callout(AdminState.export_message, icon="info", color_scheme="green", width="100%"),
                ),
                rx.cond(
                    AdminState.export_error != "",
                    rx.callout(AdminState.export_error, icon="triangle_alert", color_scheme="red", width="100%"),
                ),
                rx.cond(
                    AdminState.error != "",
                    rx.callout(AdminState.error, icon="circle_alert", color_scheme="red", width="100%"),
                ),
                spacing="2",
                width="100%",
            ),
            spacing="4",
            align="start",
            width="100%",
        ),
        width="100%",
        background="var(--app-glass-bg)",
        backdrop_filter="var(--app-glass-blur)",
        border="var(--app-glass-border)",
    )
