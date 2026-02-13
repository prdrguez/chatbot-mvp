from chatbot_mvp.services import chat_service
from chatbot_mvp.services.chat_service import ChatService, STRICT_NO_EVIDENCE_RESPONSE


class DummyAIClient:
    def __init__(self, response: str = "respuesta"):
        self.response = response
        self.calls = 0

    def generate_chat_response(
        self,
        message,
        conversation_history,
        user_context=None,
        max_tokens=150,
        temperature=0.7,
    ):
        self.calls += 1
        return self.response

    def generate_chat_response_stream(
        self,
        message,
        conversation_history,
        user_context=None,
        max_tokens=150,
        temperature=0.7,
    ):
        self.calls += 1
        yield self.response


def test_chat_service_strict_mode_no_evidence(monkeypatch):
    monkeypatch.setattr(chat_service, "get_runtime_ai_provider", lambda: "openai")
    ai_client = DummyAIClient(response="esto no deberia usarse")
    service = ChatService(ai_client=ai_client)

    response = service.send_message(
        message="Que dice sobre vacaciones ilimitadas?",
        conversation_history=[],
        user_context={
            "kb_name": "securin.txt",
            "kb_mode": "strict",
            "kb_text": "Articulo 1. Regalos: no se aceptan regalos de clientes.",
        },
    )

    assert response == STRICT_NO_EVIDENCE_RESPONSE
    assert ai_client.calls == 0


def test_chat_service_general_mode_allows_general(monkeypatch):
    monkeypatch.setattr(chat_service, "get_runtime_ai_provider", lambda: "openai")
    ai_client = DummyAIClient(response="Respuesta general del asistente.")
    service = ChatService(ai_client=ai_client)

    response = service.send_message(
        message="Hola, como estas?",
        conversation_history=[],
        user_context={"kb_mode": "general"},
    )

    assert response == "Respuesta general del asistente."
    assert ai_client.calls == 1


def test_chat_service_adds_sources_when_kb_matches(monkeypatch):
    monkeypatch.setattr(chat_service, "get_runtime_ai_provider", lambda: "openai")
    ai_client = DummyAIClient(response="Segun la politica, no se permiten regalos.")
    service = ChatService(ai_client=ai_client)

    response = service.send_message(
        message="Se pueden recibir regalos de clientes?",
        conversation_history=[],
        user_context={
            "kb_name": "securin.txt",
            "kb_mode": "general",
            "kb_text": "Articulo 4. Regalos: no se permiten regalos de clientes.",
        },
    )

    assert "Fuentes:" in response
    assert ai_client.calls == 1
