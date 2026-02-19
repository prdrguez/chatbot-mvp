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


def _source_label(source: dict) -> str:
    kb_name = str(source.get("kb_name", "")).strip()
    section = str(source.get("section", "")).strip()
    if kb_name and section:
        return f"{kb_name} | {section}"
    return kb_name or section


def test_kb_grounding_injects_context_and_sources():
    fake = FakeAIClient()
    service = ChatService(ai_client=fake)
    kb_text = (
        "ARTICULO 3 Valores fundamentales\n"
        "La organizacion define transparencia y eficacia como valores centrales."
    )

    response = service.send_message(
        message="cuales son los valores fundamentales?",
        conversation_history=[],
        user_context={
            "kb_text": kb_text,
            "kb_name": "politica.txt",
            "kb_mode": "strict",
        },
    )

    assert fake.call_count == 1
    assert "Base de Conocimiento: politica.txt" in fake.last_message
    assert "Articulo 3" in fake.last_message
    assert fake.last_user_context.get("kb_strict_mode") is True
    assert response == "Respuesta basada en evidencia."
    debug_payload = service.get_last_kb_debug()
    sources = list(debug_payload.get("sources", []))
    assert sources
    assert sources[0].get("kb_name") == "politica.txt"
    assert "Articulo 3" in str(sources[0].get("section", ""))


def test_kb_grounding_returns_strict_message_without_evidence_and_without_sources():
    fake = FakeAIClient()
    service = ChatService(ai_client=fake)
    kb_text = (
        "ARTICULO 10 Integridad\n"
        "La organizacion promueve la integridad en todas sus operaciones."
    )

    response = service.send_message(
        message="que dice sobre viajes espaciales?",
        conversation_history=[],
        user_context={
            "kb_text": kb_text,
            "kb_name": "politica.txt",
            "kb_mode": "strict",
        },
    )

    assert fake.call_count == 0
    assert response.startswith("No encuentro eso en el documento cargado.")
    debug_payload = service.get_last_kb_debug()
    assert not debug_payload.get("sources")


def test_kb_grounding_stream_strict_without_evidence_skips_provider():
    fake = FakeAIClient()
    service = ChatService(ai_client=fake)
    kb_text = (
        "ARTICULO 10 Integridad\n"
        "La organizacion promueve la integridad en todas sus operaciones."
    )

    stream = service.send_message_stream(
        message="que dice sobre la nba?",
        conversation_history=[],
        user_context={
            "kb_text": kb_text,
            "kb_name": "politica.txt",
            "kb_mode": "strict",
        },
    )
    response = "".join(stream)

    assert fake.call_count == 0
    assert response.startswith("No encuentro eso en el documento cargado.")


def test_kb_grounding_returns_strict_message_with_empty_kb():
    fake = FakeAIClient()
    service = ChatService(ai_client=fake)

    response = service.send_message(
        message="que dice sobre regalos?",
        conversation_history=[],
        user_context={
            "kb_text": "",
            "kb_name": "politica.txt",
            "kb_mode": "strict",
        },
    )

    assert fake.call_count == 0
    assert response.startswith("No encuentro eso en el documento cargado.")


def test_kb_general_mode_allows_fallback_without_evidence():
    fake = FakeAIClient()
    service = ChatService(ai_client=fake)
    kb_text = (
        "ARTICULO 10 Integridad\n"
        "La organizacion promueve la integridad en todas sus operaciones."
    )

    response = service.send_message(
        message="que dice sobre viajes espaciales?",
        conversation_history=[],
        user_context={
            "kb_text": kb_text,
            "kb_name": "politica.txt",
            "kb_mode": "general",
        },
    )

    assert fake.call_count == 1
    assert response == "Respuesta basada en evidencia."
    debug_payload = service.get_last_kb_debug()
    assert not debug_payload.get("sources")


def test_kb_general_mode_with_evidence_adds_structured_sources():
    fake = FakeAIClient()
    service = ChatService(ai_client=fake)
    kb_text = (
        "ARTICULO 2 Teletrabajo flexible\n"
        "El trabajo remoto se permite dos veces por semana."
    )

    response = service.send_message(
        message="se permite el trabajo remoto?",
        conversation_history=[],
        user_context={
            "kb_text": kb_text,
            "kb_name": "politica.txt",
            "kb_mode": "general",
        },
    )

    assert fake.call_count == 1
    assert response == "Respuesta basada en evidencia."
    debug_payload = service.get_last_kb_debug()
    sources = list(debug_payload.get("sources", []))
    assert sources
    assert all(isinstance(item, dict) for item in sources)


def test_kb_mode_legacy_strict_label_normalizes_to_strict():
    fake = FakeAIClient()
    service = ChatService(ai_client=fake)
    kb_text = (
        "ARTICULO 7 Integridad\n"
        "La organizacion protege la integridad de la informacion."
    )

    response = service.send_message(
        message="que es la nba?",
        conversation_history=[],
        user_context={
            "kb_text": kb_text,
            "kb_name": "politica.txt",
            "kb_mode": "Solo KB (estricto)",
        },
    )

    assert fake.call_count == 0
    assert response.startswith("No encuentro eso en el documento cargado.")


def test_kb_mode_unknown_value_falls_back_to_general():
    fake = FakeAIClient()
    service = ChatService(ai_client=fake)
    kb_text = (
        "ARTICULO 7 Integridad\n"
        "La organizacion protege la integridad de la informacion."
    )

    response = service.send_message(
        message="que es la nba?",
        conversation_history=[],
        user_context={
            "kb_text": kb_text,
            "kb_name": "politica.txt",
            "kb_mode": "modo-raro",
        },
    )

    assert fake.call_count == 1
    assert response == "Respuesta basada en evidencia."


def test_kb_query_with_synonym_like_wording_retrieves_heading():
    fake = FakeAIClient()
    service = ChatService(ai_client=fake)
    kb_text = (
        "1. Teletrabajo flexible\n"
        "El trabajo remoto se permite con aprobacion del lider.\n\n"
        "2. Acceso fisico\n"
        "El ingreso a edificios requiere credencial."
    )

    response = service.send_message(
        message="se puede teletrabajar los viernes?",
        conversation_history=[],
        user_context={
            "kb_text": kb_text,
            "kb_name": "politica.txt",
            "kb_mode": "strict",
        },
    )

    assert fake.call_count == 1
    assert response == "Respuesta basada en evidencia."
    debug_payload = service.get_last_kb_debug()
    assert "teletrabajo" in str(debug_payload.get("query_expanded", ""))
    assert debug_payload.get("retrieval_method") == "hybrid"
    assert debug_payload.get("sources")


def test_kb_debug_chunks_are_coherent_with_structured_sources():
    fake = FakeAIClient()
    service = ChatService(ai_client=fake)
    kb_text = (
        "1. Teletrabajo flexible\n"
        "El trabajo remoto se permite con aprobacion del lider."
    )

    response = service.send_message(
        message="se permite teletrabajar?",
        conversation_history=[],
        user_context={
            "kb_text": kb_text,
            "kb_name": "politica.txt",
            "kb_mode": "strict",
        },
    )

    assert response == "Respuesta basada en evidencia."
    debug_payload = service.get_last_kb_debug()
    debug_rows = list(debug_payload.get("chunks", []))
    debug_sources = [str(row.get("source", "")).strip() for row in debug_rows if isinstance(row, dict)]
    assert debug_sources

    source_rows = [row for row in debug_payload.get("sources", []) if isinstance(row, dict)]
    assert source_rows
    source_labels = [_source_label(row) for row in source_rows]
    assert source_labels == debug_sources[: len(source_labels)]
