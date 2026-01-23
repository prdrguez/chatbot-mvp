import reflex as rx
from chatbot_mvp.state.chat_state import ChatState

def sidebar_item(session: dict) -> rx.Component:
    return rx.button(
        rx.hstack(
            rx.icon("message-square", size=16),
            rx.text(
                session["session_id"],
                size="2",
                weight="medium",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        on_click=lambda: ChatState.load_session(session["session_id"]),
        variant="ghost",
        width="100%",
        justify_content="start",
        padding="0.5rem",
        border_radius="var(--app-radius-md)",
        _hover={"background": "var(--gray-3)"},
    )

def chat_sidebar() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Sesiones", size="4"),
            rx.icon_button(
                rx.icon("plus"),
                on_click=ChatState.clear_chat,
                variant="ghost",
                size="1",
            ),
            justify="between",
            align="center",
            width="100%",
            padding_bottom="1rem",
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
        ),
        spacing="3",
        width="240px",
        height="100%",
        padding="1rem",
        border_right="1px solid var(--gray-4)",
        # glassmorphism logic could be added here later
        background="rgba(255, 255, 255, 0.5)",
        backdrop_filter="blur(10px)",
        display=rx.cond(rx.breakpoints(initial=False, md=True), "flex", "none"),
    )
