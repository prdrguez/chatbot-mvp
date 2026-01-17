from typing import Any

import reflex as rx

from chatbot_mvp.components.layout import layout
from chatbot_mvp.state.admin_state import AdminState
from chatbot_mvp.state.theme_state import ThemeState

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
        rx.text(item["label"]),
        rx.text(item["count"]),
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
            recharts.bar(data_key="value", fill="var(--gray-600)"),
            recharts.x_axis(data_key="name"),
            recharts.y_axis(),
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
) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(title, size="4"),
            rx.cond(
                items,
                _mini_chart(items, chart_data),
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

def _theme_field(label: str, var_name: str, placeholder: str) -> rx.Component:
    return rx.vstack(
        rx.text(label, font_weight="600"),
        rx.input(
            value=ThemeState.overrides[var_name],
            placeholder=placeholder,
            on_change=ThemeState.set_var(var_name),
            width="100%",
        ),
        spacing="1",
        align="start",
        width="100%",
    )


def _theme_preview_card() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Preview", size="5"),
                rx.badge("Ejemplo", variant="soft"),
                spacing="2",
                align="center",
            ),
            rx.text(
                "Asi se veria una superficie con texto y botones usando tus valores.",
                color="var(--gray-600)",
            ),
            rx.hstack(
                rx.button("Primario", variant="solid"),
                rx.button("Secundario", variant="outline"),
                spacing="2",
                align="center",
            ),
            rx.box(
                rx.text("Chat surface de ejemplo", size="2"),
                border="var(--chat-card-border)",
                padding="var(--chat-surface-padding)",
                border_radius="var(--chat-radius)",
                width="100%",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
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


class AdminViewState(rx.State):
    section: str = "kpis"

    def set_section(self, section: str) -> None:
        self.section = section


def _admin_theme_section() -> rx.Component:
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
                        AdminState.ciudad_top_items,
                        AdminState.ciudad_chart,
                        AdminState.ciudad_extra_count,
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
                        AdminState.ciudad_top_items,
                        AdminState.ciudad_chart,
                        AdminState.ciudad_extra_count,
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
