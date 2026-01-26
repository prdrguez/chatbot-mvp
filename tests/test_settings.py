from chatbot_mvp.config.settings import (
    get_ai_provider,
    get_env_value,
    get_runtime_ai_provider,
)
from chatbot_mvp.services import app_settings_store


def test_get_ai_provider_strips_quotes(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", '"groq"')
    assert get_ai_provider() == "groq"


def test_get_env_value_strips_quotes(monkeypatch):
    monkeypatch.setenv("GROQ_MODEL", "'llama-3.1-8b-instant'")
    assert get_env_value("GROQ_MODEL") == "llama-3.1-8b-instant"


def test_get_runtime_provider_override(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setattr(
        app_settings_store, "_SETTINGS_PATH", tmp_path / "app_settings.json"
    )
    app_settings_store.set_provider_override("groq")
    assert get_runtime_ai_provider() == "groq"


def test_get_runtime_provider_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setattr(
        app_settings_store, "_SETTINGS_PATH", tmp_path / "app_settings.json"
    )
    (tmp_path / "app_settings.json").write_text(
        '{"ai_provider": "openai"}', encoding="utf-8"
    )
    assert get_runtime_ai_provider() == "gemini"
