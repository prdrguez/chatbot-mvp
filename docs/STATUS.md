# Project Status

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
- OPENAI_API_KEY
- OPENAI_MODEL

## Pasos de prueba
1) `reflex run`
2) Verificar rutas: `/chat`, `/evaluacion`, `/admin`
3) (Opcional) `/login` y `/ui` si demo

## Últimos cambios (resumen breve)
- Ajustes de layout y UX en /chat (input, panel, sidebar, altura).
- Mejoras UI admin (login y cards de KPIs/graphs).
- Manejo de errores en chat (callout sin bubble) y rate limit Gemini (cache/backoff/cooldown).
- Registro y carga temprana de ThemeState.
