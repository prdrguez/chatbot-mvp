import reflex as rx

config = rx.Config(
    app_name="chatbot_mvp",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)
