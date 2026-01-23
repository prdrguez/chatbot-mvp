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
    "border": "var(--app-card-border)",
    "padding": "var(--app-surface-padding)",
    "border_radius": "var(--app-radius-md)",
}

CHAT_SURFACE_STYLE = {
    "border": "var(--chat-border-modern)",
    "padding": "var(--chat-surface-padding)",
    "border_radius": "var(--chat-radius)",
    "box_shadow": "var(--chat-shadow-lg)",
    "background": "linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)",
    "transition": "var(--chat-transition)",
    "_hover": {
        "box_shadow": "var(--chat-shadow-xl)",
        "transform": "var(--chat-hover-lift)",
    }
}

CHAT_MESSAGE_USER_STYLE = {
    "background": "var(--chat-user-bg)",
    "color": "white",
    "box_shadow": "var(--chat-shadow-md)",
    "transition": "var(--chat-transition)",
    "_hover": {
        "box_shadow": "var(--chat-shadow-lg)",
        "transform": "var(--chat-message-scale)",
    }
}

CHAT_MESSAGE_ASSISTANT_STYLE = {
    "background": "var(--chat-assistant-bg)",
    "color": "var(--gray-800)",
    "box_shadow": "var(--chat-shadow-sm)",
    "transition": "var(--chat-transition)",
    "_hover": {
        "box_shadow": "var(--chat-shadow-md)",
        "transform": "var(--chat-message-scale)",
    }
}

CHAT_INPUT_STYLE = {
    "box_shadow": "var(--chat-shadow-sm)",
    "border": "var(--chat-border-modern)",
    "transition": "var(--chat-transition)",
    "_focus": {
        "box_shadow": "0 0 0 3px rgba(59, 130, 246, 0.1), var(--chat-shadow-md)",
        "border_color": "var(--blue-500)",
    }
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
