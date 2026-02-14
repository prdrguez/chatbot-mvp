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
