import reflex as rx

from chatbot_mvp.components.layout import layout
from chatbot_mvp.components.admin.admin_tabs import admin_tabs
from chatbot_mvp.components.admin.header import admin_header


def admin() -> rx.Component:
    """Admin page with authentication protection."""
    return layout(
        rx.vstack(
            admin_header(),
            admin_tabs(),
            spacing="4",
            align="start",
            width="100%",
        ),
        active_route="/admin",
    )
