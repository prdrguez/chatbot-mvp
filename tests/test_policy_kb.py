from chatbot_mvp.knowledge.policy_kb import (
    KB_MODE_GENERAL,
    KB_MODE_STRICT,
    build_bm25_index,
    normalize_kb_mode,
    parse_policy,
    retrieve,
)


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


def test_parse_policy_splits_by_numbered_sections_when_no_articulo():
    text = (
        "1. Valores\n"
        "Transparencia y eficacia.\n\n"
        "2. Obsequios\n"
        "Los regalos deben declararse."
    )

    chunks = parse_policy(text)

    assert len(chunks) == 2
    assert chunks[0]["section_id"] == "1"
    assert chunks[1]["section_id"] == "2"
    assert chunks[0]["source_label"].startswith("Seccion 1")


def test_policy_kb_retrieval_finds_securion_term():
    text = (
        "CAPITULO I\n"
        "Securion es una empresa orientada a ciberseguridad.\n\n"
        "ARTICULO 4\n"
        "Se deben declarar regalos de clientes."
    )
    chunks = parse_policy(text)
    index = build_bm25_index(chunks)
    results = retrieve("Que es Securion?", index, chunks, k=3)

    assert results
    assert "securion" in results[0]["text"].lower()
    assert float(results[0].get("score", 0.0)) > 0


def test_normalize_kb_mode():
    assert normalize_kb_mode(KB_MODE_GENERAL) == KB_MODE_GENERAL
    assert normalize_kb_mode(KB_MODE_STRICT) == KB_MODE_STRICT
    assert normalize_kb_mode("Solo KB (estricto)") == KB_MODE_GENERAL
