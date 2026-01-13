import os


_TRUE_VALUES = {"1", "true", "yes", "on"}


def is_demo_mode() -> bool:
    value = os.getenv("DEMO_MODE")
    if value is None:
        return True
    return value.strip().lower() in _TRUE_VALUES
