"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

from chatbot_mvp.ui.theme import APP_THEME, GLOBAL_STYLE, STYLESHEETS
from chatbot_mvp.pages.admin import admin
from chatbot_mvp.pages.chat import chat
from chatbot_mvp.pages.evaluacion import evaluacion
from chatbot_mvp.pages.home import home
from chatbot_mvp.pages.ui_gallery import ui_gallery
from chatbot_mvp.state.admin_state import AdminState
from chatbot_mvp.state.evaluacion_state import EvaluacionState
from chatbot_mvp.state.theme_state import ThemeState
from chatbot_mvp.config.settings import is_demo_mode


app = rx.App(theme=APP_THEME, style=GLOBAL_STYLE, stylesheets=STYLESHEETS)
app.add_page(home, route="/", on_load=ThemeState.load_overrides)
app.add_page(
    evaluacion,
    route="/evaluacion",
    on_load=[ThemeState.load_overrides, EvaluacionState.ensure_initialized],
)
app.add_page(chat, route="/chat", on_load=ThemeState.load_overrides)
app.add_page(
    admin,
    route="/admin",
    on_load=[ThemeState.load_overrides, AdminState.load_summary],
)

if is_demo_mode():
    app.add_page(ui_gallery, route="/ui", on_load=ThemeState.load_overrides)
