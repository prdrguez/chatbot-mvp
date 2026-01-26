import reflex as rx

from chatbot_mvp.components.layout import layout
from chatbot_mvp.state.auth_state import AuthState


def login_page() -> rx.Component:
    """Login page for admin access."""
    
    return layout(
        rx.center(
            rx.card(
                rx.vstack(
                    rx.heading(
                        "Acceso Administrador",
                        size="7",
                        margin_bottom="4",
                        color="white",
                        font_weight="700",
                    ),
                    rx.text(
                        "Ingrese la contraseña para acceder al panel de administración:",
                        margin_bottom="4",
                        text_align="center",
                        color="rgba(226, 232, 240, 0.75)",
                    ),
                    # Login form
                    rx.form(
                        rx.vstack(
                            # Password input
                            rx.input(
                                placeholder="Contraseña",
                                type="password",
                                value=AuthState.password_input,
                                on_change=AuthState.set_password,
                                margin_bottom="4",
                                width="100%",
                                size="3",
                                style={
                                    "background": "rgba(2, 6, 23, 0.55)",
                                    "color": "white",
                                    "border": "1px solid rgba(148, 163, 184, 0.35)",
                                    "_placeholder": {"color": "rgba(226, 232, 240, 0.6)"},
                                },
                            ),
                            # Error message
                            rx.cond(
                                AuthState.auth_error != "",
                                rx.callout(
                                    AuthState.auth_error,
                                    icon="triangle_alert",
                                    color_scheme="red",
                                    margin_bottom="4",
                                    width="100%",
                                ),
                                rx.box(),
                            ),
                            # Login button
                            rx.button(
                                rx.cond(
                                    AuthState.loading,
                                    rx.spinner(size="2"),
                                    "Ingresar",
                                ),
                                type="submit",
                                on_click=AuthState.login,
                                loading=AuthState.loading,
                                disabled=AuthState.is_locked_out,
                                width="100%",
                                size="3",
                                color_scheme="teal",
                            ),
                            # Lockout message
                            rx.cond(
                                AuthState.is_locked_out,
                                rx.callout(
                                    f"Cuenta bloqueada. Intenta en {AuthState.lockout_time_remaining}s",
                                    icon="lock",
                                    color_scheme="orange",
                                    margin_top="4",
                                    width="100%",
                                ),
                                rx.box(),
                            ),
                            spacing="3",
                            width="100%",
                            align="center",
                        ),
                        on_submit=AuthState.login,
                        width="100%",
                    ),
                    # Back link
                    rx.link(
                        rx.button(
                            "← Volver al inicio",
                            variant="ghost",
                            color_scheme="gray",
                            size="1",
                            margin_top="4",
                        ),
                        href="/",
                        text_decoration="none",
                    ),
                    spacing="4",
                    width="100%",
                    align="center",
                ),
                width=["92vw", "520px"],
                background="rgba(15, 23, 42, 0.92)",
                border="1px solid rgba(148, 163, 184, 0.25)",
                box_shadow="0 12px 40px rgba(0, 0, 0, 0.45)",
                border_radius="16px",
                padding="32px",
            ),
            width="100%",
            height="100%",
        ),
        active_route="/login",
    )
