import json
from pathlib import Path

import reflex as rx

_OVERRIDES_PATH = Path(__file__).resolve().parents[1] / "data" / "theme_overrides.json"

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
