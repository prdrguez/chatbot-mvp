from typing import Any

import reflex as rx

from chatbot_mvp.components.layout import layout
from chatbot_mvp.state.admin_state import AdminState
from chatbot_mvp.state.theme_state import ThemeState

ADMIN_CHART_FILL = "var(--teal-9)"
ADMIN_AXIS_STROKE = "var(--gray-8)"
ADMIN_TEXT_COLOR = "var(--gray-11)"
ADMIN_LIST_MAX_HEIGHT = "10rem"
ADMIN_ROW_TEXT_SIZE = "2"
ADMIN_GAUGE_TRACK = "var(--gray-4)"

_THEME_FIELDS: list[tuple[str, str, str]] = [
    ("Header padding", "--app-header-padding", "1.25rem 2rem"),
    ("Content padding", "--app-content-padding", "2rem"),
    ("Radius md", "--app-radius-md", "0.5rem"),
    ("Card border", "--app-card-border", "1px solid var(--gray-300)"),
    ("Text danger", "--app-text-danger", "red"),
    ("Chat radius", "--chat-radius", "0.75rem"),
    ("Chat card border", "--chat-card-border", "1px solid var(--gray-200)"),
]


def _count_row(item: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        rx.text(item["label"], size=ADMIN_ROW_TEXT_SIZE, color=ADMIN_TEXT_COLOR),
        rx.text(item["count"], size=ADMIN_ROW_TEXT_SIZE, color=ADMIN_TEXT_COLOR),
        spacing="2",
        align="center",
        width="100%",
        justify="between",
    )


def _count_list(items: list[dict[str, Any]]) -> rx.Component:
    return rx.cond(
        items,
        rx.vstack(
            rx.foreach(items, _count_row),
            spacing="1",
            align="start",
            width="100%",
            max_height=ADMIN_LIST_MAX_HEIGHT,
            overflow_y="auto",
        ),
        rx.text("Sin datos"),
    )


def _mini_bar_row(item: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        rx.text(
            item["label"],
            width="40%",
            white_space="nowrap",
            overflow="hidden",
            text_overflow="ellipsis",
        ),
        rx.progress(value=item["count"], max=AdminState.total, width="45%"),
        rx.text(item["count"], width="15%", text_align="right"),
        spacing="2",
        align="center",
        width="100%",
    )


def _mini_chart(
    items: list[dict[str, Any]], chart_data: list[dict[str, Any]]
) -> rx.Component:
    recharts = getattr(rx, "recharts", None)
    if recharts is not None and hasattr(recharts, "bar_chart"):
        return recharts.bar_chart(
            recharts.bar(data_key="value", fill=ADMIN_CHART_FILL),
            recharts.x_axis(
                data_key="name",
                tick_line=False,
                axis_line=False,
                stroke=ADMIN_AXIS_STROKE,
                tick=False,
            ),
            recharts.y_axis(
                tick_line=False,
                axis_line=False,
                stroke=ADMIN_AXIS_STROKE,
                tick=False,
            ),
            data=chart_data,
            height=120,
            width="100%",
        )
    return rx.vstack(
        rx.foreach(items, _mini_bar_row),
        spacing="1",
        align="start",
        width="100%",
    )


