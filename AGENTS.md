# AGENTS.md

Instrucciones persistentes para este repo (Streamlit + Python). Seguir estas reglas en todas las tareas futuras.

## Alcance y stack
- Mantener el stack actual: Python + Streamlit.
- No reintroducir Reflex salvo pedido explicito.
- Default AI: Gemini (via `google-genai`).
- Streaming habilitado por defecto en Chat.

## Estilo de cambios
- Cambios pequenos y diffs acotados.
- Nombres claros y consistentes.
- Mantener UI "Premium" (dark mode friendly, `streamlit_app/assets/style.css`).

## Scope y control
- Respetar estrictamente el scope pedido.
- No implementar mejoras fuera de scope.
- Si aparece una mejora fuera de scope: anotarla como `Backlog` en `docs/STATUS_REPORT.md`.

## Verificacion
- Ejecutar la app con `python -m streamlit run streamlit_app/Inicio.py`.
- Validar rutas: Inicio, Evaluacion, Chat, Admin.
- Ejecutar tests con `python -m pytest`.

## Comandos
- Usar siempre comandos PowerShell en documentacion, prompts y seccion "Como verificar".

## Commits
- Mensajes MUY cortos (1 linea).
- Commits pequenos y enfocados.

## Workflow
- Fuente de verdad: `docs/WORKFLOW.md`.
- Branch por tarea.
- Codex hace cambios + commit + push + PR.
- Usuario solo revisa y aprueba.

## PR
- Base branch: `main`.
- El body del PR debe ser texto plano.
- No usar backticks ni bloques de codigo en el body del PR.

## Secrets / Keys
- Nunca commitear keys ni tokens.
- Usar `.env` local (ignorado) o variables de entorno.
- Si GitHub detecta una key expuesta: rotarla inmediatamente.
- Chequeo antes de commitear:
  - `git grep -n "AIza" . || true`
  - `git grep -n "GEMINI_API_KEY|GOOGLE_API_KEY" . || true`

## Output al finalizar
- Listar archivos tocados.
- Indicar como verificar (comandos de Streamlit y pytest en PowerShell).
- Incluir link del PR.
