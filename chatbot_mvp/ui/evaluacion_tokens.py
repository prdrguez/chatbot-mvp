from chatbot_mvp.ui.tokens import (
    APP_CARD_STYLE,
    APP_PAGE_TITLE_STYLE,
    APP_PRIMARY_BUTTON_PROPS,
    APP_SECONDARY_BUTTON_PROPS,
    APP_SURFACE_STYLE,
)

EVAL_STACK_BASE = {
    "align": "start",
    "width": "100%",
}

EVAL_CONTAINER_STYLE = {
    "width": "100%",
    "max_width": "900px",
}

EVAL_CARD_STYLE = APP_CARD_STYLE

EVAL_CARD_HEADER_STYLE = {
    **EVAL_STACK_BASE,
    "spacing": "2",
}

EVAL_SECTION_STACK_STYLE = {
    **EVAL_STACK_BASE,
    "spacing": "4",
}

EVAL_PROGRESS_STACK_STYLE = {
    **EVAL_STACK_BASE,
    "spacing": "3",
}

EVAL_OPTION_STACK_STYLE = {
    **EVAL_STACK_BASE,
    "spacing": "2",
}

EVAL_LABEL_STACK_STYLE = {
    **EVAL_STACK_BASE,
    "spacing": "1",
}

EVAL_BADGE_ROW_STYLE = {
    "spacing": "2",
    "align": "center",
    "width": "100%",
}

EVAL_BUTTON_ROW_STYLE = {
    "spacing": "3",
}

EVAL_TITLE_STYLE = APP_PAGE_TITLE_STYLE

EVAL_PRIMARY_BUTTON_PROPS = APP_PRIMARY_BUTTON_PROPS

EVAL_SECONDARY_BUTTON_PROPS = APP_SECONDARY_BUTTON_PROPS

EVAL_PROMPT_TEXT_STYLE = {
    "size": "5",
    "font_weight": "600",
}

EVAL_SUBTITLE_STYLE = {
    "font_weight": "600",
}

EVAL_ERROR_TEXT_STYLE = {
    "color": "var(--app-text-danger)",
}

EVAL_INPUT_PROPS = {
    "width": "100%",
}

EVAL_RADIO_ITEM_STYLE = {
    "width": "100%",
    "white_space": "normal",
    "align_items": "flex-start",
}

EVAL_CHECKBOX_STYLE = {
    "width": "100%",
    "white_space": "normal",
}

EVAL_RESULT_BOX_STYLE = APP_SURFACE_STYLE
