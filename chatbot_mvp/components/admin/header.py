import reflex as rx

from chatbot_mvp.state.admin_state import AdminState


def admin_header() -> rx.Component:
    confirm_panel = rx.card(
        rx.vstack(
            rx.text(
                "¿Seguro que querés borrar los datos locales? Esta acción no se puede deshacer.",
                size="2",
                color="var(--gray-700)",
            ),
            rx.hstack(
                rx.button(
                    "Cancelar",
                    on_click=AdminState.cancel_reset,
                    variant="soft",
                    size="2",
                ),
                rx.button(
                    "Confirmar Reset",
                    on_click=AdminState.reset_data,
                    color_scheme="red",
                    variant="solid",
                    size="2",
                ),
                spacing="2",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
        background="white",
        border="1px solid var(--gray-200)",
    )

    return rx.vstack(
        rx.hstack(
            rx.heading("Admin (Demo)", size="8"),
            rx.hstack(
                rx.button(
                    "Reset Local Data",
                    on_click=AdminState.request_reset,
                    color_scheme="red",
                    variant="soft",
                    size="2",
                ),
                rx.button(
                    "Cerrar Sesión",
                    on_click=AdminState.logout_admin,
                    variant="soft",
                    size="2",
                ),
                spacing="3",
            ),
            justify="between",
            align="center",
            width="100%",
        ),
        rx.cond(AdminState.reset_confirm_open, confirm_panel, rx.box()),
        rx.cond(
            AdminState.reset_message != "",
            rx.callout(
                AdminState.reset_message,
                icon="info",
                color_scheme="green",
                width="100%",
            ),
            rx.box(),
        ),
        rx.cond(
            AdminState.reset_error != "",
            rx.callout(
                AdminState.reset_error,
                icon="triangle_alert",
                color_scheme="red",
                width="100%",
            ),
            rx.box(),
        ),
        spacing="3",
        align="start",
        width="100%",
    )
