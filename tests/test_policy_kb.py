from chatbot_mvp.knowledge import load_kb as public_load_kb
from chatbot_mvp.knowledge.policy_kb import (
    KB_MODE_GENERAL,
    KB_MODE_STRICT,
    build_bm25_index,
    expand_query_with_kb,
    get_last_kb_debug,
    normalize_kb_mode,
    parse_policy,
    retrieve,
)


def _build_large_brechas_fixture() -> str:
    intro = (
        "## La necesidad social y tecnologica que motivo su creacion\n"
        "Este apartado describe por que se diseña Jano y cuales son los limites actuales del ecosistema."
    )
    brecha_1 = (
        "1. Brecha de acceso: comunidades con conectividad inestable quedan fuera de servicios "
        "digitales esenciales y no logran sostener acompanamiento continuo."
    )
    brecha_2 = (
        "2. Brecha de alfabetizacion tecnologica: muchas personas usuarias requieren mediacion permanente "
        "porque los flujos de atencion se presentan con lenguaje tecnico, requisitos cambiantes y tramites "
        "fragmentados entre distintas instituciones que no comparten criterios de prioridad."
    )
    relleno = "\n\n".join(
        [
            (
                "Detalle operativo A: se documentan casos, actores, tiempos y fricciones de implementacion "
                "para sostener acompanamiento continuo en equipos interdisciplinarios y evitar respuestas "
                "fragmentadas frente a situaciones de alta vulnerabilidad social."
            ),
            (
                "Detalle operativo B: se consolidan trayectorias de atencion, reglas de priorizacion y "
                "mecanismos de derivacion entre equipos para reducir perdida de contexto en procesos largos."
            ),
            (
                "Detalle operativo C: se releva informacion historica de intervenciones previas para "
                "conservar continuidad institucional, evitar duplicaciones y sostener seguimiento "
                "longitudinal de cada caso."
            ),
        ]
    )
    brecha_3 = (
        "3. Brecha de confianza institucional: aparece temor constante ante la falta de trazabilidad, "
        "sin claridad sobre quien decide, como se corrigen errores y que vias de reclamo existen cuando "
        "la respuesta automatizada no contempla la situacion real."
    )
    cierre = (
        "Este bloque finaliza proponiendo mejoras de coordinacion para equipos sociales y tecnicos."
    )
    return "\n\n".join([intro, brecha_1, brecha_2, relleno, brecha_3, cierre])


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


def test_retrieve_stitches_contiguous_section_chunks_for_large_heading_match():
    text = _build_large_brechas_fixture()
    chunks = parse_policy(text)
    index = build_bm25_index(chunks)

    results = retrieve(
        "cual es la necesidad social y tecnologica?",
        index,
        chunks,
        k=1,
        min_score=0.05,
        max_context_chars=6000,
    )

    assert results
    combined_context = "\n".join(str(row.get("text", "")) for row in results)
    assert "Brecha de acceso" in combined_context
    assert "Brecha de alfabetizacion tecnologica" in combined_context
    assert "Brecha de confianza institucional" in combined_context

    debug = get_last_kb_debug()
    assert int(debug.get("stitching_added_count", 0)) >= 1
    assert int(debug.get("context_chars_used", 0)) > 0

