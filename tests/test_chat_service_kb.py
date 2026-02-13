from chatbot_mvp.services.chat_service import ChatService


class FakeAIClient:
    def __init__(self):
        self.last_message = ""
        self.last_user_context = None
        self.call_count = 0

    def generate_chat_response(
        self, message, conversation_history, user_context=None, **kwargs
    ):
        self.call_count += 1
        self.last_message = message
        self.last_user_context = user_context or {}
        return "Respuesta basada en evidencia."

    def generate_chat_response_stream(
        self, message, conversation_history, user_context=None, **kwargs
    ):
        self.call_count += 1
        self.last_message = message
        self.last_user_context = user_context or {}
        yield "Respuesta basada en evidencia."


def test_kb_grounding_injects_context_and_sources():
    fake = FakeAIClient()
    service = ChatService(ai_client=fake)
    kb_text = (
        "ARTICULO 3 Valores fundamentales\n"
        "Los valores fundamentales de Securion son transparencia y eficacia."
    )

    response = service.send_message(
        message="Cuales son los valores fundamentales de Securion?",
        conversation_history=[],
        user_context={
            "kb_text": kb_text,
            "kb_name": "securin.txt",
            "kb_mode": "strict",
        },
    )

    assert fake.call_count == 1
    assert "Base de Conocimiento: securin.txt" in fake.last_message
    assert "Fuente: Articulo 3" in fake.last_message
    assert fake.last_user_context.get("kb_strict_mode") is True
    assert "Fuentes:" in response
    assert "Articulo 3" in response


def test_kb_grounding_returns_strict_message_without_evidence():
    fake = FakeAIClient()
    service = ChatService(ai_client=fake)
    kb_text = (
        "ARTICULO 10 Integridad\n"
        "Securion promueve la integridad en todas sus operaciones."
    )

    response = service.send_message(
        message="Que dice sobre viajes espaciales?",
        conversation_history=[],
        user_context={
            "kb_text": kb_text,
            "kb_name": "securin.txt",
            "kb_mode": "strict",
        },
    )

    assert fake.call_count == 0
    assert response.startswith("No encuentro eso en la pol")


def test_kb_grounding_returns_strict_message_with_empty_kb():
    fake = FakeAIClient()
    service = ChatService(ai_client=fake)

    response = service.send_message(
        message="Que dice sobre regalos?",
        conversation_history=[],
        user_context={
            "kb_text": "",
            "kb_name": "securin.txt",
            "kb_mode": "strict",
        },
    )

    assert fake.call_count == 0
    assert response.startswith("No encuentro eso en la pol")


def test_kb_general_mode_allows_fallback_without_evidence():
    fake = FakeAIClient()
    service = ChatService(ai_client=fake)
    kb_text = (
        "ARTICULO 10 Integridad\n"
        "Securion promueve la integridad en todas sus operaciones."
    )

    response = service.send_message(
        message="Que dice sobre viajes espaciales?",
        conversation_history=[],
        user_context={
            "kb_text": kb_text,
            "kb_name": "securin.txt",
            "kb_mode": "general",
        },
    )

    assert fake.call_count == 1
    assert response == "Respuesta basada en evidencia."
