import reflex as rx

from chatbot_mvp.components.admin import kpis
from chatbot_mvp.state.admin_state import AdminState


def admin_kpis_section() -> rx.Component:
    summary_card = rx.card(
        rx.hstack(
            rx.vstack(
                rx.heading("Resumen", size="4", color=kpis.ADMIN_TEXT_COLOR),
                rx.text("Total", size="2", color=kpis.ADMIN_TEXT_MUTED),
                rx.text(AdminState.total, size="6", font_weight="600", color=kpis.ADMIN_TEXT_COLOR),
                rx.text("Avg %", size="2", color=kpis.ADMIN_TEXT_MUTED),
                rx.text(
                    AdminState.avg_percent,
                    "%",
                    size="6",
                    font_weight="600",
                    color=kpis.ADMIN_TEXT_COLOR,
                ),
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
        **kpis.ADMIN_CARD_STYLE,
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
                rx.icon("database", size=48, color="rgba(226, 232, 240, 0.65)"),
                rx.text("Sin datos aún", size="4", color="rgba(226, 232, 240, 0.75)"),
                spacing="3",
            ),
            padding="4rem",
            width="100%",
        ),
    )
