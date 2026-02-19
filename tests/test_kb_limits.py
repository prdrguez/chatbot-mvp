from chatbot_mvp.services.kb_limits import (
    KB_MAX_CHARS,
    apply_kb_limit_to_session,
    limit_kb_text_size,
)


def test_limit_kb_text_size_truncates_text_when_exceeds_max_chars():
    text = "A" * (KB_MAX_CHARS + 77)

    result = limit_kb_text_size(text)

    assert result["truncated"] is True
    assert result["original_chars"] == KB_MAX_CHARS + 77
    assert result["used_chars"] == KB_MAX_CHARS
    assert len(result["text"]) == KB_MAX_CHARS


def test_apply_kb_limit_to_session_sets_flag_and_char_metadata():
    session_state = {}
    text = "B" * (KB_MAX_CHARS + 12)

    limited_text = apply_kb_limit_to_session(session_state, text)

    assert len(limited_text) == KB_MAX_CHARS
    assert session_state["kb_truncated"] is True
    assert session_state["kb_original_chars"] == KB_MAX_CHARS + 12
    assert session_state["kb_max_chars"] == KB_MAX_CHARS
