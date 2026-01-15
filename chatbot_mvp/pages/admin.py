from typing import Any

import reflex as rx

from chatbot_mvp.components.layout import layout
from chatbot_mvp.state.admin_state import AdminState


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


def admin() -> rx.Component:
    return layout(
        rx.vstack(
            rx.heading("Admin (Demo)", size="8"),
            rx.hstack(
                rx.button(
                    "Refrescar",
                    on_click=AdminState.load_summary,
                    is_loading=AdminState.loading,
                ),
                rx.cond(
                    AdminState.error != "",
                    rx.text(AdminState.error, color="red"),
                    rx.box(),
                ),
                spacing="3",
                align="center",
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
