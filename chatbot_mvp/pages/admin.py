import reflex as rx

from chatbot_mvp.components.layout import layout
from chatbot_mvp.components.admin.app_settings_section import admin_app_settings_section
from chatbot_mvp.components.admin.export_section import admin_export_section
from chatbot_mvp.components.admin.header import admin_header
from chatbot_mvp.components.admin.kpis_section import admin_kpis_section
from chatbot_mvp.state.admin_state import AdminState
from chatbot_mvp.ui.simplified_theme_components import simplified_theme_editor

ADMIN_MENU_ITEM_STYLE = {
    "padding": "0.5rem 0.75rem",
    "border_radius": "0.6rem",
    "width": "100%",
    "justify_content": "start",
    "padding_left": "1.5rem",
}
ADMIN_MENU_ITEM_ACTIVE_STYLE = {
    "background": "rgba(20, 184, 166, 0.12)",
    "border": "1px solid rgba(45, 212, 191, 0.25)",
}
ADMIN_MENU_ITEM_HOVER_STYLE = {
    "background": "rgba(255, 255, 255, 0.06)",
}


def _admin_menu_item(label: str, value: str) -> rx.Component:
    is_active = AdminState.active_section == value
    return rx.button(
        label,
        variant="ghost",
        style=ADMIN_MENU_ITEM_STYLE,
        on_click=AdminState.set_active_section(value),
        background=rx.cond(
            is_active,
            ADMIN_MENU_ITEM_ACTIVE_STYLE["background"],
            "transparent",
        ),
        border=rx.cond(
            is_active,
            ADMIN_MENU_ITEM_ACTIVE_STYLE["border"],
            "1px solid transparent",
        ),
        _hover=ADMIN_MENU_ITEM_HOVER_STYLE,
    )


def _admin_sidebar_menu() -> rx.Component:
    return rx.vstack(
        rx.vstack(
            _admin_menu_item("KPIs", "kpis"),
            _admin_menu_item("Ajustes", "settings"),
            _admin_menu_item("Theme", "theme"),
            _admin_menu_item("Export/Reset", "export"),
            spacing="1",
            width="100%",
        ),
        spacing="2",
        width="100%",
        align="start",
    )


def _admin_content() -> rx.Component:
    export_section = rx.box(
        admin_export_section(),
        style={
            "--app-glass-bg": "rgba(17, 17, 17, 0.98)",
            "--app-glass-border": "1px solid rgba(255, 255, 255, 0.08)",
            "--app-glass-blur": "0px",
        },
    )
    return rx.cond(
        AdminState.active_section == "kpis",
        admin_kpis_section(),
        rx.cond(
            AdminState.active_section == "settings",
            admin_app_settings_section(),
            rx.cond(
                AdminState.active_section == "theme",
                simplified_theme_editor(),
                export_section,
            ),
        ),
    )


def admin() -> rx.Component:
    """Admin page with authentication protection."""
    return layout(
        rx.vstack(
            admin_header(),
            _admin_content(),
            spacing="4",
            align="start",
            width="100%",
        ),
        active_route="/admin",
        sidebar_extra=_admin_sidebar_menu(),
    )
