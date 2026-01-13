"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

from chatbot_mvp.pages.chat import chat
from chatbot_mvp.pages.evaluacion import evaluacion
from chatbot_mvp.pages.home import home


app = rx.App()
app.add_page(home, route="/")
app.add_page(evaluacion, route="/evaluacion")
app.add_page(chat, route="/chat")
