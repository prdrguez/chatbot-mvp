import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from chatbot_mvp.config.settings import sanitize_env_value

_SETTINGS_PATH = Path(__file__).resolve().parents[1] / "data" / "app_settings.json"
_LOCK = threading.Lock()
_VALID_PROVIDERS = {"gemini", "groq"}


def _read_settings() -> Dict[str, Any]:
    if not _SETTINGS_PATH.exists():
        return {}
    try:
        raw = _SETTINGS_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _write_settings(data: Dict[str, Any]) -> None:
    _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=_SETTINGS_PATH.parent,
    ) as tmp_file:
        tmp_file.write(payload)
        tmp_file.flush()
        os.fsync(tmp_file.fileno())
        temp_name = tmp_file.name
    os.replace(temp_name, _SETTINGS_PATH)


def get_app_settings() -> Dict[str, Any]:
    with _LOCK:
        return _read_settings()


def get_provider_override() -> Optional[str]:
    with _LOCK:
        data = _read_settings()
    value = sanitize_env_value(str(data.get("ai_provider", "")))
    value = value.lower()
    return value if value in _VALID_PROVIDERS else None


def set_provider_override(provider: str) -> str:
    cleaned = sanitize_env_value(provider).lower()
    if cleaned not in _VALID_PROVIDERS:
        raise ValueError("Proveedor invalido")
    with _LOCK:
        data = _read_settings()
        data["ai_provider"] = cleaned
        _write_settings(data)
    return cleaned
