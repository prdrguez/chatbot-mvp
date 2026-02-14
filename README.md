# Chatbot MVP (Streamlit)

MVP educativo en Python + Streamlit para evaluacion, chat con IA en streaming y panel administrativo.

- Entry point real: `streamlit_app/Inicio.py`
- Stack actual: Streamlit, pandas, plotly, google-genai, openai, rank-bm25
- Default AI provider: Gemini

## Quickstart (Windows + PowerShell)

1. Abrir PowerShell y pararse en el repo:

```powershell
Set-Location C:\Dev\chatbot-mvp
```

2. Crear y activar entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Instalar dependencias:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. Definir variables de entorno minimas para Gemini:

```powershell
$env:AI_PROVIDER = "gemini"
$env:GEMINI_API_KEY = "<tu_api_key>"
$env:ADMIN_PASSWORD = "123"
```

5. Ejecutar la app:

```powershell
python -m streamlit run streamlit_app/Inicio.py
```

## Paginas y flujo de uso

- `Inicio`: landing y explicacion del flujo general.
- `Evaluacion`: consentimiento, cuestionario y resultados. Guarda cada envio en `data/submissions.jsonl`.
- `Chat`: conversacion con streaming. Si hay KB activa, aplica grounding y agrega fuentes.
- `Admin`: dashboard de envios, exportacion y configuracion (requiere password).

Flujo recomendado:

1. Completar `Evaluacion`.
2. Ir a `Chat` para profundizar consultas.
3. Entrar en `Admin` para revisar resultados y configurar provider/KB.

## Providers de IA (Gemini/Groq/OpenAI/Demo)

Resolucion de provider en runtime (orden real):

1. Override de sesion de Streamlit (`st.session_state.ai_provider`).
2. Override persistido en `chatbot_mvp/data/app_settings.json`.
3. Variable de entorno `AI_PROVIDER`.

Valores validos en config global: `gemini`, `groq`, `openai`, `demo`.

Configuracion desde Admin:

- Ruta: `Admin` -> `Configuracion` -> `Proveedor de IA`.
- UI actual permite cambiar entre `gemini` y `groq`.
- Ese cambio persiste en `chatbot_mvp/data/app_settings.json`.

Notas importantes:

- `gemini` es el default.
- `groq` requiere `GROQ_API_KEY`.
- `openai` existe en configuracion/env, pero no esta expuesto en el selector actual de Admin.
- `demo` responde con textos simulados y tambien se usa como fallback cuando faltan credenciales o falla la inicializacion de cliente.

## Variables de entorno

Base:

- `AI_PROVIDER` = `gemini|groq|openai|demo`
- `ADMIN_PASSWORD`
- `DEMO_MODE` (si no se define, el codigo lo toma como activo)

Gemini:

- `GEMINI_API_KEY` o `GOOGLE_API_KEY`
- `GEMINI_MODEL` (default: `gemini-2.0-flash`)
- `GEMINI_MAX_OUTPUT_TOKENS` (default: `280`)
- `GEMINI_TEMPERATURE` (default: `0.4`)

Groq:

- `GROQ_API_KEY`
- `GROQ_MODEL` (default: `openai/gpt-oss-20b`)

OpenAI:

- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default en cliente: `gpt-4o-mini`)

## Base de Conocimiento (KB)

Gestion desde `Admin` -> `Configuracion` -> `Base de Conocimiento`.

- Formatos soportados: `.txt`, `.md`
- Carga: un archivo por vez
- Limpieza: boton `Limpiar KB`

Modos de respuesta:

- `General`: prioriza evidencia de KB; si no alcanza, permite respuesta general.
- `Solo KB (estricto)`: responde solo con evidencia. Si no hay evidencia suficiente, devuelve mensaje fijo de no encontrado.

Debug KB:

- Opcion `Debug KB` en Admin.
- En Chat aparece un expander con query, razon de retrieval, cantidad de chunks y scores.

## Comandos utiles (PowerShell)

Ejecutar tests:

```powershell
python -m pytest
```

Ejecutar app en puerto especifico:

```powershell
python -m streamlit run streamlit_app/Inicio.py --server.port 8502
```

## Estructura

```text
streamlit_app/                 UI Streamlit (Inicio + pages + assets)
chatbot_mvp/                   Logica de negocio (config, services, knowledge, data)
data/submissions.jsonl         Persistencia local de evaluaciones
chatbot_mvp/data/app_settings.json  Override de provider (creado por Admin)
docs/                          Documentacion operativa
```

Para estado operativo detallado, ver `docs/STATUS_REPORT.md`.
