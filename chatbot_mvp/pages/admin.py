from typing import Any

import reflex as rx

from chatbot_mvp.components.layout import layout
from chatbot_mvp.state.admin_state import AdminState
from chatbot_mvp.state.theme_state import ThemeState
from chatbot_mvp.state.simplified_theme_state import SimplifiedThemeState
from chatbot_mvp.state.auth_state import AuthState
from chatbot_mvp.ui.simplified_theme_components import simplified_theme_editor

from chatbot_mvp.components.admin import kpis
from chatbot_mvp.components.admin.export_section import admin_export_section

def _admin_kpis_section() -> rx.Component:
    summary_card = rx.card(
        rx.hstack(
            rx.vstack(
                rx.heading("Resumen", size="4"),
                rx.text("Total", size="2", color="var(--gray-600)"),
                rx.text(AdminState.total, size="6", font_weight="600"),
                rx.text("Avg %", size="2", color="var(--gray-600)"),
                rx.text(AdminState.avg_percent, "%", size="6", font_weight="600"),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.box(kpis.avg_gauge(), width="100%", max_width="320px"),
            spacing="4",
            align="center",
            justify="between",
            width="100%",
            wrap="wrap",
        ),
        width="100%",
        height="100%",
        min_height="20rem",
        background="var(--app-glass-bg)",
        backdrop_filter="var(--app-glass-blur)",
        border="var(--app-glass-border)",
    )

    cards = [
        summary_card,
        kpis.kpi_card(
            "By Level",
            AdminState.by_level_top_items,
            AdminState.by_level_extra_count,
            chart_data=AdminState.by_level_chart,
        ),
        kpis.kpi_card(
            "Edad",
            AdminState.edad_top_items,
            AdminState.edad_extra_count,
            chart_data=AdminState.edad_chart,
        ),
        kpis.kpi_card(
            "Genero",
            AdminState.genero_top_items,
            AdminState.genero_extra_count,
            chart_data=AdminState.genero_chart,
        ),
        kpis.kpi_card(
            "Ciudad",
            AdminState.ciudad_chart_items,
            0,
            chart_data=AdminState.ciudad_chart,
        ),
        kpis.kpi_card(
            "Frecuencia IA",
            AdminState.frecuencia_ia_top_items,
            AdminState.frecuencia_ia_extra_count,
            chart_data=AdminState.frecuencia_ia_chart,
        ),
        kpis.kpi_card(
            "Nivel Educativo",
            AdminState.nivel_educativo_top_items,
            AdminState.nivel_educativo_extra_count,
            chart_data=AdminState.nivel_educativo_chart,
        ),
        kpis.kpi_card(
            "Ocupacion",
            AdminState.ocupacion_top_items,
            AdminState.ocupacion_extra_count,
            chart_data=AdminState.ocupacion_chart,
        ),
        kpis.kpi_card(
            "Area",
            AdminState.area_top_items,
            AdminState.area_extra_count,
            chart_data=AdminState.area_chart,
        ),
        kpis.kpi_card(
            "Emociones",
            AdminState.emociones_top_items,
            AdminState.emociones_extra_count,
            chart_data=AdminState.emociones_chart,
        ),
    ]

    return rx.cond(
        AdminState.has_data,
        rx.grid(
            *cards,
            columns=rx.breakpoints(initial="1", md="2"),
            spacing="6",
            width="100%",
            align="stretch",
            style={"grid_auto_rows": "1fr"},
        ),
        rx.center(
            rx.vstack(
                rx.icon("database", size=48, color="var(--gray-300)"),
                rx.text("Sin datos aún", size="4", color="var(--gray-600)"),
                spacing="3",
            ),
            padding="4rem",
            width="100%",
        ),
    )

def _admin_tabs() -> rx.Component:
    return rx.tabs.root(
        rx.tabs.list(
            rx.tabs.trigger("KPIs", value="kpis"),
            rx.tabs.trigger("Theme", value="theme"),
            rx.tabs.trigger("Export/Reset", value="export"),
        ),
        rx.tabs.content(
            rx.box(_admin_kpis_section(), padding_top="1rem"),
            value="kpis"
        ),
        rx.tabs.content(
             rx.box(simplified_theme_editor(), padding_top="1rem"),
             value="theme"
        ),
        rx.tabs.content(
            rx.box(admin_export_section(), padding_top="1rem"),
            value="export"
        ),
        default_value="kpis",
        width="100%",
    )


def admin() -> rx.Component:
    """Admin page with authentication protection."""
    return layout(
        rx.vstack(
            rx.hstack(
                rx.heading("Admin (Demo)", size="8"),
                rx.hstack(
                    rx.button(
                        "Reiniciar Datos",
                        on_click=AdminState.reset_data,
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
            _admin_tabs(),
            spacing="4",
            align="start",
            width="100%",
        ),
    )
