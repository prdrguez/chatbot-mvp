from chatbot_mvp.config.settings import (
    get_ai_provider,
    get_env_value,
    get_kb_min_score_strict,
    get_kb_top_k,
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


def test_get_kb_top_k(monkeypatch):
    monkeypatch.setenv("KB_TOP_K", "6")
    assert get_kb_top_k() == 6

    monkeypatch.setenv("KB_TOP_K", "99")
    assert get_kb_top_k() == 8

    monkeypatch.setenv("KB_TOP_K", "0")
    assert get_kb_top_k() == 1


def test_get_kb_min_score_strict(monkeypatch):
    monkeypatch.setenv("KB_MIN_SCORE_STRICT", "0.52")
    assert get_kb_min_score_strict() == 0.52

    monkeypatch.setenv("KB_MIN_SCORE_STRICT", "2.0")
    assert get_kb_min_score_strict() == 1.0

    monkeypatch.setenv("KB_MIN_SCORE_STRICT", "-1")
    assert get_kb_min_score_strict() == 0.0
