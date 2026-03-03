import reflex as rx

from chatbot_mvp.components.admin.app_settings_section import admin_app_settings_section
from chatbot_mvp.components.admin.export_section import admin_export_section
from chatbot_mvp.components.admin.kpis_section import admin_kpis_section
from chatbot_mvp.ui.simplified_theme_components import simplified_theme_editor


def admin_tabs() -> rx.Component:
    return rx.tabs.root(
        rx.hstack(
            rx.tabs.list(
                rx.tabs.trigger("KPIs", value="kpis", height="2.5rem", padding="0 1rem", width="100%"),
                rx.tabs.trigger("Ajustes", value="settings", height="2.5rem", padding="0 1rem", width="100%"),
                rx.tabs.trigger("Theme", value="theme", height="2.5rem", padding="0 1rem", width="100%"),
                rx.tabs.trigger("Export/Reset", value="export", height="2.5rem", padding="0 1rem", width="100%"),
                width="220px",
                min_width="220px",
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "alignItems": "stretch",
                    "gap": "0.5rem",
                    "padding": "0.25rem",
                },
            ),
            rx.box(
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
                    rx.box(
                        admin_export_section(),
                        padding_top="1rem",
                        style={
                            "--app-glass-bg": "rgba(17, 17, 17, 0.98)",
                            "--app-glass-border": "1px solid rgba(255, 255, 255, 0.08)",
                            "--app-glass-blur": "0px",
                        },
                    ),
                    value="export",
                ),
                flex="1",
                min_width="0",
            ),
            align="start",
            spacing="4",
            width="100%",
        ),
        default_value="kpis",
        width="100%",
    )
