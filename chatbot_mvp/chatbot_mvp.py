"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

import chatbot_mvp.state
from chatbot_mvp.ui.theme import APP_THEME, GLOBAL_STYLE, STYLESHEETS
from chatbot_mvp.pages.admin import admin
from chatbot_mvp.pages.chat import chat
from chatbot_mvp.pages.evaluacion import evaluacion
from chatbot_mvp.pages.home import home
from chatbot_mvp.pages.login import login_page
from chatbot_mvp.pages.ui_gallery import ui_gallery
from chatbot_mvp.state.admin_state import AdminState
from chatbot_mvp.state.auth_state import AuthState
from chatbot_mvp.state.evaluacion_state import EvaluacionState
from chatbot_mvp.state.theme_state import ThemeState
from chatbot_mvp.config.settings import is_demo_mode, get_admin_password


app = rx.App(theme=APP_THEME, style=GLOBAL_STYLE, stylesheets=STYLESHEETS)
app.add_page(home, route="/", on_load=ThemeState.load_theme)
app.add_page(
    evaluacion,
    route="/evaluacion",
    on_load=[ThemeState.load_theme, EvaluacionState.ensure_initialized],
)
from chatbot_mvp.state.chat_state import ChatState
app.add_page(chat, route="/chat", on_load=[ThemeState.load_theme, ChatState.load_sessions])

app.add_page(
    admin,
    route="/admin",
    on_load=[ThemeState.load_theme, AuthState.check_login, AuthState.check_session, AdminState.load_summary],
)

# Login page for admin access
app.add_page(login_page, route="/login", on_load=ThemeState.load_theme)

if is_demo_mode():
    app.add_page(ui_gallery, route="/ui", on_load=ThemeState.load_theme)
