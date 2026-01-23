import reflex as rx

from chatbot_mvp.state.simplified_theme_state import SimplifiedThemeState


def mode_toggle() -> rx.Component:
    """
    Light/Dark mode toggle switch.
    
    Returns:
        Toggle component for theme mode switching
    """
    return rx.hstack(
        rx.text("☀️", font_size="20px"),
        rx.button(
            "☀️",
            on_click=lambda: SimplifiedThemeState.set_mode("light"),
            variant=rx.cond(
                SimplifiedThemeState.is_light_mode,
                "solid",
                "soft"
            ),
            color_scheme=rx.cond(
                SimplifiedThemeState.is_light_mode,
                "yellow",
                "gray"
            ),
            size="2",
            margin_right="1"
        ),
        rx.button(
            "🌙", 
            on_click=lambda: SimplifiedThemeState.set_mode("dark"),
            variant=rx.cond(
                SimplifiedThemeState.is_dark_mode,
                "solid",
                "soft"
            ),
            color_scheme=rx.cond(
                SimplifiedThemeState.is_dark_mode,
                "blue",
                "gray"
            ),
            size="2"
        ),
        align="center",
        spacing="1"
    )


def color_picker(label: str, color_value: str, color_type: str) -> rx.Component:
    """
    Color picker with preview.
    
    Args:
        label: Label for color picker
        color_value: Current color value
        color_type: Type of color (primary/secondary/accent)
        
    Returns:
        Color picker component with preview
    """
    return rx.vstack(
        rx.text(label, font_weight="500", margin_bottom="1"),
        rx.hstack(
            # Color preview
            rx.box(
                width="40px",
                height="40px",
                background=color_value,
                border_radius="8px",
                border="2px solid #e2e8f0",
                cursor="pointer",
                transition="all 0.2s",
            ),
            
            # Color input
            rx.input(
                value=color_value,
                on_change=lambda v: SimplifiedThemeState.set_color(color_type, v),
                placeholder="#000000",
                type_="color",
                margin_left="3",
                size="2",
                width="120px"
            ),
            
            align="center",
            spacing="2"
        ),
        spacing="1",
        width="100%"
    )


def border_radius_selector() -> rx.Component:
    """
    Border radius selector with size options.
    
    Returns:
        Radio button group for border radius selection
    """
    return rx.vstack(
        rx.text("Bordes Redondeados", font_weight="500", margin_bottom="3"),
        rx.radio(
            ["Pequeño", "Mediano", "Grande"],
            value=SimplifiedThemeState.border_radius,
            on_change=lambda value: SimplifiedThemeState.set_border_radius("small" if value == "Pequeño" else "medium" if value == "Mediano" else "large"),
            default_value="Mediano",
            size="2"
        ),
        spacing="1",
        width="100%"
    )


def action_buttons() -> rx.Component:
    """
    Save, reset, and action buttons for theme editor.
    
    Returns:
        Button group for theme actions
    """
    return rx.hstack(
        # Reset button
        rx.button(
            "Resetear",
            on_click=lambda: SimplifiedThemeState.reset_theme(),
            variant="soft",
            color_scheme="gray",
            size="2",
            loading=SimplifiedThemeState.loading
        ),
        
        # Save button
        rx.button(
            "Guardar",
            on_click=lambda: SimplifiedThemeState.save_theme(),
            variant="solid",
            color_scheme="blue", 
            size="2",
            loading=SimplifiedThemeState.loading
        ),
        
        spacing="3",
        justify="end",
        width="100%"
    )


def error_message() -> rx.Component:
    """
    Error message display for theme operations.
    
    Returns:
        Error callout component if error exists
    """
    return rx.cond(
        SimplifiedThemeState.error_message != "",
        rx.callout(
            SimplifiedThemeState.error_message,
            icon="warning",
            color_scheme="red",
            margin_top="3",
            width="100%"
        )
    )


def success_message() -> rx.Component:
    """
    Success message display for theme operations.
    
    Returns:
        Success callout component if theme was updated
    """
    return rx.cond(
        SimplifiedThemeState.theme_updated,
        rx.callout(
            "¡Tema guardado exitosamente!",
            icon="check",
            color_scheme="green", 
            margin_top="3",
            width="100%"
        )
    )


def simplified_theme_editor() -> rx.Component:
    """
    Complete simplified theme editor interface.
    
    Replaces complex developer-focused theme editor with 
    user-friendly color selection and simple controls.
    
    Returns:
        Complete theme editor component
    """
    return rx.vstack(
        # Header
        rx.heading("Personalizar Apariencia", size="5", margin_bottom="6"),
        rx.text(
            "Configura los colores y estilo de la interfaz de forma sencilla.",
            color="#6b7280",
            margin_bottom="8"
        ),
        
        # Theme mode toggle
        rx.card(
            rx.vstack(
                rx.text("Modo de Tema", font_weight="500", margin_bottom="3"),
                mode_toggle(),
                spacing="3",
                padding="4",
                width="100%"
            ),
            margin_bottom="6",
            variant="surface"
        ),
        
        # Color customization
        rx.card(
            rx.vstack(
                rx.text("Colores Principales", font_weight="500", margin_bottom="4"),
                
                color_picker("Color Primario", SimplifiedThemeState.primary_color, "primary"),
                color_picker("Color Secundario", SimplifiedThemeState.secondary_color, "secondary"),
                color_picker("Color de Acento", SimplifiedThemeState.accent_color, "accent"),
                
                spacing="4",
                padding="4",
                width="100%"
            ),
            margin_bottom="6",
            variant="surface"
        ),
        
        # Border radius
        rx.card(
            rx.vstack(
                border_radius_selector(),
                spacing="3",
                padding="4",
                width="100%"
            ),
            margin_bottom="6",
            variant="surface"
        ),
        
        # Action buttons
        action_buttons(),
        
        # Messages
        error_message(),
        success_message(),
        
        spacing="4",
        width="100%",
        max_width="500px"
    )