"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

from chatbot_mvp.pages.admin import admin
from chatbot_mvp.pages.chat import chat
from chatbot_mvp.pages.evaluacion import evaluacion
from chatbot_mvp.pages.home import home
from chatbot_mvp.state.admin_state import AdminState
from chatbot_mvp.state.evaluacion_state import EvaluacionState


app = rx.App()
app.add_page(home, route="/")
app.add_page(evaluacion, route="/evaluacion", on_load=EvaluacionState.ensure_initialized)
app.add_page(chat, route="/chat")
app.add_page(admin, route="/admin", on_load=AdminState.load_summary)
