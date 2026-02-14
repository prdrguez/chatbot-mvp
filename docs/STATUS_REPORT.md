# STATUS REPORT - Streamlit MVP

Fecha de actualizacion: 2026-02-14

## Resumen ejecutivo
- App activa en Streamlit multipage con entry point `streamlit_app/Inicio.py`.
- KB grounding actualizado con retrieval BM25 liviano en Python puro y bonus por match exacto.
- Cache de indice/chunks por `kb_hash + kb_updated_at` para evitar recomputo por mensaje.
- Modos KB `General` y `Solo KB (estricto)` activos en Chat con control desde Admin.

## Que funciona hoy
- Navegacion multipage Streamlit (`Inicio.py`, `pages/1_Evaluacion.py`, `pages/2_Chat.py`, `pages/3_Admin.py`).
- Chat con streaming y providers Gemini/Groq, fallback Demo.
- Selector de provider en Admin persistido en `chatbot_mvp/data/app_settings.json`.
- KB en Admin:
  - Upload `.txt` / `.md` (un archivo por vez).
  - Construccion de indice BM25-like cacheada por `kb_hash` y `kb_updated_at`.
  - Parametros configurables: `Top K`, `Score minimo`, `Max chars contexto`.
  - Indicador `Index builds (cache miss)` para validar performance.
- KB en Chat:
  - Reutiliza `kb_index` en `st.session_state`.
  - Recupera evidencia con `top_k/min_score` configurados.
  - Limita contexto inyectado por cantidad de chunks y caracteres.
  - Agrega `Fuentes:` en post-proceso del sistema cuando se uso KB.
  - En `Solo KB (estricto)`, sin evidencia suficiente responde fijo y no llama provider.
  - `Debug KB retrieval` muestra score, seccion y preview por evidencia.
- Evaluacion y dashboard Admin siguen operativos (submissions + export CSV/JSON).

## Que NO funciona hoy
- `openai` no esta expuesto en el selector de Admin.
- Si `AI_PROVIDER=openai`, el flujo runtime actual cae en fallback Demo.
- Existe test legacy Reflex skippeado (`tests/test_auth_state.py`).

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

## Como probar KB grounding y performance (PowerShell)

1. Levantar app y abrir Admin.
2. Cargar `docs\securin.txt` en Base de Conocimiento.
3. Verificar que aparece `KB cargada` e `Index builds (cache miss)`.
4. Ir a Chat y preguntar:
   - `Que es Securion?`
   - `Se pueden recibir regalos?`
5. Cambiar a `Solo KB (estricto)` y preguntar algo fuera del documento.
6. Activar `Debug KB` y validar score/seccion/preview.
7. Hacer 5 preguntas seguidas y verificar que `index_build_count` no sube por cada mensaje.

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
- Resultado: `25 passed, 1 skipped`
- Test skippeado: `tests/test_auth_state.py` (legacy Reflex)

## Backlog
- Integrar provider OpenAI de punta a punta en Chat (selector + init cliente).
- Limpiar restos legacy Reflex cuando se defina cierre definitivo.
