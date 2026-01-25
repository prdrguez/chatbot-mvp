import time

from chatbot_mvp.state.auth_state import AuthState


def test_logout_clears_state():
    state = AuthState()
    state.is_authenticated = True
    state.login_time = time.time()
    state.auth_error = "error"
    state.password_input = "secret"
    state.login_attempt_count = 2

    state.logout()

    assert state.is_authenticated is False
    assert state.login_time == 0.0
    assert state.auth_error == ""
    assert state.password_input == ""
    assert state.login_attempt_count == 0


def test_check_session_expires():
    state = AuthState()
    state.is_authenticated = True
    state.session_timeout = 1
    state.login_time = time.time() - 10

    state.check_session()

    assert state.is_authenticated is False
