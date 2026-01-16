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


def _count_list(items: list[dict[str, Any]]) -> rx.Component:
    return rx.cond(
        items,
        rx.vstack(
            rx.foreach(
                items,
                lambda item: rx.text(item["label"], ": ", item["count"]),
            ),
            spacing="1",
            align="start",
        ),
        rx.text("Sin datos"),
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


def admin() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Admin (Demo)", size="8"),
            rx.card(
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
            ),
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
            rx.cond(
                AdminState.has_data,
                rx.vstack(
                    rx.vstack(
                        rx.text("Total:", font_weight="600"),
                        rx.text(AdminState.total),
                        rx.text("Avg %:", font_weight="600"),
                        rx.text(AdminState.avg_percent, "%"),
                        spacing="1",
                        align="start",
                    ),
                    rx.vstack(
                        rx.text("By Level", font_weight="600"),
                        _count_list(AdminState.by_level_items),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Edad", font_weight="600"),
                        _count_list(AdminState.edad_items),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Genero", font_weight="600"),
                        _count_list(AdminState.genero_items),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Ciudad", font_weight="600"),
                        _count_list(AdminState.ciudad_items),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Frecuencia IA", font_weight="600"),
                        _count_list(AdminState.frecuencia_ia_items),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Nivel Educativo", font_weight="600"),
                        _count_list(AdminState.nivel_educativo_items),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Ocupacion", font_weight="600"),
                        _count_list(AdminState.ocupacion_items),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Area", font_weight="600"),
                        _count_list(AdminState.area_items),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Emociones", font_weight="600"),
                        _count_list(AdminState.emociones_items),
                        spacing="1",
                        align="start",
                        width="100%",
                    ),
                    spacing="4",
                    align="start",
                    width="100%",
                    max_width="720px",
                ),
                rx.text("Sin datos aún"),
            ),
            spacing="4",
            align="start",
            width="100%",
        )
    )
