# Project Status

## Estado actual (hoy)

- App Reflex con rutas principales: `/`, `/evaluacion`, `/chat`, `/admin`.
- Modo demo por `DEMO_MODE` habilita `/ui` y links extra en el header.
- Evaluacion con IA (Gemini) en tiempo real para feedback personalizado.
- ChatBot con integración `google-genai` y fallback a modo demo.
- Historial de sesiones persistente en barra lateral del chat.
- Guardado local de submissions en `data/submissions.jsonl` (append-only).
- KPIs en Admin con charts, reinicio de datos y logout.
- Theme editor simplificado y persistente.
- Export de submissions a `exports/` en JSON y CSV.
- UI Premium con glassmorphism, animaciones y diseño responsivo.

## Arquitectura rapida

- `pages/` define pantallas (layout + componentes).
- `components/` contiene layout compartido (header + content).
- `state/` guarda estado Reflex (vars, events, carga de datos).
- `services/` maneja I/O local (submissions, export, resumen de KPIs).
- `data/` contiene cuestionario, versiones, y overrides de theme.
- `ui/` define tokens y estilos reutilizables.

## Mapa de archivos clave

- `chatbot_mvp/chatbot_mvp.py`: define app, rutas y on_load.
- `chatbot_mvp/components/layout.py`: layout base, header y links demo.
- `chatbot_mvp/pages/admin.py`: tabs (KPIs/Theme/Export) y layout de cards.
- `chatbot_mvp/pages/evaluacion.py`: render de preguntas y flujo visual.
- `chatbot_mvp/pages/chat.py`: UI de chat con respuestas demo.
- `chatbot_mvp/pages/ui_gallery.py`: catalogo de componentes (demo).
- `chatbot_mvp/state/admin_state.py`: KPIs, charts y export.
- `chatbot_mvp/state/evaluacion_state.py`: flujo de evaluacion y scoring.
- `chatbot_mvp/state/chat_state.py`: mensajes de chat demo.
- `chatbot_mvp/state/theme_state.py`: overrides de theme persistidos.
- `chatbot_mvp/services/submissions_store.py`: lectura, resumen y export.
- `chatbot_mvp/data/juego_etico.py`: preguntas y metadata del cuestionario.
- `chatbot_mvp/ui/tokens.py`: tokens base de layout/estilo.
- `chatbot_mvp/ui/evaluacion_tokens.py`: estilos del flujo de evaluacion.

## Decisiones tomadas y por que (mini ADR)

- Theme overrides: se guardan en `chatbot_mvp/data/theme_overrides.json` y se aplican
  via `ThemeState.applied_overrides` en `components/layout.py` para afectar toda la app.
- UI Gallery: existe para verificar componentes Reflex disponibles y estilos base
  en modo demo, sin depender del flujo productivo.
- Admin: tabs separan KPIs, Theme y Export. KPIs usan Recharts con fallback seguro
  para mantener UI funcional aun si algunos componentes no existen.
- Evaluacion: tipos `consent`, `text`, `single`, `multi` renderizan inputs distintos
  y se validan en `EvaluacionState` antes de avanzar.

## Estado de KPIs

- KPIs activos: Resumen (total + promedio), By Level, Edad, Genero, Ciudad,
  Frecuencia IA, Nivel Educativo, Ocupacion, Area, Emociones.
- Fuente de datos: `services/submissions_store.summarize` sobre submissions locales.
- Ciudad usa top 8 + "Otros" en chart horizontal.
- Export: JSON y CSV con timestamp en `exports/`.

## Known issues / riesgos

- P0: Ninguno identificado.
- P1: `reflex` no disponible en PATH -> usar `python3 -m reflex run`.
- P1: Errores por usar `if state_var` -> usar `rx.cond` en UI.
- P2: Props invalidas en grid (`columns=[...]`) -> usar string o breakpoints.
- P2: `openai_client.py` existe pero no esta conectado a UI (verificar
  `chatbot_mvp/services/openai_client.py`).

## Backlog recomendado (orden sugerido)

1) Agregar autenticacion o gating real para `/admin` en no-demo.
2) Semillas de datos de ejemplo para KPIs (y reset local).
3) Conectar evaluacion a `openai_client` (si se requiere feedback IA).
4) Tests basicos de `summarize` y `AdminState` (happy path + edge cases).
5) Documentar el formato de submissions en `data/submissions.jsonl`.
6) Ajustar export CSV para incluir schema/version metadata.
7) Separar assets y estilos en un tema centralizado (tokens unificados).
8) Agregar logging simple para cargas/errores en Admin.
9) Mejorar UX de errores en evaluacion y export.
10) Revisar performance de charts con datasets grandes.
