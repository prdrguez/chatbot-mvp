import reflex as rx

from chatbot_mvp.components.layout import layout
from chatbot_mvp.state.auth_state import AuthState


def login_page() -> rx.Component:
    """Login page for admin access."""
    
    return layout(
        rx.center(
            rx.card(
                rx.vstack(
                    rx.heading("Acceso Administrador", size="7", margin_bottom="4"),
                    
                    # Login form
                    rx.form(
                        rx.vstack(
                            rx.text(
                                "Ingrese la contraseña para acceder al panel de administración:",
                                margin_bottom="4",
                                text_align="center"
                            ),
                            
                            # Password input
                            rx.input(
                                placeholder="Contraseña",
                                type="password",
                                value=AuthState.password_input,
                                on_change=AuthState.set_password,
                                margin_bottom="4",
                                width="100%",
                                size="3"
                            ),
                            
                            # Error message
                            rx.cond(
                                AuthState.auth_error != "",
                                rx.callout(
                                    AuthState.auth_error,
                                    icon="triangle_alert",
                                    color_scheme="red",
                                    margin_bottom="4",
                                    width="100%"
                                ),
                                rx.box()
                            ),
                            
                            # Login button
                            rx.button(
                                rx.cond(
                                    AuthState.loading,
                                    rx.spinner(size="2"),
                                    "Ingresar"
                                ),
                                type="submit",
                                on_click=AuthState.login,
                                loading=AuthState.loading,
                                disabled=AuthState.is_locked_out,
                                width="100%",
                                size="3"
                            ),
                            
                            # Lockout message
                            rx.cond(
                                AuthState.is_locked_out,
                                rx.callout(
                                    f"Cuenta bloqueada. Intenta en {AuthState.lockout_time_remaining}s",
                                    icon="lock",
                                    color_scheme="orange",
                                    margin_top="4",
                                    width="100%"
                                ),
                                rx.box()
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
                        "← Volver al inicio",
                        href="/",
                        margin_top="6",
                        text_decoration="underline",
                        color="blue"
                    ),
                    
                    spacing="4",
                    width="400px",
                    max_width="90vw",
                    align="center",
                    padding="6",
                ),
                width="100%",
                max_width="500px",
            ),
            padding="8",
            min_height="100vh",
        )
    )