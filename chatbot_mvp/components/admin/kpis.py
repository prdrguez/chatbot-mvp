from typing import Any
import reflex as rx
from chatbot_mvp.state.admin_state import AdminState

ADMIN_CHART_FILL = "var(--teal-9)"
ADMIN_TEXT_COLOR = "var(--gray-11)"
ADMIN_ROW_TEXT_SIZE = "2"
ADMIN_GAUGE_TRACK = "var(--gray-4)"

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

def _mini_chart(items: list[dict[str, Any]]) -> rx.Component:
    return rx.vstack(
        rx.foreach(items, _mini_bar_row),
        spacing="1",
        align="start",
        width="100%",
        max_height="10rem",
        overflow_y="auto",
    )

def kpi_card(
    title: str,
    items: list[dict[str, Any]],
    extra_count: int,
    chart_data: list[dict[str, Any]] | None = None,
) -> rx.Component:
    recharts = getattr(rx, "recharts", None)
    if recharts is not None and hasattr(recharts, "bar_chart"):
        label_list = getattr(recharts, "label_list", None)
        tooltip = getattr(recharts, "tooltip", None)
        responsive_container = getattr(recharts, "responsive_container", None)
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
                width=120,
                stroke="var(--gray-6)",
            ),
            bar,
        ]
        if tooltip is not None:
            chart_children.append(tooltip())
        
        bar_chart = recharts.bar_chart(
            *chart_children,
            data=chart_data,
            layout="vertical",
            height="100%",
            width="100%",
        )
        
        chart = (
            responsive_container(bar_chart, width="100%", height=220)
            if responsive_container is not None
            else bar_chart
        )
        
        return rx.card(
            rx.vstack(
                rx.heading(title, size="4"),
                rx.cond(
                    items,
                    chart,
                    rx.text("Sin datos"),
                ),
                spacing="2",
                align="start",
                width="100%",
            ),
            width="100%",
            height="100%",
            min_height="20rem",
            # Glassmorphism
            background="var(--app-glass-bg)",
            backdrop_filter="var(--app-glass-blur)",
            border="var(--app-glass-border)",
        )
    
    return rx.card(
        rx.vstack(
            rx.heading(title, size="4"),
            rx.cond(
                items,
                _mini_chart(items),
                rx.text("Sin datos"),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        width="100%",
        height="100%",
        min_height="20rem",
    )

def avg_gauge() -> rx.Component:
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
        rx.progress(value=AdminState.avg_percent_int, max=100, width="100%"),
        rx.hstack(
            rx.text(AdminState.avg_percent_display, size="5", font_weight="700"),
            rx.badge(AdminState.avg_level_label, variant="soft"),
            spacing="2",
        ),
        width="100%",
    )
