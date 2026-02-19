from chatbot_mvp.services.kb_sources import (
    KB_SOURCES_MAX,
    MAX_ITEM_LEN,
    build_compact_sources_view,
    compact_kb_name,
    compact_section_label,
)


def test_compact_section_label_reduces_long_section_with_part():
    section = "Seccion 4 - ## Matriz de riesgos y mitigaciones (parte 1/3) {#abc}"

    compact = compact_section_label(section)

    assert compact == "§4 Matriz riesgos (1/3)"


def test_build_compact_sources_view_limits_items_and_dedupes_by_best_score():
    sources = [
        {
            "kb_name": "Jano_by_Iguales_argentina_final_sin_lineas_violetas.docx.md",
            "section": "Seccion 4 - ## Matriz de riesgos y mitigaciones (parte 1/3)",
            "part": "1/3",
            "score": 0.61,
            "method": "hybrid:heading+overlap",
        },
        {
            "kb_name": "Jano_by_Iguales_argentina_final_sin_lineas_violetas.docx.md",
            "section": "Seccion 4 - ## Matriz de riesgos y mitigaciones (parte 1/3)",
            "part": "1/3",
            "score": 0.89,
            "method": "hybrid:heading+exact",
        },
        {
            "kb_name": "politica_larguisima_de_prueba.txt",
            "section": "Seccion 5 - Implementacion y monitoreo continuo (parte 2/4)",
            "part": "2/4",
            "score": 0.5,
            "method": "hybrid:overlap",
        },
        {
            "kb_name": "politica_otra_larga.md",
            "section": "Seccion 6 - Evidencia y auditoria",
            "part": "",
            "score": 0.4,
            "method": "hybrid:fuzzy",
        },
        {
            "kb_name": "politica_extra.md",
            "section": "Seccion 7 - Riesgos residuales",
            "part": "",
            "score": 0.2,
            "method": "hybrid:bm25",
        },
    ]

    compact = build_compact_sources_view(
        sources=sources,
        max_sources=KB_SOURCES_MAX,
        max_item_len=MAX_ITEM_LEN,
    )

    line = str(compact.get("line", ""))
    compact_rows = list(compact.get("compact_rows", []))
    hidden_rows = list(compact.get("hidden_rows", []))

    assert line.startswith("Fuentes:")
    assert len(compact_rows) == KB_SOURCES_MAX
    assert len(hidden_rows) >= 2
    assert ".md" in line
    assert "[4]" not in line

    best_duplicate = compact_rows[0]
    assert float(best_duplicate.get("score", 0.0)) >= 0.89
    assert len(str(best_duplicate.get("compact", ""))) <= MAX_ITEM_LEN


def test_compact_kb_name_preserves_extension_tail():
    compact = compact_kb_name(
        "Jano_by_Iguales_argentina_final_sin_lineas_violetas_version_extendida.docx.md"
    )

    assert compact.endswith(".md")
    assert len(compact) <= 28
