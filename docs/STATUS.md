# Project Status

## Session Snapshot (2026-01-25)
- Branch actual: main
- Último commit: 3319103 docs: add workflow (#1)
- PRs abiertos: ninguno

## NOW / NEXT
- NOW: estabilizar UI chat (sidebar height/scroll) + tareas #0 pendientes
- NEXT:
  - Retomar tarea #0 (por definir)
  - Mejorar panel lateral de sesiones (estética + scroll)
  - Revisar tema ThemeState null (si vuelve a aparecer)

## Estado actual
- App Reflex + Python en funcionamiento local.
- Rutas activas: `/`, `/chat`, `/evaluacion`, `/admin`, `/login` (y `/ui` en modo demo).
- Chat: UI oscura, sidebar y panel con scroll interno; input legible.
- Evaluación: flujo completo con resultados y fallback si Gemini falla.
- Admin: login funcional en demo, UI oscura y KPIs/graphs legibles.
- Gemini: rate limiting, cache, backoff y cooldown configurables por env.

## Issues conocidos
- P0: Ninguno reportado al momento.
- P1: Límites de cuota de Gemini pueden activar cooldown/429 en picos de tráfico (mitigado por backoff/cooldown).
- P1: Admin login usa password por env; en demo se permite "123" si no hay env.

## Variables de entorno requeridas
- AI_PROVIDER
- DEMO_MODE
- ADMIN_PASSWORD
- GEMINI_API_KEY
- GOOGLE_API_KEY
- GEMINI_MODEL
- GEMINI_MIN_INTERVAL_SECONDS
- GEMINI_CACHE_TTL_SECONDS
- GEMINI_CACHE_MAX_SIZE
- GEMINI_MAX_BACKOFF_SECONDS
- GEMINI_COOLDOWN_SECONDS
- GEMINI_MAX_COOLDOWN_SECONDS
- GROQ_API_KEY
- GROQ_MODEL
- OPENAI_API_KEY
- OPENAI_MODEL

## Pasos de prueba
1) `reflex run`
2) Verificar rutas: `/chat`, `/evaluacion`, `/admin`
3) (Opcional) `/login` y `/ui` si demo

## Workflow / Cómo retomar
- Source of truth: `docs/WORKFLOW.md` (AGENTS.md lo referencia).
- Branch actual: `docs/workflow`.
- Para retomar: `git status -sb` + `git diff --name-only` + `git log -5 --oneline`.
- Revisar PRs abiertos antes de continuar.

## Backlog UI
- Arreglar panel lateral de sesiones (alto/scroll/estética).

## Últimos cambios (resumen breve)
- Ajustes de layout y UX en /chat (input, panel, sidebar, altura).
- Mejoras UI admin (login y cards de KPIs/graphs).
- Manejo de errores en chat (callout sin bubble) y rate limit Gemini (cache/backoff/cooldown).
- Registro y carga temprana de ThemeState.

## PRs abiertos
- OPEN: feat/admin-provider-selector (selector global de provider AI persistido en data/app_settings.json).
