# STATUS REPORT - Streamlit MVP

Fecha de actualizacion: 2026-02-14

## Resumen ejecutivo
- App activa en Streamlit multipage con entry point `streamlit_app/Inicio.py`.
- Paginas activas: Inicio, Evaluacion, Chat y Admin.
- Chat usa streaming y soporte de providers Gemini/Groq con fallback a Demo.
- Admin permite cambiar provider (Gemini/Groq), cargar KB y activar debug de retrieval.
- Evaluacion guarda resultados locales en `data/submissions.jsonl`.

## Que funciona hoy
- Navegacion multipage Streamlit (`Inicio.py`, `pages/1_Evaluacion.py`, `pages/2_Chat.py`, `pages/3_Admin.py`).
- Evaluacion con consentimiento, cuestionario y feedback por nivel (Bajo/Medio/Alto).
- Persistencia de respuestas y score via `chatbot_mvp/services/submissions_store.py`.
- Chat con streaming token/chunk en UI y boton "Nuevo chat".
- Providers de Chat:
  - Gemini via `google-genai` (`GEMINI_API_KEY` o `GOOGLE_API_KEY`).
  - Groq via OpenAI SDK + base_url Groq (`GROQ_API_KEY`).
  - Demo como fallback o provider explicito.
- Selector de provider en Admin (Gemini/Groq) persistido en `chatbot_mvp/data/app_settings.json`.
- Base de Conocimiento:
  - Upload de `.txt`/`.md` (un archivo por vez).
  - Parse por articulos/secciones + chunking por tamano.
  - Retrieval lexical con overlap/substrings/sequence fallback.
  - Modos `General` y `Solo KB (estricto)`.
  - `Debug KB` en Chat (expander con query, razon, chunks y scores).
- Dashboard Admin con KPIs + export CSV/JSON + borrado de submissions en modo mantenimiento.

## Que NO funciona hoy
- `openai` no esta expuesto en el selector de Admin.
- Si `AI_PROVIDER=openai`, `ChatService` no inicializa cliente OpenAI automaticamente y termina en fallback Demo.
- Existe test legacy Reflex skippeado (`tests/test_auth_state.py`), sin cobertura activa de ese legado.

## Comandos de ejecucion (PowerShell)

Preparacion local:

```powershell
Set-Location C:\Dev\chatbot-mvp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Variables ejemplo para Gemini:

```powershell
$env:AI_PROVIDER = "gemini"
$env:GEMINI_API_KEY = "<tu_api_key>"
$env:ADMIN_PASSWORD = "123"
```

Run app:

```powershell
python -m streamlit run streamlit_app/Inicio.py
```

Run tests:

```powershell
python -m pytest
```

## Troubleshooting actual (PowerShell)

- Falta clave Gemini:

```powershell
$env:GEMINI_API_KEY = "<tu_api_key>"
```

- Quiero usar Groq:

```powershell
$env:AI_PROVIDER = "groq"
$env:GROQ_API_KEY = "<tu_api_key>"
```

- Error por conflicto de paquete `google`:

```powershell
pip uninstall -y google
pip install -U google-genai
```

- Error por SDK OpenAI faltante (Groq/OpenAI):

```powershell
pip install -U openai
```

- Proveedor no cambia en runtime:

```powershell
Remove-Item chatbot_mvp\data\app_settings.json -ErrorAction SilentlyContinue
```

- Puerto ocupado al correr Streamlit:

```powershell
python -m streamlit run streamlit_app/Inicio.py --server.port 8502
```

## Tests (estado actual)
- Comando ejecutado: `python -m pytest`
- Resultado: `22 passed, 1 skipped`
- Test skippeado: `tests/test_auth_state.py` (legacy Reflex)

## Backlog
- Integrar provider OpenAI de punta a punta en Chat (selector + init cliente).
- Limpiar restos legacy Reflex (codigo/tests) cuando se defina cierre definitivo.
