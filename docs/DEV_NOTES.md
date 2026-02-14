# DEV NOTES

Notas tecnicas vigentes del repo.

## Estado actual (runtime)
- Stack productivo: Python + Streamlit.
- Entry point: `streamlit_app/Inicio.py`.
- UI multipage en `streamlit_app/`.
- Logica de negocio en `chatbot_mvp/`.

## KB grounding (diseno actual)

### Objetivo
Evitar recomputar chunking/indice en cada mensaje y mejorar precision sin embeddings.

### Indexado
- Archivo: `chatbot_mvp/knowledge/policy_kb.py`.
- `build_kb_index(text, kb_name, kb_updated_at)`:
  - Parsea la politica en chunks.
  - Normaliza `source_label` y metadatos (`id`, `title`, `article_id`, `section_id`).
  - Construye indice BM25-like liviano (puro Python):
    - `tf_docs`, `df`, `doc_len`, `avgdl`, `normalized_texts`.
  - Aplica bonus por match exacto de query normalizada dentro del chunk.
- Cache:
  - `@st.cache_data` por `kb_hash + kb_updated_at`.
  - Evita reconstruccion del indice mientras no cambie la KB.

### Retrieval
- `retrieve_evidence(query, index, top_k, min_score)`.
- Tokenizacion simple (lower + non-alnum split + stopwords ES/EN).
- Scoring BM25-like (`k1=1.5`, `b=0.75`) + bonus exacto.
- Filtra por `min_score` y retorna `top_k` evidencias.
- Debug guarda top candidatos con `score`, `section`, `preview`.

## Integracion Streamlit

### Admin
- Archivo: `streamlit_app/pages/3_Admin.py`.
- Al cargar KB:
  - Guarda `kb_name`, `kb_text`, `kb_updated_at`, `kb_hash`.
  - Construye y persiste `kb_index` + `kb_chunks` en `st.session_state`.
- Config KB expuesta en UI:
  - `Top K`
  - `Score minimo`
  - `Max chars contexto`
- Muestra `Index builds (cache miss)` para validar que no recompone por mensaje.

### Chat
- Archivo: `streamlit_app/pages/2_Chat.py`.
- Envia al servicio:
  - `kb_index` ya construido
  - `kb_top_k`, `kb_min_score`, `kb_max_context_chars`
- Debug expander muestra query, razon, score, seccion, preview e `index_build_count`.

## Servicio de chat
- Archivo: `chatbot_mvp/services/chat_service.py`.
- `strict`:
  - Sin evidencia suficiente: respuesta fija y no llamada al provider.
- `general`:
  - Si hay evidencia: inyecta contexto KB con limite de chars/chunks.
  - Si no hay evidencia: fallback normal al provider.
- Post-proceso:
  - Si se uso KB, agrega siempre `Fuentes: ...` desde sistema.

## Providers
- Default: Gemini.
- Selector Admin: `gemini` y `groq`.
- `demo` permanece como fallback.
- `openai` existe en config/env, sin conexion end-to-end en UI actual.

## Testing
- Suite principal: `python -m pytest`.
- Estado actual: `25 passed, 1 skipped`.
- Skip legacy: `tests/test_auth_state.py` (Reflex historico).

## Legacy (Reflex)
El runtime actual no usa Reflex.

Restos legacy que aun existen en repo:
- `chatbot_mvp/components/`
- `.states/`
- `tests/test_auth_state.py`

Mantener solo como referencia historica hasta limpieza definitiva.
