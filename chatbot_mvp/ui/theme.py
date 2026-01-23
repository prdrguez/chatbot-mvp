import reflex as rx

APP_THEME = rx.theme(
    appearance="light",
    has_background=True,
    radius="large",
    accent_color="teal",
)

GLOBAL_STYLE = {
    "font_family": "Outfit, Inter, system-ui, sans-serif",
}

STYLESHEETS = [
    "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap",
    "/theme.css",
]
