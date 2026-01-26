import json
from pathlib import Path
from typing import Any, Dict

import reflex as rx

_OVERRIDES_PATH = Path(__file__).resolve().parents[1] / "data" / "theme_overrides.json"
_THEME_PATH = Path(__file__).resolve().parents[1] / "data" / "simplified_theme.json"

THEME_VARS = [
    "--app-header-padding",
    "--app-content-padding",
    "--app-radius-md",
    "--app-card-border",
    "--app-text-danger",
    "--chat-radius",
    "--chat-card-border",
]


class ThemeState(rx.State):
    overrides: dict[str, str] = {}
    saved: bool = False
    error: str = ""

    # Simplified theme settings
    mode: str = "dark"
    primary_color: str = "#60a5fa"
    secondary_color: str = "#34d399"
    accent_color: str = "#fbbf24"
    border_radius: str = "medium"

    # UI state
    loading: bool = False
    theme_updated: bool = False
    error_message: str = ""

    def load_overrides(self) -> None:
        try:
            if not _OVERRIDES_PATH.exists():
                self.overrides = {var: "" for var in THEME_VARS}
                self.saved = False
                self.error = ""
                return
            data = json.loads(_OVERRIDES_PATH.read_text())
            if isinstance(data, dict):
                self.overrides = {var: str(data.get(var, "")) for var in THEME_VARS}
            else:
                self.overrides = {var: "" for var in THEME_VARS}
            self.saved = False
            self.error = ""
        except Exception:
            self.overrides = {var: "" for var in THEME_VARS}
            self.saved = False
            self.error = "No se pudieron cargar los overrides."

    def save_overrides(self) -> None:
        try:
            _OVERRIDES_PATH.parent.mkdir(parents=True, exist_ok=True)
            filtered = {
                key: value
                for key, value in self.overrides.items()
                if key in THEME_VARS and value.strip() != ""
            }
            _OVERRIDES_PATH.write_text(
                json.dumps(filtered, indent=2, sort_keys=True)
            )
            self.saved = True
            self.error = ""
        except Exception:
            self.saved = False
            self.error = "No se pudieron guardar los overrides."

    def set_var(self, name: str, value: str) -> None:
        if name not in THEME_VARS:
            return
        cleaned = value.strip()
        self.overrides[name] = cleaned
        self.save_overrides()

    def reset_overrides(self) -> None:
        self.overrides = {var: "" for var in THEME_VARS}
        self.save_overrides()

    @rx.var(cache=True)
    def applied_overrides(self) -> dict[str, str]:
        return {k: v for k, v in self.overrides.items() if v.strip() != ""}

    @rx.var
    def is_light_mode(self) -> bool:
        return self.mode == "light"

    @rx.var
    def is_dark_mode(self) -> bool:
        return self.mode == "dark"

    def _adjust_brightness(self, hex_color: str, factor: float) -> str:
        try:
            hex_clean = hex_color.lstrip('#')
            r = int(hex_clean[0:2], 16)
            g = int(hex_clean[2:4], 16)
            b = int(hex_clean[4:6], 16)

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

    def _get_border_radius_value(self) -> str:
        radius_map = {
            "small": "0.25rem",
            "medium": "0.5rem",
            "large": "0.75rem",
        }
        return radius_map.get(self.border_radius, "0.5rem")

    def _generate_css_variables(self) -> Dict[str, str]:
        primary_light = self._adjust_brightness(self.primary_color, 0.2)
        primary_dark = self._adjust_brightness(self.primary_color, -0.2)
        secondary_light = self._adjust_brightness(self.secondary_color, 0.2)
        secondary_dark = self._adjust_brightness(self.secondary_color, -0.2)

        primary_gradient = f"linear-gradient(135deg, {self.primary_color} 0%, {primary_dark} 100%)"
        secondary_gradient = f"linear-gradient(135deg, {self.secondary_color} 0%, {secondary_dark} 100%)"

        return {
            "--chat-user-bg": primary_gradient,
            "--chat-assistant-bg": secondary_gradient,
            "--button-primary": self.primary_color,
            "--button-primary-hover": primary_light,
            "--button-secondary": self.secondary_color,
            "--button-secondary-hover": secondary_light,
            "--text-primary": "#1a202c" if self.is_light_mode else "#f8fafc",
            "--text-secondary": "#475569" if self.is_light_mode else "#e2e8f0",
            "--text-accent": self.accent_color,
            "--bg-primary": "#ffffff" if self.is_light_mode else "#1a202c",
            "--bg-secondary": "#f8fafc" if self.is_light_mode else "#2d3748",
            "--bg-tertiary": "#f1f5f9" if self.is_light_mode else "#4a5568",
            "--border-color": "#e2e8f0" if self.is_light_mode else "#4a5568",
            "--shadow-color": "rgba(0, 0, 0, 0.1)" if self.is_light_mode else "rgba(0, 0, 0, 0.3)",
        }

    def load_theme(self) -> None:
        self.load_overrides()
        try:
            if _THEME_PATH.exists():
                data = json.loads(_THEME_PATH.read_text())
                if isinstance(data, dict):
                    self.mode = "dark"
                    self.primary_color = data.get("primary_color", "#60a5fa")
                    self.secondary_color = data.get("secondary_color", "#34d399")
                    self.accent_color = data.get("accent_color", "#fbbf24")
                    self.border_radius = data.get("border_radius", "medium")
            self.error_message = ""
        except Exception as exc:
            self.error_message = f"Error loading theme: {exc}"

    def save_theme(self) -> None:
        try:
            self.loading = True
            self.error_message = ""
            _THEME_PATH.parent.mkdir(parents=True, exist_ok=True)

            theme_data = {
                "mode": self.mode,
                "primary_color": self.primary_color,
                "secondary_color": self.secondary_color,
                "accent_color": self.accent_color,
                "border_radius": self.border_radius,
            }

            _THEME_PATH.write_text(json.dumps(theme_data, indent=2))
            self.theme_updated = True
        except Exception as exc:
            self.error_message = f"Error saving theme: {exc}"
        finally:
            self.loading = False

    def set_mode(self, mode: str) -> None:
        if mode in ["light", "dark"]:
            self.mode = mode
            self.theme_updated = False

    def set_color(self, color_type: str, value: str) -> None:
        if color_type == "primary":
            self.primary_color = value
        elif color_type == "secondary":
            self.secondary_color = value
        elif color_type == "accent":
            self.accent_color = value
        self.theme_updated = False

    def set_border_radius(self, size: str) -> None:
        if size in ["small", "medium", "large"]:
            self.border_radius = size
            self.theme_updated = False

    def reset_theme(self) -> None:
        self.mode = "dark"
        self.primary_color = "#60a5fa"
        self.secondary_color = "#34d399"
        self.accent_color = "#fbbf24"
        self.border_radius = "medium"
        self.theme_updated = False
        self.error_message = ""

    def get_theme_summary(self) -> Dict[str, Any]:
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

    @rx.var
    def applied_theme(self) -> dict[str, str]:
        base_vars = {
            "--theme-mode": self.mode,
            "--theme-primary": self.primary_color,
            "--theme-secondary": self.secondary_color,
            "--theme-accent": self.accent_color,
            "--theme-border-radius": self._get_border_radius_value(),
            "background": "rgba(17, 17, 17, 0.98)",
            "color": "var(--gray-50)",
            "color_scheme": "dark",
        }
        theme_vars = self._generate_css_variables()
        return {**theme_vars, **base_vars, **self.applied_overrides}
