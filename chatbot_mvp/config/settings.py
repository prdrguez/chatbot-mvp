import logging
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


_ROOT = Path(__file__).resolve().parents[2]
logger = logging.getLogger(__name__)
if load_dotenv is None:
    logger.warning("python-dotenv not installed; .env will not be loaded")
else:
    load_dotenv(dotenv_path=_ROOT / ".env", override=False)


_TRUE_VALUES = {"1", "true", "yes", "on"}
_DEFAULT_AI_PROVIDER = "gemini"
_VALID_AI_PROVIDERS = {"demo", "openai", "gemini", "groq"}


def sanitize_env_value(value: str | None) -> str:
    if value is None:
        return ""
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
        cleaned = cleaned[1:-1].strip()
    return cleaned


def get_env_value(name: str, default: str = "") -> str:
    raw = os.getenv(name)
    if raw is None:
        return default
    cleaned = sanitize_env_value(raw)
    return cleaned if cleaned != "" else default


def get_ai_provider() -> str:
    """
    Get the configured AI provider.
    
    Returns:
        'demo', 'openai', 'gemini', or 'groq' based on AI_PROVIDER env var
        Defaults to 'gemini' if not set
    """
    provider = get_env_value("AI_PROVIDER", _DEFAULT_AI_PROVIDER).lower()
    return provider if provider in _VALID_AI_PROVIDERS else _DEFAULT_AI_PROVIDER


def get_runtime_ai_provider() -> str:
    """
    Get the AI provider for runtime usage.

    Prioritizes Streamlit Session State -> App Settings Store -> Env.
    """
    # Check Streamlit Session State (Hot switch)
    try:
        import streamlit as st
        # Verify we are running in streamlit context
        if hasattr(st, "session_state") and "ai_provider" in st.session_state:
            override = st.session_state["ai_provider"]
            if override in _VALID_AI_PROVIDERS:
                return override
    except ImportError:
       pass
    except Exception:
        # e.g. run outside of streamlit context
        pass
        
    try:
        from chatbot_mvp.services.app_settings_store import get_provider_override
    except Exception:
        return get_ai_provider()
    override = get_provider_override()
    return override if override else get_ai_provider()


def is_demo_mode() -> bool:
    """
    Check if demo mode is enabled.
    
    Note: This is now independent of AI provider.
    Demo mode controls UI features (like gallery, admin links)
    while AI provider controls which chat backend to use.
    
    Returns:
        True if demo mode is enabled
    """
    value = get_env_value("DEMO_MODE")
    if value == "":
        return True
    return value.strip().lower() in _TRUE_VALUES


def is_openai_mode() -> bool:
    """Check if OpenAI is configured as the AI provider."""
    return get_runtime_ai_provider() == "openai"


def is_gemini_mode() -> bool:
    """Check if Gemini is configured as the AI provider."""
    return get_runtime_ai_provider() == "gemini"


def get_admin_password() -> str:
    """
    Get the admin password from environment.
    
    Returns:
        Admin password string or empty string if not set
    """
    value = get_env_value("ADMIN_PASSWORD")
    if value == "":
        return "123" if is_demo_mode() else ""
    return value
