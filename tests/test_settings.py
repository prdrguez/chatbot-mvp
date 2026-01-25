from chatbot_mvp.config.settings import get_ai_provider, get_env_value


def test_get_ai_provider_strips_quotes(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", '"groq"')
    assert get_ai_provider() == "groq"


def test_get_env_value_strips_quotes(monkeypatch):
    monkeypatch.setenv("GROQ_MODEL", "'llama-3.1-8b-instant'")
    assert get_env_value("GROQ_MODEL") == "llama-3.1-8b-instant"
