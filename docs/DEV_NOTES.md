# DEV NOTES

Notas tecnicas vigentes del repo.

## Estado actual (runtime)
- Stack productivo: Python + Streamlit.
- Entry point: `streamlit_app/Inicio.py`.
- UI multipage en `streamlit_app/`.
- Logica de negocio en `chatbot_mvp/`.

## Paginas activas
- `streamlit_app/Inicio.py`
- `streamlit_app/pages/1_Evaluacion.py`
- `streamlit_app/pages/2_Chat.py`
- `streamlit_app/pages/3_Admin.py`

## Providers
- Default: Gemini.
- Selector en Admin: solo `gemini` y `groq`.
- Persistencia de override: `chatbot_mvp/data/app_settings.json`.
- `demo` existe y se usa como fallback.
- `openai` existe en config/env pero no esta conectado end-to-end en UI actual.

## Base de Conocimiento (KB)
- Carga desde Admin (`.txt`, `.md`, un archivo por vez).
- Runtime en `st.session_state` (`kb_text`, `kb_name`, `kb_chunks`, `kb_index`, etc.).
- Modo `general` y `strict`.
- Debug opcional de retrieval visible en Chat.

### KB-driven query expansion (agnostico al dominio)
- El retrieval aplica expansion de query sin LLM, derivada del documento cargado.
- `policy_kb.build_bm25_index` construye un indice enriquecido con:
  - `section_titles_normalized`: titulos/secciones normalizados del documento.
  - `vocab_terms`: terminos frecuentes + bigrams/trigrams del propio KB.
  - `cooc_map`: terminos relacionados por co-ocurrencia en ventana local.
- `policy_kb.expand_query_with_kb` agrega terminos a la consulta y guarda notas de origen:
  - `heading_match`
  - `fuzzy_heading`
  - `vocab`
  - `cooc`
- La query expandida y sus notas quedan en debug (`query_expanded`, `expansion_notes`).

### Retrieval hibrido unificado
- `policy_kb.retrieve` siempre usa un pipeline `hybrid` y devuelve un unico resultado final.
- Score final por chunk:
  - `bm25_norm`
  - `overlap_norm`
  - `exact_bonus`
  - `heading_bonus`
  - `fuzzy_bonus`
- Se deduplica por `section_id`/`chunk_id` y se aplica `top_k` + `min_score`.
- Debug guarda `chunks_final` con score y breakdown por senal.

### Evidencia suficiente (criterio generico)
- `ChatService` evalua evidencia sin reglas tematicas hardcodeadas:
  - pasa si hay `strong_match` y score tope razonable, o
  - suma de scores altos en top chunks, o
  - score tope alto por si solo.
- `Strict`:
  - si no hay evidencia suficiente: respuesta fija y sin `Fuentes`.
  - no llama provider.
- `General`:
  - con evidencia suficiente: grounded + `Fuentes`.
  - sin evidencia suficiente: responde normal sin `Fuentes`.

### Knobs runtime (en user_context)
- `kb_top_k`: maximo de chunks candidatos.
- `kb_min_score`: corte minimo de score en retrieval.
- `kb_max_context_chars`: presupuesto maximo de contexto inyectado.
- Si no se proveen, se aplican defaults en `ChatService`.

## Persistencia de datos
- Evaluaciones: `data/submissions.jsonl`.
- Override provider: `chatbot_mvp/data/app_settings.json`.

## Testing
- Suite principal: `python -m pytest`.
- Existe un test legacy de Reflex marcado como skipped (`tests/test_auth_state.py`).

## Legacy (Reflex)
El runtime actual no usa Reflex.

Restos legacy que aun existen en repo:
- `chatbot_mvp/components/` (archivos con dependencias historicas de Reflex)
- `.states/` (cache/artefactos legacy)
- `tests/test_auth_state.py` (skippeado)

Mantener estas referencias solo como contexto historico hasta su limpieza definitiva.
