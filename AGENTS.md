# AGENTS.md

Instrucciones persistentes para este repo (Streamlit + Python). Seguir estas reglas en todas las tareas futuras.

## Alcance y stack
- Mantener el stack actual: **Python + Streamlit**.
- No reintroducir Reflex salvo pedido explícito.
- Default AI: **Gemini** (vía `google-genai`).
- Streaming enabled por defecto en Chat.

## Estilo de cambios
- Cambios pequeños y diffs acotados.
- Nombres claros y consistentes.
- Mantener UI "Premium" (Dark mode friendly, `style.css`).

## Verificación
- Correr la app con `streamlit run streamlit_app/Inicio.py`.
- Chequear rutas: Home, Evaluación, Chat.

## Commits
- Si hacés commits: mensajes **MUY cortos** (1 línea).

## Workflow
- Guía completa en `docs/WORKFLOW.md` (source of truth).
- Resumen: branch por tarea, commits cortos, push y PR a `main`.

## Secrets / Keys
- Nunca commitear keys ni tokens.
- Usar `.env` local (ignorado) o exportar variables de entorno.
- Si GitHub detecta una key expuesta: rotar inmediatamente.
- Chequeo antes de commitear:
  - `git grep -n "AIza" . || true`
  - `git grep -n "GEMINI_API_KEY|GOOGLE_API_KEY" . || true`

## Output al finalizar
- Listar archivos tocados.
- Indicar cómo verificar (comandos de Streamlit).
