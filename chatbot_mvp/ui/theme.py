import reflex as rx

APP_THEME = rx.theme(
    appearance="light",
    has_background=True,
    radius="large",
    accent_color="teal",
)

GLOBAL_STYLE = {
    "font_family": "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
}

STYLESHEETS = ["/theme.css"]
