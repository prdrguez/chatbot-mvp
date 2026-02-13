# STATUS REPORT — Reflex → Streamlit

## Resumen ejecutivo (10 lineas)
- Repo activo en Streamlit con multipage en `streamlit_app/` (Inicio, Evaluacion, Chat, Admin).
- Entry point real es `streamlit_app/Inicio.py`; README y AGENTS.md ya estan alineados.
- Fuente de verdad: `docs/STATUS_REPORT.md` (STATUS duplicados removidos).
- Logica de negocio vive en `chatbot_mvp/` (config, services, data).
- Chat usa `ChatService` con streaming; proveedores: gemini/groq/openai (segun env).
- Chat soporta KB de politicas/protocolos cargada desde Admin (TXT/MD) con recuperacion BM25.
- Evaluacion es local con scoring y feedback estatico; persiste en `data/submissions.jsonl`.
- Admin lee submissions y genera dashboards con pandas/plotly; requiere `ADMIN_PASSWORD`.
- Tests corren: 7 passed, 1 skipped (legacy Reflex).
- No se encontraron scripts de build ni CI configurada.
- Quedan restos de Reflex: `chatbot_mvp/components`, `.states/`, docs/DEV_NOTES.

## Qué funciona hoy
- Navegacion multipage Streamlit implementada (Inicio, Evaluacion, Chat, Admin).
- Cuestionario usa `chatbot_mvp.data.juego_etico` y guarda resultados via `submissions_store`.
- Chat usa streaming con Gemini o Groq si hay API keys; el provider se elige en Admin.
- Chat puede usar una KB cargada para responder con evidencia y linea final de fuentes.
- Chat renderiza mensajes con flex left/right sin burbujas (usuario a la derecha).
- Admin autentica con password y muestra KPIs desde `data/submissions.jsonl`.
- Admin incluye seccion "Base de Conocimiento" para subir/limpiar politicas (`.txt`, `.md`).
- Estilos cargan desde `streamlit_app/assets/style.css`.

## Que NO funciona hoy
- Componentes Reflex importan modulos inexistentes (`chatbot_mvp.state`, `chatbot_mvp.ui`) y no son compatibles con Streamlit.
- Test legacy Reflex (`tests/test_auth_state.py`) esta skippeado (sin coverage real).
- `chatbot_mvp/data/app_settings.json` fija `groq` y puede sobreescribir `AI_PROVIDER`.

## Cómo correr local
- Requisitos:
  - Python 3.10+ (usa typing con `|`).
  - Paquetes en `requirements.txt`.
- Variables de entorno:
  - `AI_PROVIDER` (gemini|groq|openai|demo).
  - `GEMINI_API_KEY` o `GOOGLE_API_KEY` (si gemini).
  - `GEMINI_MAX_OUTPUT_TOKENS` (default: 280).
  - `GROQ_API_KEY` (si groq).
  - `GROQ_MODEL` (default: `openai/gpt-oss-20b`).
  - `OPENAI_API_KEY` (si openai).
  - `KB_TOP_K` (default: `4`).
  - `KB_MIN_SCORE_STRICT` (default: `0.35`).
  - `ADMIN_PASSWORD`, `DEMO_MODE`.
- Dependencias clave:
  - `google-genai` (Gemini), `openai` (Groq/OpenAI) y `rank-bm25` (retrieval KB).
- Datos/archivos requeridos:
  - `data/submissions.jsonl` (se crea automaticamente al guardar).
  - `chatbot_mvp/data/app_settings.json` (override de proveedor).
- Comando (real):
  - `streamlit run streamlit_app/Inicio.py`
- Notas de troubleshooting:
  - Si el chat no responde, validar API keys y `AI_PROVIDER`.
  - Si el proveedor no cambia, borrar `chatbot_mvp/data/app_settings.json` o usar el selector en Admin.
  - Si aparece "cannot import name genai from google", desinstalar el paquete `google` y reinstalar `google-genai`.
  - Si falta `openai`, instalar el SDK con `pip install openai`.
  - Si la respuesta dice "No encuentro eso en la politica cargada", revisar que la KB cargada tenga ese tema textual.
  - Si no se usa KB, verificar que Admin muestre `KB cargada: <nombre> (N caracteres)`.
  - Admin muestra toast y caption al cambiar provider.

## Base de Conocimiento (KB)
- Carga:
  - Se carga desde `streamlit_app/pages/3_Admin.py` con `st.file_uploader`.
  - Formatos soportados: `.txt` y `.md` (un archivo por vez).
  - Estado guardado en `st.session_state`: `kb_text`, `kb_name`, `kb_updated_at`.
- Parsing y chunking:
  - Si detecta `Articulo <n>` o `ARTICULO <n>`, separa por articulo y conserva `article_id`.
  - Si no detecta articulos, divide en fragmentos de aprox 1000 chars con overlap de 150.
