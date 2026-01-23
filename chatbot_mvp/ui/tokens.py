HEADER_BOX_STYLE = {
    "padding": "var(--app-header-padding)",
    "border_bottom": "var(--app-border-bottom)",
}

CONTENT_BOX_STYLE = {
    "padding": "var(--app-content-padding)",
}

APP_CARD_STYLE = {
    "width": "100%",
}

APP_PAGE_TITLE_STYLE = {
    "size": "7",
}

APP_SECONDARY_BUTTON_PROPS = {
    "variant": "outline",
}

APP_PRIMARY_BUTTON_PROPS = {
    "variant": "solid",
}

APP_SURFACE_STYLE = {
    "background": "var(--app-glass-bg)",
    "backdrop_filter": "var(--app-glass-blur)",
    "border": "var(--app-glass-border)",
    "box_shadow": "var(--app-glass-shadow)",
    "border_radius": "var(--app-radius-md)",
}

CHAT_SURFACE_STYLE = {
    "background": "var(--app-glass-bg)",
    "backdrop_filter": "var(--app-glass-blur)",
    "border": "var(--app-glass-border)",
    "padding": "var(--chat-surface-padding)",
    "border_radius": "var(--chat-radius)",
    "box_shadow": "var(--app-glass-shadow)",
    "transition": "var(--chat-transition)",
    "animation": "fadeInUp 0.6s ease-out",
}

CHAT_MESSAGE_USER_STYLE = {
    "background": "var(--chat-user-bg)",
    "color": "white",
    "box_shadow": "var(--chat-shadow-md)",
    "transition": "var(--chat-transition)",
    "animation": "slideInRight 0.3s ease-out",
}

CHAT_MESSAGE_ASSISTANT_STYLE = {
    "background": "var(--chat-assistant-bg)",
    "color": "var(--gray-900)",
    "box_shadow": "var(--chat-shadow-sm)",
    "transition": "var(--chat-transition)",
    "animation": "slideInLeft 0.3s ease-out",
}

CHAT_INPUT_STYLE = {
    "background": "white",
    "border": "1px solid var(--gray-300)",
    "border_radius": "var(--app-radius-md)",
    "color": "var(--gray-900)",
    "padding": "0.5rem",
}

CHAT_SEND_BUTTON_STYLE = {
    "background": "var(--chat-bg-gradient)",
    "box_shadow": "var(--chat-shadow-sm)",
    "transition": "var(--chat-transition)",
    "_hover": {
        "box_shadow": "var(--chat-shadow-md)",
        "transform": "var(--chat-hover-lift)",
    }
}
