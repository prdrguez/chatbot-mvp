import reflex as rx

from chatbot_mvp.components.admin.app_settings_section import admin_app_settings_section
from chatbot_mvp.components.admin.export_section import admin_export_section
from chatbot_mvp.components.admin.kpis_section import admin_kpis_section
from chatbot_mvp.ui.simplified_theme_components import simplified_theme_editor


def admin_tabs() -> rx.Component:
    return rx.tabs.root(
        rx.tabs.list(
            rx.tabs.trigger("KPIs", value="kpis"),
            rx.tabs.trigger("Ajustes", value="settings"),
            rx.tabs.trigger("Theme", value="theme"),
            rx.tabs.trigger("Export/Reset", value="export"),
        ),
        rx.tabs.content(
            rx.box(admin_kpis_section(), padding_top="1rem"),
            value="kpis",
        ),
        rx.tabs.content(
            rx.box(admin_app_settings_section(), padding_top="1rem"),
            value="settings",
        ),
        rx.tabs.content(
            rx.box(simplified_theme_editor(), padding_top="1rem"),
            value="theme",
        ),
        rx.tabs.content(
            rx.box(admin_export_section(), padding_top="1rem"),
            value="export",
        ),
        default_value="kpis",
        width="100%",
    )
