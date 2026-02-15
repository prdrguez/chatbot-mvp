from pathlib import Path

from chatbot_mvp.knowledge import load_kb as public_load_kb
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
    assert normalize_kb_mode("Solo KB (estricto)") == KB_MODE_STRICT
    assert normalize_kb_mode("modo-invalido") == KB_MODE_GENERAL


def test_retrieve_securion_with_real_kb():
    kb_path = Path(__file__).resolve().parents[1] / "docs" / "securin.txt"
    text = kb_path.read_text(encoding="utf-8")
    chunks = parse_policy(text)
    index = build_bm25_index(chunks)

    results = retrieve("Cuales son los valores del Grupo Securion?", index, chunks, k=4)

    assert results
    assert any("securion" in str(item.get("text", "")).lower() for item in results)


def test_public_load_kb_accepts_kb_updated_at_kwarg():
    bundle = public_load_kb(
        text="Politica de prueba",
        name="test.txt",
        kb_updated_at="2026-02-13T00:00:00Z",
    )

    assert isinstance(bundle, dict)
    assert bundle.get("kb_name") == "test.txt"
    assert bundle.get("kb_updated_at") == "2026-02-13T00:00:00Z"


def test_public_load_kb_infers_primary_entity():
    bundle = public_load_kb(
        text=(
            "Codigo Etico Grupo Securion\n"
            "Securion define principios de cumplimiento.\n"
            "Securion aplica controles internos."
        ),
        name="securin.txt",
    )

    assert bundle.get("kb_primary_entity") == "Securion"
