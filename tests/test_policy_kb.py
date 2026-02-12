from chatbot_mvp.knowledge.policy_kb import parse_policy


def test_parse_policy_splits_by_articulo():
    text = (
        "ART\u00cdCULO 1 - Regalos\n"
        "No se pueden aceptar regalos de clientes.\n\n"
        "Art\u00edculo 2 - Conflictos\n"
        "Se deben declarar posibles conflictos de interes."
    )

    chunks = parse_policy(text)

    assert len(chunks) == 2
    assert chunks[0]["article_id"] == "1"
    assert chunks[1]["article_id"] == "2"
    assert chunks[0]["source_label"] == "Articulo 1"
    assert "No se pueden aceptar regalos" in chunks[0]["text"]
