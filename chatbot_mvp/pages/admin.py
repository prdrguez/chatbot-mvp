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


def _item_label(item: dict[str, Any]) -> str:
    return str(
        item.get("label")
        or item.get("name")
        or item.get("key")
        or item
    )


def _item_count(item: dict[str, Any]) -> int:
    return int(item.get("count") or item.get("value") or 0)


def _count_list(items: list[dict[str, Any]]) -> rx.Component:
    if not items:
        return rx.text("Sin datos")
    return rx.vstack(
        *[
            rx.hstack(
                rx.text(_item_label(item)),
                rx.text(_item_count(item)),
                spacing="2",
                align="center",
                width="100%",
                justify="between",
            )
            for item in items
        ],
        spacing="1",
        align="start",
        width="100%",
    )


def _mini_bar_chart(items: list[dict[str, Any]]) -> rx.Component:
    if not items:
        return rx.text("Sin datos")
    counts = [_item_count(item) for item in items]
    max_count = max(counts) if counts else 1
    return rx.vstack(
        *[
            rx.hstack(
                rx.text(_item_label(item), size="2"),
                rx.box(
                    rx.box(
                        height="0.35rem",
                        width=f"{int((_item_count(item) / max_count) * 100)}%",
                        background_color="var(--gray-600)",
                        border_radius="999px",
                    ),
                    width="100%",
                ),
                rx.text(_item_count(item), size="2"),
                spacing="2",
                align="center",
                width="100%",
            )
            for item in items
        ],
        spacing="1",
        align="start",
        width="100%",
    )


def _kpi_card(title: str, items: list[dict[str, Any]]) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(title, size="4"),
            _mini_bar_chart(items),
            _count_list(items),
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
            rx.vstack(
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
                    _kpi_card("By Level", AdminState.by_level_items),
                    _kpi_card("Edad", AdminState.edad_items),
                    _kpi_card("Genero", AdminState.genero_items),
                    _kpi_card("Ciudad", AdminState.ciudad_items),
                    _kpi_card("Frecuencia IA", AdminState.frecuencia_ia_items),
                    _kpi_card("Nivel Educativo", AdminState.nivel_educativo_items),
                    _kpi_card("Ocupacion", AdminState.ocupacion_items),
                    _kpi_card("Area", AdminState.area_items),
                    _kpi_card("Emociones", AdminState.emociones_items),
                ],
                columns=["1", "2"],
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
                    _kpi_card("By Level", AdminState.by_level_items),
                    _kpi_card("Edad", AdminState.edad_items),
                    _kpi_card("Genero", AdminState.genero_items),
                    _kpi_card("Ciudad", AdminState.ciudad_items),
                    _kpi_card("Frecuencia IA", AdminState.frecuencia_ia_items),
                    _kpi_card("Nivel Educativo", AdminState.nivel_educativo_items),
                    _kpi_card("Ocupacion", AdminState.ocupacion_items),
                    _kpi_card("Area", AdminState.area_items),
                    _kpi_card("Emociones", AdminState.emociones_items),
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
