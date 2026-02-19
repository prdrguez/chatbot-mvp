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
- Se deduplica por `chunk_id` y se aplica `top_k` + `min_score`.
- Debug guarda `chunks_final` con score y breakdown por senal.

### Chunking y stitching para KB grandes
- El parser prioriza separacion por headings + parrafos (doble salto de linea), evitando cortes duros por caracteres.
- Los chunks se arman por parrafos con target aproximado de 900-1400 chars (default 1100/1400).
- Se agrega overlap semantico al chunk siguiente (ultimo parrafo o ultimas oraciones) para evitar frases cortadas.
- Si un top match tiene senal fuerte (`heading`/`exact`/`strong_match`), se activa section stitching:
  - se agregan chunks contiguos de la misma seccion antes de construir contexto final,
  - respetando el presupuesto `kb_max_context_chars`.
- Debug de retrieval ahora incluye:
  - `chunks_added_by_stitching`
  - `stitching_added_count`
  - `context_chars_used` y `context_chars_budget`

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
- Para KB grandes (`kb_text_len > 40000`) se eleva el default de `kb_max_context_chars` a `6000` si el usuario no lo personalizo.
- En modo KB con Groq se eleva `max_tokens` por defecto a `700` (configurable por contexto interno, sin UI nueva).

### Limite de tamano KB en Admin
- Se agrega `KB_MAX_CHARS` con default `120000`.
- Si el archivo supera el limite, se trunca de forma controlada y se marca `kb_truncated=True`.
- Admin muestra tamaño actual, limite y advertencia persistente recomendando subir una version resumida.

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