- Retrieval:
  - Usa BM25 (`rank-bm25`) sobre chunks parseados.
  - Recupera `KB_TOP_K` fragmentos relevantes por query.
  - Cache: parseo y carga de KB con `st.cache_data`; indice BM25 con `st.cache_resource` (clave por hash de texto y `kb_updated_at`).
  - En modo estricto usa umbral configurable `KB_MIN_SCORE_STRICT`.
- Integracion en chat:
  - Con KB: inyecta bloque de contexto + instruccion estricta para responder solo con evidencia.
  - Sin KB: mantiene comportamiento actual sin cambios.
  - La respuesta final agrega `Fuentes: ...` con articulos/fragmentos usados.
- Limitaciones actuales:
  - Solo una KB activa por sesion.
  - Solo texto plano (`.txt`/`.md`), sin parser de PDF/DOCX.
  - Retrieval lexical (BM25), sin embeddings semanticos.

## Arquitectura actual
- Estructura (alto nivel):
  - `streamlit_app/`, `chatbot_mvp/`, `data/`, `tests/`, `docs/`, `exports/`, `.states/` (legacy).
- Entry point(s):
  - `streamlit_app/Inicio.py` (home).
  - `streamlit_app/pages/1_Evaluacion.py`, `2_Chat.py`, `3_Admin.py`.
- Módulos clave:
  - `chatbot_mvp/services/chat_service.py` (orquesta IA y streaming).
  - `chatbot_mvp/services/submissions_store.py` (persistencia y agregados).
  - `chatbot_mvp/config/settings.py` (env y defaults).
  - `chatbot_mvp/data/juego_etico.py` (questions/scoring).
- Flujo principal:
  - UI Streamlit -> servicios `chatbot_mvp` -> persistencia en `data/`.

## Dependencias y entorno
- Python: 3.10+ (probado local: 3.11.9).
- Gestor (requirements/pyproject):
  - `requirements.txt` y `requirements-dev.txt` (no hay pyproject).
- Variables env:
  - `AI_PROVIDER`, `GEMINI_API_KEY`/`GOOGLE_API_KEY`, `GROQ_API_KEY`, `OPENAI_API_KEY`,
    `GEMINI_MODEL`, `GROQ_MODEL`, `OPENAI_MODEL`, `ADMIN_PASSWORD`, `DEMO_MODE`.
- Servicios externos (si hay):
  - Google Gemini (google-genai), Groq (via OpenAI SDK + base_url), OpenAI (opcional).

## Calidad (tests/lint/CI)
- Checks disponibles:
  - `pytest` (no hay lint/format configurados).
- Scripts:
  - No se encontraron Makefile ni scripts de automatizacion.
- Estado CI:
  - No se encontraron workflows en `.github/`.
- Resultados locales:
  - `python -m pytest`: 7 passed, 1 skipped (legacy Reflex).
  - `python -m streamlit run streamlit_app/Inicio.py --server.headless true --server.port 8510`: arranca y expone URL local.
  - Nota: puerto 8510 estaba en uso y se libero antes de la prueba.

## Migracion Reflex -> Streamlit
- Migrado:
  - UI Streamlit en `streamlit_app/` y servicios reutilizados en `chatbot_mvp/`.
- Pendiente:
  - Limpiar/archivar componentes Reflex y tests asociados.
  - Revisar y borrar `.states/` si ya no se usa.
- Restos de Reflex detectados:
  - `chatbot_mvp/components/` (imports `reflex as rx`).
  - `.states/` (cache Reflex).
  - `tests/test_auth_state.py` (usa `chatbot_mvp.state`).
  - `docs/DEV_NOTES.md` (guia Reflex).

## Riesgos / bloqueos (priorizados)
- P0: Ninguno bloqueante detectado para ejecucion local.
- P1: Test legacy Reflex skippeado (sin cobertura).
- P2: Restos de Reflex generan ruido y imports rotos si se usan por error.

## Backlog recomendado (P0/P1/P2 + esfuerzo S/M/L)
- P1 (S): Resolver test legacy (eliminar o migrar `test_auth_state.py`).
- P1 (M): Limpiar/archivar codigo Reflex (`chatbot_mvp/components`, `.states/`).
- P2 (M): Decidir soporte OpenAI (agregar dependencia o remover provider).
- P2 (S): Reducir duplicacion de prompts en `openai_client`, `gemini_client`, `groq_client`.

## Primeros 3 proximos pasos
1) Definir destino de tests legacy (eliminar o migrar `test_auth_state.py`).
2) Limpiar restos de Reflex (`chatbot_mvp/components`, `.states/`).
3) Definir politica de proveedor IA y manejo de `app_settings.json`.
