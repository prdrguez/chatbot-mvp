import reflex as rx
import json
import os
from typing import Dict, Any

from chatbot_mvp.ui.tokens import CONTENT_BOX_STYLE


class SimplifiedThemeState(rx.State):
    """
    Simplified theme state with intuitive user controls.
    
    Replaces complex developer-focused theme system with user-friendly
    color selection and simple mode switching.
    """
    
    # Theme settings
    mode: str = "light"  # "light" or "dark"
    primary_color: str = "#60a5fa"  # Soft blue
    secondary_color: str = "#34d399"  # Soft green  
    accent_color: str = "#fbbf24"  # Soft amber
    border_radius: str = "medium"  # "small", "medium", "large"
    
    # UI state
    loading: bool = False
    theme_updated: bool = False
    error_message: str = ""
    
    # Theme file paths
    THEME_FILE = "chatbot_mvp/data/simplified_theme.json"
    BACKUP_FILE = "chatbot_mvp/data/theme_overrides.json"
    
    @rx.var
    def is_light_mode(self) -> bool:
        """Check if current mode is light."""
        return self.mode == "light"
    
    @rx.var
    def is_dark_mode(self) -> bool:
        """Check if current mode is dark."""
        return self.mode == "dark"
    
    @rx.var
    def applied_theme(self) -> Dict[str, Any]:
        """
        Generate CSS variables from simplified theme settings.
        
        Returns:
            Dictionary of CSS variables for Reflex style application
        """
        # Convert simplified settings to CSS variables
        css_vars = self._generate_css_variables()
        
        # Add base variables
        base_vars = {
            "--theme-mode": self.mode,
            "--theme-primary": self.primary_color,
            "--theme-secondary": self.secondary_color,
            "--theme-accent": self.accent_color,
            "--theme-border-radius": self._get_border_radius_value(),
        }
        
        # Merge all CSS variables
        css_vars.update(base_vars)
        
        return css_vars
    
    def _generate_css_variables(self) -> Dict[str, str]:
        """
        Generate CSS variables based on current theme settings.
        
        Returns:
            Dictionary mapping CSS variable names to values
        """
        # Generate color variations
        primary_light = self._adjust_brightness(self.primary_color, 0.2)
        primary_dark = self._adjust_brightness(self.primary_color, -0.2)
        secondary_light = self._adjust_brightness(self.secondary_color, 0.2)
        secondary_dark = self._adjust_brightness(self.secondary_color, -0.2)
        
        # Create gradients
        primary_gradient = f"linear-gradient(135deg, {self.primary_color} 0%, {primary_dark} 100%)"
        secondary_gradient = f"linear-gradient(135deg, {self.secondary_color} 0%, {secondary_dark} 100%)"
        
        return {
            # Chat colors
            "--chat-user-bg": primary_gradient,
            "--chat-assistant-bg": secondary_gradient,
            
            # Button colors  
            "--button-primary": self.primary_color,
            "--button-primary-hover": primary_light,
            "--button-secondary": self.secondary_color,
            "--button-secondary-hover": secondary_light,
            
            # Text colors
            "--text-primary": "#1a202c" if self.is_light_mode else "#f8fafc",
            "--text-secondary": "#475569" if self.is_light_mode else "#e2e8f0",
            "--text-accent": self.accent_color,
            
            # Background colors
            "--bg-primary": "#ffffff" if self.is_light_mode else "#1a202c",
            "--bg-secondary": "#f8fafc" if self.is_light_mode else "#2d3748",
            "--bg-tertiary": "#f1f5f9" if self.is_light_mode else "#4a5568",
            
            # Border and shadow
            "--border-color": "#e2e8f0" if self.is_light_mode else "#4a5568",
            "--shadow-color": "rgba(0, 0, 0, 0.1)" if self.is_light_mode else "rgba(0, 0, 0, 0.3)",
        }
    
    def _get_border_radius_value(self) -> str:
        """
        Convert border radius setting to CSS value.
        
        Returns:
            CSS border-radius value
        """
        radius_map = {
            "small": "0.25rem",
            "medium": "0.5rem", 
            "large": "0.75rem",
        }
        return radius_map.get(self.border_radius, "0.5rem")
    
    def _adjust_brightness(self, hex_color: str, factor: float) -> str:
        """
        Adjust brightness of a hex color.
        
        Args:
            hex_color: Hex color string (e.g., "#60a5fa")
            factor: Brightness factor (-1.0 to 1.0)
            
        Returns:
            Adjusted hex color string
        """
        try:
            # Remove # and convert to RGB
            hex_clean = hex_color.lstrip('#')
            r = int(hex_clean[0:2], 16)
            g = int(hex_clean[2:4], 16)
            b = int(hex_clean[4:6], 16)
            
            # Adjust brightness
            if factor > 0:
                r = min(255, int(r + (255 - r) * factor))
                g = min(255, int(g + (255 - g) * factor))
                b = min(255, int(b + (255 - b) * factor))
            else:
                r = max(0, int(r * (1 + factor)))
                g = max(0, int(g * (1 + factor)))
                b = max(0, int(b * (1 + factor)))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color
    
    def load_theme(self) -> None:
        """Load theme from file, with fallback to defaults."""
        try:
            if os.path.exists(self.THEME_FILE):
                with open(self.THEME_FILE, 'r') as f:
                    theme_data = json.load(f)
                    self.mode = theme_data.get("mode", "light")
                    self.primary_color = theme_data.get("primary_color", "#60a5fa")
                    self.secondary_color = theme_data.get("secondary_color", "#34d399")
                    self.accent_color = theme_data.get("accent_color", "#fbbf24")
                    self.border_radius = theme_data.get("border_radius", "medium")
        except Exception as exc:
            self.error_message = f"Error loading theme: {exc}"
    
    def save_theme(self) -> None:
        """Save current theme settings to file."""
        try:
            self.loading = True
            self.error_message = ""
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.THEME_FILE), exist_ok=True)
            
            theme_data = {
                "mode": self.mode,
                "primary_color": self.primary_color,
                "secondary_color": self.secondary_color,
                "accent_color": self.accent_color,
                "border_radius": self.border_radius,
            }
            
            with open(self.THEME_FILE, 'w') as f:
                json.dump(theme_data, f, indent=2)
            
            self.theme_updated = True
            
        except Exception as exc:
            self.error_message = f"Error saving theme: {exc}"
        finally:
            self.loading = False
    
    def set_mode(self, mode: str) -> None:
        """Set theme mode (light/dark)."""
        if mode in ["light", "dark"]:
            self.mode = mode
            self.theme_updated = False
    
    def set_color(self, color_type: str, value: str) -> None:
        """Set a specific color."""
        if color_type == "primary":
            self.primary_color = value
        elif color_type == "secondary":
            self.secondary_color = value
        elif color_type == "accent":
            self.accent_color = value
        
        self.theme_updated = False
    
    def set_border_radius(self, size: str) -> None:
        """Set border radius size."""
        if size in ["small", "medium", "large"]:
            self.border_radius = size
            self.theme_updated = False
    
    def reset_theme(self) -> None:
        """Reset theme to defaults."""
        self.mode = "light"
        self.primary_color = "#60a5fa"
        self.secondary_color = "#34d399"
        self.accent_color = "#fbbf24"
        self.border_radius = "medium"
        self.theme_updated = False
        self.error_message = ""
    
    def get_theme_summary(self) -> Dict[str, Any]:
        """Get current theme summary for display."""
        return {
            "mode": self.mode,
            "colors": {
                "primary": self.primary_color,
                "secondary": self.secondary_color,
                "accent": self.accent_color,
            },
            "border_radius": self.border_radius,
            "css_vars": self.applied_theme,
        }