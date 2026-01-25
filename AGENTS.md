# AGENTS.md

Instrucciones persistentes para este repo (Reflex + Python). Seguir estas reglas en todas las tareas futuras.

## Alcance y stack
- Mantener el stack actual: **Python + Reflex**.
- No introducir frameworks nuevos.
- Default AI: **Gemini**.
- No arreglar OpenAI salvo que una tarea lo pida explícitamente.

## Estilo de cambios
- Cambios pequeños y diffs acotados.
- Nombres claros y consistentes.

## Verificación
- Correr la app con `reflex run`.
- Chequear rutas: `/chat`, `/evaluacion`, `/admin`.

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
- Indicar cómo verificar.
