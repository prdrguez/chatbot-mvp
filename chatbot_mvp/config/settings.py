import os


_TRUE_VALUES = {"1", "true", "yes", "on"}


def get_ai_provider() -> str:
    """
    Get the configured AI provider.
    
    Returns:
        'demo', 'openai', or 'gemini' based on AI_PROVIDER env var
        Defaults to 'demo' if not set
    """
    provider = os.getenv("AI_PROVIDER", "demo").strip().lower()
    valid_providers = {"demo", "openai", "gemini"}
    return provider if provider in valid_providers else "demo"


def is_demo_mode() -> bool:
    """
    Check if demo mode is enabled.
    
    Note: This is now independent of AI provider.
    Demo mode controls UI features (like gallery, admin links)
    while AI provider controls which chat backend to use.
    
    Returns:
        True if demo mode is enabled
    """
    value = os.getenv("DEMO_MODE")
    if value is None:
        return True
    return value.strip().lower() in _TRUE_VALUES


def is_openai_mode() -> bool:
    """Check if OpenAI is configured as the AI provider."""
    return get_ai_provider() == "openai"


def is_gemini_mode() -> bool:
    """Check if Gemini is configured as the AI provider."""
    return get_ai_provider() == "gemini"


def get_admin_password() -> str:
    """
    Get the admin password from environment.
    
    Returns:
        Admin password string or empty string if not set
    """
    return os.getenv("ADMIN_PASSWORD", "").strip()
