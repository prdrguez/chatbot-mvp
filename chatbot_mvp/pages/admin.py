from typing import Any

import reflex as rx

from chatbot_mvp.components.layout import layout
from chatbot_mvp.state.admin_state import AdminState
from chatbot_mvp.state.theme_state import ThemeState

ADMIN_CHART_FILL = "var(--teal-9)"
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


def _mini_bar_row(item: dict[str, Any]) -> rx.Component:
    return rx.hstack(
        rx.text(
            item["label"],
            width="40%",
            white_space="nowrap",
            overflow="hidden",
            text_overflow="ellipsis",
            size=ADMIN_ROW_TEXT_SIZE,
            color=ADMIN_TEXT_COLOR,
        ),
        rx.progress(
            value=item["count"],
            max=AdminState.total,
            width="45%",
            color_scheme="teal",
        ),
        rx.text(
            item["count"],
            width="15%",
            text_align="right",
            size=ADMIN_ROW_TEXT_SIZE,
            color=ADMIN_TEXT_COLOR,
        ),
        spacing="2",
        align="center",
        width="100%",
    )


def _mini_chart(items: list[dict[str, Any]], extra_count: int) -> rx.Component:
    return rx.vstack(
        rx.foreach(items, _mini_bar_row),
        rx.cond(
            extra_count > 0,
            rx.text(
                "+",
                extra_count,
                " mas",
                size=ADMIN_ROW_TEXT_SIZE,
                color=ADMIN_TEXT_COLOR,
            ),
            rx.box(),
        ),
        spacing="1",
        align="start",
        width="100%",
        max_height=ADMIN_LIST_MAX_HEIGHT,
        overflow_y="auto",
    )


def _kpi_card(
    title: str,
    items: list[dict[str, Any]],
    extra_count: int,
    chart_data: list[dict[str, Any]] | None = None,
) -> rx.Component:
    recharts = getattr(rx, "recharts", None)
    if recharts is not None and hasattr(recharts, "bar_chart"):
        label_list = getattr(recharts, "label_list", None)
        tooltip = getattr(recharts, "tooltip", None)
        bar_children = []
        if label_list is not None:
            bar_children.append(label_list(data_key="value", position="right"))
        bar = recharts.bar(
            *bar_children,
            data_key="value",
            fill=ADMIN_CHART_FILL,
            radius=4,
        )
        chart_children = [
            recharts.cartesian_grid(stroke="var(--gray-6)", stroke_dasharray="3 3"),
            recharts.x_axis(type_="number", hide=True),
            recharts.y_axis(
                data_key="name",
                type_="category",
                width=110,
                stroke="var(--gray-6)",
            ),
            bar,
        ]
        if tooltip is not None:
            chart_children.append(tooltip())
        return rx.card(
            rx.vstack(
                rx.heading(title, size="4"),
                rx.cond(
                    items,
                    recharts.bar_chart(
                        *chart_children,
                        data=chart_data,
                        layout="vertical",
                        height=180,
                        width="100%",
                    ),
                    rx.text("Sin datos"),
                ),
                rx.cond(
                    extra_count > 0,
                    rx.text(
                        "+",
                        extra_count,
                        " mas",
                        size=ADMIN_ROW_TEXT_SIZE,
                        color=ADMIN_TEXT_COLOR,
                    ),
                    rx.box(),
                ),
                spacing="2",
                align="start",
                width="100%",
            ),
            width="100%",
        )
    return rx.card(
        rx.vstack(
            rx.heading(title, size="4"),
            rx.cond(
                items,
                _mini_chart(items, extra_count),
                rx.text("Sin datos"),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def _avg_gauge() -> rx.Component:
    svg = getattr(rx, "svg", None)
    path = getattr(rx, "path", None)
    if svg is not None and path is not None:
        return rx.box(
            svg(
                path(
                    d="M 30 100 A 70 70 0 0 0 170 100",
                    fill="none",
                    stroke="var(--gray-6)",
                    stroke_width=6,
                    stroke_linecap="round",
                    stroke_dasharray=AdminState.gauge_track_dasharray,
                ),
                path(
                    d="M 30 100 A 70 70 0 0 0 170 100",
                    fill="none",
                    stroke=AdminState.avg_level_color,
                    stroke_width=10,
                    stroke_linecap="round",
                    stroke_dasharray=AdminState.gauge_progress_dasharray,
                ),
                view_box="0 0 200 140",
                width="100%",
                height="160px",
            ),
            rx.box(
                rx.text(
                    AdminState.avg_percent_display,
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
    return rx.vstack(
        rx.box(
            rx.box(
                height="0.5rem",
                width=AdminState.avg_percent_width,
                background_color=AdminState.avg_level_color,
                border_radius="999px",
            ),
            height="0.5rem",
            width="100%",
            background_color=ADMIN_GAUGE_TRACK,
            border_radius="999px",
        ),
        rx.hstack(
            rx.text(
                AdminState.avg_percent_display,
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
    return rx.cond(
        AdminState.has_data,
        rx.vstack(
            rx.hstack(
                rx.card(
                    rx.hstack(
                        rx.vstack(
                            rx.heading("Resumen", size="4"),
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
                        rx.box(_avg_gauge(), width="100%", max_width="320px"),
                        spacing="4",
                        align="center",
                        justify="between",
                        width="100%",
                        wrap="wrap",
                    ),
                    width="100%",
                ),
                _kpi_card(
                    "By Level",
                    AdminState.by_level_top_items,
                    AdminState.by_level_extra_count,
                    chart_data=AdminState.by_level_chart,
                ),
                spacing="4",
                align="start",
                width="100%",
                wrap="wrap",
            ),
            rx.hstack(
                _kpi_card(
                    "Edad",
                    AdminState.edad_top_items,
                    AdminState.edad_extra_count,
                    chart_data=AdminState.edad_chart,
                ),
                _kpi_card(
                    "Genero",
                    AdminState.genero_top_items,
                    AdminState.genero_extra_count,
                    chart_data=AdminState.genero_chart,
                ),
                spacing="4",
                align="start",
                width="100%",
                wrap="wrap",
            ),
            _kpi_card(
                "Ciudad",
                AdminState.ciudad_chart_items,
                AdminState.ciudad_extra_count,
                chart_data=AdminState.ciudad_chart,
            ),
            rx.hstack(
                _kpi_card(
                    "Frecuencia IA",
                    AdminState.frecuencia_ia_top_items,
                    AdminState.frecuencia_ia_extra_count,
                    chart_data=AdminState.frecuencia_ia_chart,
                ),
                _kpi_card(
                    "Nivel Educativo",
                    AdminState.nivel_educativo_top_items,
                    AdminState.nivel_educativo_extra_count,
                    chart_data=AdminState.nivel_educativo_chart,
                ),
                spacing="4",
                align="start",
                width="100%",
                wrap="wrap",
            ),
            rx.hstack(
                _kpi_card(
                    "Ocupacion",
                    AdminState.ocupacion_top_items,
                    AdminState.ocupacion_extra_count,
                    chart_data=AdminState.ocupacion_chart,
                ),
                _kpi_card(
                    "Area",
                    AdminState.area_top_items,
                    AdminState.area_extra_count,
                    chart_data=AdminState.area_chart,
                ),
                spacing="4",
                align="start",
                width="100%",
                wrap="wrap",
            ),
            _kpi_card(
                "Emociones",
                AdminState.emociones_top_items,
                AdminState.emociones_extra_count,
                chart_data=AdminState.emociones_chart,
            ),
            spacing="4",
            align="start",
            width="100%",
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