def _kpi_card(
    title: str,
    items: list[dict[str, Any]],
    chart_data: list[dict[str, Any]],
    extra_count: int,
    chart_component: rx.Component | None = None,
) -> rx.Component:
    chart = chart_component if chart_component is not None else _mini_chart(items, chart_data)
    return rx.card(
        rx.vstack(
            rx.heading(title, size="4"),
            rx.cond(
                items,
                chart,
                rx.text("Sin datos"),
            ),
            _count_list(items),
            rx.cond(
                extra_count > 0,
                rx.text("+", extra_count, " mas", size="2", color="var(--gray-600)"),
                rx.box(),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def _city_chart(
    items: list[dict[str, Any]], chart_data: list[dict[str, Any]]
) -> rx.Component:
    recharts = getattr(rx, "recharts", None)
    if recharts is not None and hasattr(recharts, "pie_chart"):
        return recharts.pie_chart(
            recharts.pie(
                data=chart_data,
                data_key="value",
                name_key="name",
                fill=ADMIN_CHART_FILL,
                inner_radius="45%",
                outer_radius="70%",
            ),
            height=160,
            width="100%",
        )
    return _mini_chart(items, chart_data)


def _avg_gauge() -> rx.Component:
    recharts = getattr(rx, "recharts", None)
    if recharts is not None and hasattr(recharts, "pie_chart"):
        return rx.box(
            recharts.pie_chart(
                recharts.pie(
                    data=[
                        {"name": "value", "value": AdminState.avg_percent_value},
                        {
                            "name": "rest",
                            "value": 100 - AdminState.avg_percent_value,
                        },
                    ],
                    data_key="value",
                    name_key="name",
                    start_angle=180,
                    end_angle=0,
                    inner_radius="65%",
                    outer_radius="90%",
                    fill=AdminState.avg_level_color,
                    stroke="none",
                ),
                height=160,
                width="100%",
            ),
            rx.box(
                rx.text(
                    AdminState.avg_percent_value,
                    "%",
                    size="6",
                    font_weight="700",
                    color=ADMIN_TEXT_COLOR,
                ),
                rx.badge(
                    AdminState.avg_level_label,
                    variant="soft",
                    color_scheme="gray",
                    style={"color": AdminState.avg_level_color},
                ),
                position="absolute",
                inset="0",
                display="flex",
                flex_direction="column",
                align_items="center",
                justify_content="center",
                gap="0.35rem",
            ),
            position="relative",
            width="100%",
        )
    progress = getattr(rx, "progress", None)
    if progress is None:
        return rx.text("Gauge no disponible", color="var(--gray-600)")
    return rx.vstack(
        rx.progress(
            value=AdminState.avg_percent_value,
            max=100,
            width="100%",
            color_scheme="gray",
        ),
        rx.hstack(
            rx.text(
                AdminState.avg_percent_value,
                "%",
                size="5",
                font_weight="700",
                color=ADMIN_TEXT_COLOR,
            ),
            rx.badge(
                AdminState.avg_level_label,
                variant="soft",
                style={"color": AdminState.avg_level_color},
            ),
            spacing="2",
            align="center",
        ),
        spacing="2",
        align="start",
        width="100%",
    )

def _theme_field(label: str, var_name: str, placeholder: str) -> rx.Component:
    return rx.vstack(
        rx.text(label, font_weight="600"),
        rx.input(
            value=ThemeState.overrides[var_name],
            placeholder=placeholder,
            on_change=ThemeState.set_var(var_name),
            width="100%",
        ),
        rx.text(placeholder, size="1", color="var(--gray-600)"),
        spacing="1",
        align="start",
        width="100%",
    )


def _theme_preview_card() -> rx.Component:
    return rx.box(
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.heading("Preview", size="5"),
                    rx.badge("Live", variant="soft"),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    "Asi se veria una card con tus estilos actuales.",
                    color="var(--gray-600)",
                ),
                rx.hstack(
                    rx.button("Primario", variant="solid"),
                    rx.button("Secundario", variant="outline"),
                    spacing="2",
                    align="center",
                ),
                rx.input(placeholder="Input de ejemplo"),
                rx.box(
                    rx.text("Chat bubble de ejemplo", size="2"),
                    border="var(--chat-card-border)",
                    padding="var(--chat-surface-padding)",
                    border_radius="var(--chat-radius)",
                    width="100%",
                ),
                rx.hstack(
                    rx.box(
                        rx.text("Card Border", size="1"),
                        border="var(--app-card-border)",
                        padding="0.5rem",
                        border_radius="var(--app-radius-md)",
                    ),
                    rx.box(
                        rx.text("Danger Text", size="1", color="var(--app-text-danger)"),
                        border="1px dashed var(--app-text-danger)",
                        padding="0.5rem",
                        border_radius="var(--app-radius-md)",
                    ),
                    rx.box(
                        rx.text("Danger Fill", size="1", color="white"),
                        background_color="var(--app-text-danger)",
                        padding="0.5rem",
                        border_radius="var(--app-radius-md)",
                    ),
                    rx.box(
                        rx.text("Chat Border", size="1"),
                        border="var(--chat-card-border)",
                        padding="0.5rem",
                        border_radius="var(--chat-radius)",
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            width="100%",
        ),
        style=ThemeState.applied_overrides,
        width="100%",
    )


def _preset_selector(var_name: str, options: list[str]) -> rx.Component:
    select = getattr(rx, "select", None)
    if select is not None:
        return select(
            options,
            value=ThemeState.overrides[var_name],
            on_change=ThemeState.set_var(var_name),
            width="100%",
        )
    return rx.radio_group(
        items=options,
        value=ThemeState.overrides[var_name],
        on_change=ThemeState.set_var(var_name),
        direction="column",
        spacing="2",
        width="100%",
    )


def _preset_field(label: str, var_name: str, options: list[str]) -> rx.Component:
    return rx.vstack(
        rx.text(label, font_weight="600"),
        _preset_selector(var_name, options),
        rx.input(
            value=ThemeState.overrides[var_name],
            placeholder="Custom",
            on_change=ThemeState.set_var(var_name),
            width="100%",
        ),
        spacing="2",
        align="start",
        width="100%",
    )


def _section_block(title: str, body: rx.Component) -> rx.Component:
    accordion = getattr(rx, "accordion", None)
    if (
        accordion is not None
        and hasattr(accordion, "root")
        and hasattr(accordion, "item")
        and hasattr(accordion, "trigger")
        and hasattr(accordion, "content")
    ):
        return accordion.root(
            accordion.item(
                accordion.trigger(title),
                accordion.content(body),
                value=title,
            ),
            type="multiple",
            collapsible=True,
            default_value=[title],
            width="100%",
        )
    return rx.card(
        rx.vstack(
            rx.heading(title, size="4"),
            body,
            spacing="2",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def _theme_group(label: str, fields: list[tuple[str, str, str]]) -> rx.Component:
    return _section_block(
        label,
        rx.vstack(
            *[
                _theme_field(field_label, var_name, placeholder)
                for field_label, var_name, placeholder in fields
            ],
            spacing="3",
            align="start",
            width="100%",
        ),
    )


class AdminViewState(rx.State):
    section: str = "kpis"

    def set_section(self, section: str) -> None:
        self.section = section


def _admin_theme_section() -> rx.Component:
    spacing_fields = [
        ("Header padding", "--app-header-padding", "Ej: 1.25rem 2rem"),
        ("Content padding", "--app-content-padding", "Ej: 2rem"),
    ]
    radius_fields = [
        ("Radius md", "--app-radius-md", "Ej: 0.5rem"),
        ("Chat radius", "--chat-radius", "Ej: 0.75rem"),
    ]
    border_fields = [
        ("Card border", "--app-card-border", "Ej: 1px solid var(--gray-300)"),
        ("Chat card border", "--chat-card-border", "Ej: 1px solid var(--gray-200)"),
    ]
    color_fields = [
        ("Text danger", "--app-text-danger", "Ej: red"),
    ]
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Theme Editor (MVP)", size="6"),
                rx.cond(
                    ThemeState.saved,
                    rx.badge("Guardado", variant="soft", color_scheme="green"),
                    rx.box(),
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.text(
                'Ejemplos: padding "1rem 2rem", border '
                '"1px solid var(--gray-200)", radius "0.75rem", '
                'color "red".',
                color="var(--gray-600)",
            ),
            rx.cond(
                ThemeState.error != "",
                rx.text(ThemeState.error, color="var(--app-text-danger)"),
                rx.box(),
            ),
            _theme_preview_card(),
            rx.vstack(
                rx.heading("Presets rapidos", size="4"),
                _preset_field(
                    "Radius (app)",
                    "--app-radius-md",
                    ["0.25rem", "0.5rem", "0.75rem", "1rem"],
                ),
                _preset_field(
                    "Padding (content)",
                    "--app-content-padding",
                    ["1rem", "1.5rem", "2rem", "2.5rem 3rem"],
                ),
                _preset_field(
                    "Border (card)",
                    "--app-card-border",
                    [
                        "1px solid var(--gray-200)",
                        "1px solid var(--gray-300)",
                        "1px solid var(--gray-400)",
                    ],
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            rx.heading("Controles", size="4"),
            _theme_group("Spacing", spacing_fields),
            _theme_group("Radius", radius_fields),
            _theme_group("Borders", border_fields),
            _theme_group("Colors", color_fields),
            rx.card(
                rx.vstack(
                    rx.heading("Avanzado", size="4"),
                    *[
                        _theme_field(label, var_name, placeholder)
                        for (label, var_name, placeholder) in _THEME_FIELDS
                    ],
                    spacing="3",
                    align="start",
                    width="100%",
                ),
                width="100%",
            ),
            rx.button(
                "Reset",
                on_click=ThemeState.reset_overrides,
                variant="outline",
            ),
            spacing="4",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def _admin_export_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.button(
                    "Refrescar",
                    on_click=AdminState.load_summary,
                    is_loading=AdminState.loading,
                ),
                rx.button("Export JSON", on_click=AdminState.do_export_json),
                rx.button("Export CSV", on_click=AdminState.do_export_csv),
                rx.cond(
                    AdminState.error != "",
                    rx.text(AdminState.error, color="red"),
                    rx.box(),
                ),
                spacing="3",
                align="center",
            ),
            rx.cond(
                AdminState.export_message != "",
                rx.text(AdminState.export_message, color="green"),
                rx.box(),
            ),
            rx.cond(
                AdminState.export_error != "",
                rx.text(AdminState.export_error, color="red"),
                rx.box(),
            ),
            spacing="4",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def _admin_kpis_section() -> rx.Component:
    grid = getattr(rx, "simple_grid", None) or getattr(rx, "grid", None)
    return rx.cond(
        AdminState.has_data,
        (
            grid(
                *[
                    rx.card(
                        rx.vstack(
                            rx.heading("Resumen", size="4"),
                            _avg_gauge(),
                            rx.text("Total", size="2", color="var(--gray-600)"),
                            rx.text(AdminState.total, size="6", font_weight="600"),
                            rx.text("Avg %", size="2", color="var(--gray-600)"),
                            rx.text(
                                AdminState.avg_percent, "%", size="6", font_weight="600"
                            ),
                            spacing="1",
                            align="start",
                            width="100%",
                        ),
                        width="100%",
                    ),
                    _kpi_card(
                        "By Level",
                        AdminState.by_level_top_items,
                        AdminState.by_level_chart,
                        AdminState.by_level_extra_count,
                    ),
                    _kpi_card(
                        "Edad",
                        AdminState.edad_top_items,
                        AdminState.edad_chart,
                        AdminState.edad_extra_count,
                    ),
                    _kpi_card(
                        "Genero",
                        AdminState.genero_top_items,
                        AdminState.genero_chart,
                        AdminState.genero_extra_count,
                    ),
                    _kpi_card(
                        "Ciudad",
                        AdminState.ciudad_chart_items,
                        AdminState.ciudad_chart,
                        AdminState.ciudad_extra_count,
                        chart_component=_city_chart(
                            AdminState.ciudad_chart_items,
                            AdminState.ciudad_chart,
                        ),
                    ),
                    _kpi_card(
                        "Frecuencia IA",
                        AdminState.frecuencia_ia_top_items,
                        AdminState.frecuencia_ia_chart,
                        AdminState.frecuencia_ia_extra_count,
                    ),
                    _kpi_card(
                        "Nivel Educativo",
                        AdminState.nivel_educativo_top_items,
                        AdminState.nivel_educativo_chart,
                        AdminState.nivel_educativo_extra_count,
                    ),
                    _kpi_card(
                        "Ocupacion",
                        AdminState.ocupacion_top_items,
                        AdminState.ocupacion_chart,
                        AdminState.ocupacion_extra_count,
                    ),
                    _kpi_card(
                        "Area",
                        AdminState.area_top_items,
                        AdminState.area_chart,
                        AdminState.area_extra_count,
                    ),
                    _kpi_card(
                        "Emociones",
                        AdminState.emociones_top_items,
                        AdminState.emociones_chart,
                        AdminState.emociones_extra_count,
                    ),
                ],
                columns=(
                    rx.breakpoints(initial="1", sm="2")
                    if hasattr(rx, "breakpoints")
                    else "2"
                ),
                gap="3",
                width="100%",
            )
            if grid is not None
            else rx.vstack(
                *[
                    rx.card(
                        rx.vstack(
                            rx.heading("Resumen", size="4"),
                            _avg_gauge(),
                            rx.text("Total", size="2", color="var(--gray-600)"),
                            rx.text(AdminState.total, size="6", font_weight="600"),
                            rx.text("Avg %", size="2", color="var(--gray-600)"),
                            rx.text(
                                AdminState.avg_percent, "%", size="6", font_weight="600"
                            ),
                            spacing="1",
                            align="start",
                            width="100%",
                        ),
                        width="100%",
                    ),
                    _kpi_card(
                        "By Level",
                        AdminState.by_level_top_items,
                        AdminState.by_level_chart,
                        AdminState.by_level_extra_count,
                    ),
                    _kpi_card(
                        "Edad",
                        AdminState.edad_top_items,
                        AdminState.edad_chart,
                        AdminState.edad_extra_count,
                    ),
                    _kpi_card(
                        "Genero",
                        AdminState.genero_top_items,
                        AdminState.genero_chart,
                        AdminState.genero_extra_count,
                    ),
                    _kpi_card(
                        "Ciudad",
                        AdminState.ciudad_chart_items,
                        AdminState.ciudad_chart,
                        AdminState.ciudad_extra_count,
                        chart_component=_city_chart(
                            AdminState.ciudad_chart_items,
                            AdminState.ciudad_chart,
                        ),
                    ),
                    _kpi_card(
                        "Frecuencia IA",
                        AdminState.frecuencia_ia_top_items,
                        AdminState.frecuencia_ia_chart,
                        AdminState.frecuencia_ia_extra_count,
                    ),
                    _kpi_card(
                        "Nivel Educativo",
                        AdminState.nivel_educativo_top_items,
                        AdminState.nivel_educativo_chart,
                        AdminState.nivel_educativo_extra_count,
                    ),
                    _kpi_card(
                        "Ocupacion",
                        AdminState.ocupacion_top_items,
                        AdminState.ocupacion_chart,
                        AdminState.ocupacion_extra_count,
                    ),
                    _kpi_card(
                        "Area",
                        AdminState.area_top_items,
                        AdminState.area_chart,
                        AdminState.area_extra_count,
                    ),
                    _kpi_card(
                        "Emociones",
                        AdminState.emociones_top_items,
                        AdminState.emociones_chart,
                        AdminState.emociones_extra_count,
                    ),
                ],
                spacing="3",
                align="start",
                width="100%",
            )
        ),
        rx.text("Sin datos aún"),
    )


def _admin_tabs() -> rx.Component:
    tabs = getattr(rx, "tabs", None)
    if tabs is not None and hasattr(tabs, "root"):
        return tabs.root(
            tabs.list(
                tabs.trigger("KPIs", value="kpis"),
                tabs.trigger("Theme", value="theme"),
                tabs.trigger("Export", value="export"),
            ),
            tabs.content(_admin_kpis_section(), value="kpis"),
            tabs.content(_admin_theme_section(), value="theme"),
            tabs.content(_admin_export_section(), value="export"),
            default_value="kpis",
            width="100%",
        )
    return rx.vstack(
        rx.hstack(
            rx.button("KPIs", on_click=AdminViewState.set_section("kpis")),
            rx.button("Theme", on_click=AdminViewState.set_section("theme")),
            rx.button("Export", on_click=AdminViewState.set_section("export")),
            spacing="2",
            align="center",
        ),
        rx.cond(
            AdminViewState.section == "kpis",
            _admin_kpis_section(),
            rx.cond(
                AdminViewState.section == "theme",
                _admin_theme_section(),
                _admin_export_section(),
            ),
        ),
        spacing="3",
        align="start",
        width="100%",
    )


def admin() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Admin (Demo)", size="8"),
            _admin_tabs(),
            spacing="4",
            align="start",
            width="100%",
        )
    )
