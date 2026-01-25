import reflex as rx
from chatbot_mvp.state.chat_state import ChatState

SIDEBAR_STYLE = {
    "background": "rgba(15, 23, 42, 0.92)",
    "border": "1px solid rgba(148, 163, 184, 0.25)",
    "box_shadow": "0 12px 40px rgba(0,0,0,0.25)",
    "border_radius": "16px",
}
SIDEBAR_HEADER_STYLE = {
    "padding_bottom": "1rem",
}
SIDEBAR_ITEM_STYLE = {
    "padding": "0.55rem 0.6rem",
    "border_radius": "0.6rem",
    "width": "100%",
    "justify_content": "start",
}
SIDEBAR_ITEM_ACTIVE_STYLE = {
    "background": "rgba(20, 184, 166, 0.12)",
    "border": "1px solid rgba(45, 212, 191, 0.25)",
}
SIDEBAR_ITEM_HOVER_STYLE = {
    "background": "rgba(148, 163, 184, 0.12)",
}
SIDEBAR_TEXT_TITLE = {
    "color": "white",
    "size": "2",
    "weight": "medium",
}
SIDEBAR_TEXT_PREVIEW = {
    "color": "rgba(226, 232, 240, 0.75)",
    "size": "1",
}
SIDEBAR_TEXT_DATE = {
    "color": "rgba(226, 232, 240, 0.6)",
    "size": "1",
}


def _format_date(value: str) -> str:
    s = value.to_string()
    return rx.cond(
        (s == "") | (s == "None") | (s == "null"),
        "",
        s[:10],
    )

def sidebar_item(session: dict) -> rx.Component:
    session_id = session.get("session_id", "")
    preview = rx.cond(
        session.get("preview", "") != "",
        session.get("preview", ""),
        session_id,
    )
    updated_at = rx.cond(
        session.get("updated_at", "") != "",
        session.get("updated_at", ""),
        session.get("created_at", ""),
    )
    date_label = _format_date(updated_at)
    is_active = session_id == ChatState.session_id

    collapsed = rx.icon_button(
        rx.icon("message-square", size=16),
        on_click=lambda: ChatState.load_session(session_id),
        variant="ghost",
        size="2",
        width="100%",
        justify_content="center",
        border_radius="var(--app-radius-md)",
        color="white",
        _hover=SIDEBAR_ITEM_HOVER_STYLE,
    )

    expanded = rx.button(
        rx.vstack(
            rx.hstack(
                rx.icon("message-square", size=16),
                rx.text(
                    preview,
                    **SIDEBAR_TEXT_TITLE,
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.text(
                preview,
                **SIDEBAR_TEXT_PREVIEW,
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
            ),
            rx.text(
                date_label,
                **SIDEBAR_TEXT_DATE,
            ),
            spacing="1",
            align="start",
            width="100%",
        ),
        on_click=lambda: ChatState.load_session(session_id),
        variant="ghost",
        style=SIDEBAR_ITEM_STYLE,
        _hover=SIDEBAR_ITEM_HOVER_STYLE,
        background=rx.cond(
            is_active,
            SIDEBAR_ITEM_ACTIVE_STYLE["background"],
            "transparent",
        ),
        border=rx.cond(
            is_active,
            SIDEBAR_ITEM_ACTIVE_STYLE["border"],
            "1px solid transparent",
        ),
    )

    return rx.cond(ChatState.sidebar_collapsed, collapsed, expanded)

def chat_sidebar() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon_button(
                rx.cond(
                    ChatState.sidebar_collapsed,
                    rx.icon("chevron-right"),
                    rx.icon("chevron-left"),
                ),
                on_click=ChatState.toggle_sidebar,
                variant="ghost",
                size="1",
                color="var(--teal-9)",
                _hover={"background": "rgba(20, 184, 166, 0.12)"},
            ),
            rx.cond(
                ChatState.sidebar_collapsed,
                rx.icon("message-square", size=16),
                rx.heading("Sesiones", size="4", color="white"),
            ),
            rx.icon_button(
                rx.icon("plus"),
                on_click=ChatState.clear_chat,
                variant="ghost",
                size="1",
                color="var(--teal-9)",
                _hover={"background": "rgba(20, 184, 166, 0.12)"},
            ),
            justify="between",
            align="center",
            width="100%",
            **SIDEBAR_HEADER_STYLE,
        ),
        rx.scroll_area(
            rx.vstack(
                rx.foreach(ChatState.session_list, sidebar_item),
                spacing="1",
                width="100%",
            ),
            height="auto",
            max_height="70vh",
            width="100%",
            padding_right="0.25rem",
        ),
        spacing="3",
        width=rx.cond(ChatState.sidebar_collapsed, "64px", "280px"),
        height="100vh",
        padding=rx.cond(ChatState.sidebar_collapsed, "0.75rem", "1rem"),
        **SIDEBAR_STYLE,
        display=rx.cond(rx.breakpoints(initial=False, md=True), "flex", "none"),
    )
