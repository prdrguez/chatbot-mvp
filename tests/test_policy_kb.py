from chatbot_mvp.knowledge import load_kb as public_load_kb
from chatbot_mvp.knowledge.policy_kb import (
    KB_MODE_GENERAL,
    KB_MODE_STRICT,
    build_bm25_index,
    expand_query_with_kb,
    normalize_kb_mode,
    parse_policy,
    retrieve,
)


def test_parse_policy_splits_by_articulo():
    text = (
        "ARTICULO 1 - Regalos\n"
        "No se pueden aceptar regalos de clientes.\n\n"
        "Articulo 2 - Conflictos\n"
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


def test_normalize_kb_mode():
    assert normalize_kb_mode(KB_MODE_GENERAL) == KB_MODE_GENERAL
    assert normalize_kb_mode(KB_MODE_STRICT) == KB_MODE_STRICT
    assert normalize_kb_mode("Solo KB (estricto)") == KB_MODE_STRICT
    assert normalize_kb_mode("modo-invalido") == KB_MODE_GENERAL


def test_public_load_kb_accepts_kb_updated_at_kwarg():
    bundle = public_load_kb(
        text="Politica de prueba",
        name="test.txt",
        kb_updated_at="2026-02-16T00:00:00Z",
    )

    assert isinstance(bundle, dict)
    assert bundle.get("kb_name") == "test.txt"
    assert bundle.get("kb_updated_at") == "2026-02-16T00:00:00Z"


def test_expand_query_with_kb_uses_heading_and_fuzzy():
    text = (
        "1. Teletrabajo flexible\n"
        "El trabajo remoto se permite con aprobacion del lider.\n\n"
        "2. Licencias\n"
        "Las licencias especiales se revisan caso por caso."
    )
    chunks = parse_policy(text)
    index = build_bm25_index(chunks)

    expanded = expand_query_with_kb("se puede teletrabajar los viernes?", index)

    assert "teletrabajo" in str(expanded.get("query_expanded", ""))
    notes = list(expanded.get("expansion_notes", []))
    assert notes
    assert any(
        str(note.get("source", "")) in {"heading_match", "fuzzy_heading", "cooc", "vocab"}
        for note in notes
        if isinstance(note, dict)
    )


def test_retrieve_indirect_query_hits_expected_section_and_debug():
    text = (
        "1. Teletrabajo flexible\n"
        "El trabajo remoto se permite con aprobacion del lider.\n\n"
        "2. Seguridad de datos\n"
        "El acceso debe protegerse con autenticacion multifactor."
    )
    chunks = parse_policy(text)
    index = build_bm25_index(chunks)

    results = retrieve(
        "politica para teletrabajar desde casa",
        index,
        chunks,
        k=3,
        min_score=0.05,
    )

    assert results
    assert any("Teletrabajo" in str(item.get("source_label", "")) for item in results)

