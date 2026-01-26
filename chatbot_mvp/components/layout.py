import reflex as rx

from chatbot_mvp.config.settings import is_demo_mode, get_admin_password
from chatbot_mvp.state.theme_state import ThemeState

APP_HEADER_STYLE = {
    "padding": "1rem 1.5rem",
    "border_bottom": "1px solid rgba(148, 163, 184, 0.15)",
    "background": "rgba(20, 20, 20, 0.98)",
}
APP_SIDEBAR_STYLE = {
    "background": "rgba(18, 18, 18, 0.98)",
    "border_right": "1px solid rgba(255, 255, 255, 0.08)",
}
NAV_ITEM_STYLE = {
    "padding": "0.5rem 0.75rem",
    "border_radius": "0.6rem",
    "width": "100%",
    "justify_content": "start",
}
NAV_ITEM_ACTIVE_STYLE = {
    "background": "rgba(20, 184, 166, 0.12)",
    "border": "1px solid rgba(45, 212, 191, 0.25)",
}
NAV_ITEM_HOVER_STYLE = {
    "background": "rgba(255, 255, 255, 0.06)",
}


def _nav_item(label: str, href: str, is_active: bool) -> rx.Component:
    return rx.link(
        rx.button(
            label,
            variant="ghost",
            style=NAV_ITEM_STYLE,
            background=NAV_ITEM_ACTIVE_STYLE["background"] if is_active else "transparent",
            border=NAV_ITEM_ACTIVE_STYLE["border"] if is_active else "1px solid transparent",
            _hover=NAV_ITEM_HOVER_STYLE,
        ),
        href=href,
        width="100%",
        text_decoration="none",
    )


def _nav_section(active_route: str) -> rx.Component:
    items = [
        ("Inicio", "/"),
        ("Evaluación", "/evaluacion"),
        ("Chat", "/chat"),
    ]
    if get_admin_password():
        items.append(("Admin", "/admin"))

    return rx.vstack(
        rx.heading("Navegación", size="3", color="white"),
        rx.vstack(
            *[
                _nav_item(label, href, active_route == href)
                for label, href in items
            ],
            spacing="1",
            width="100%",
        ),
        spacing="3",
        width="100%",
        align="start",
    )


def layout(
    content: rx.Component,
    active_route: str = "",
    sidebar_extra: rx.Component | None = None,
    header_actions: rx.Component | None = None,
    content_scroll: bool = True,
) -> rx.Component:
    header = rx.box(
        rx.hstack(
            rx.hstack(
                rx.heading("Chatbot MVP", size="6", color="var(--gray-50)"),
                rx.cond(
                    is_demo_mode(),
                    rx.hstack(
                        rx.badge("DEMO", variant="soft", color_scheme="yellow"),
                        rx.badge("sin costos", variant="soft", color_scheme="yellow"),
                        spacing="2",
                        align="center",
                    ),
                    rx.box(),
                ),
                spacing="3",
                align="center",
            ),
            header_actions if header_actions else rx.box(),
            justify="between",
            align="center",
            width="100%",
        ),
        width="100%",
        **APP_HEADER_STYLE,
    )

    extra_section = rx.box(
        sidebar_extra if sidebar_extra else rx.box(),
        flex="1",
        min_height="0",
        width="100%",
        overflow="hidden",
    )

    sidebar = rx.vstack(
        _nav_section(active_route),
        extra_section,
        spacing="4",
        width="260px",
        min_width="260px",
        max_width="260px",
        height="100%",
        max_height="100%",
        padding="1rem",
        align="start",
        **APP_SIDEBAR_STYLE,
        overflow="hidden",
    )

    content_wrapper = rx.box(
        content,
        width="100%",
        height="100%",
        min_height="0",
        overflow_y="auto" if content_scroll else "hidden",
    )

    main = rx.hstack(
        sidebar,
        rx.box(
            content_wrapper,
            flex="1",
            min_width="0",
            height="100%",
            min_height="0",
            overflow="hidden",
        ),
        width="100%",
        height="100%",
        min_height="0",
        align="stretch",
        spacing="0",
        flex="1",
    )

    return rx.vstack(
        header,
        main,
        style=ThemeState.applied_theme,
        width="100%",
        height="100vh",
        min_height="0",
        spacing="0",
        overflow="hidden",
    )
