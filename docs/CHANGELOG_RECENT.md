# CHANGELOG RECENT

Base: `main`
Ventana: ultimos 25 commits (`git log --oneline -25`)

- `07c4e26` Sidebar + KB integrados en el flujo principal.
- `b384e34` Ajustes de layout flex en chat, toast en Admin y streaming Gemini.
- `be7c6c0` Burbujas de chat, toast admin y respuestas Gemini mas completas.
- `f469bc7` Config de provider centralizada en Admin con lazy init estricto.
- `c22e99b` Soporte Groq via OpenAI SDK + switch de provider + fix de re-stream.
- `69f959b` Actualizacion de docs de estado y entrypoint Streamlit.
- `f10eff0` Fix de import faltante en Admin y layout consistente.
- `6a94eea` Fix Gemini 404, anchos uniformes y switch persistente de provider.
- `1db7df5` Pulido UX final: typing effect, logo sidebar y modelo Gemini.
- `40cd8df` Limpieza de historial chat, sidebar y deprecations.
- `15224ad` Reorganizacion UI (logo/badge), CSS unificado y docs `.env`.
- `b660991` Pulido UI: fixes deprecations, badge menor, typing effect.
- `b7e6b20` Feedback estatico por nivel en resultados de evaluacion.
- `5aec628` Migracion completa a Streamlit con Admin 2.0 y branding.
- `8a4d4d3` Fix de typewriter estable en evaluacion.
- `a9284f8` Fallback rapido cuando se cancela stream de evaluacion.
- `8d54713` Scheduling de stream desde `finish()` con logs de carga.
- `1bbcfc7` Fix de timeout de loading en `finish()`.
- `05211fb` Manejo de streaming cancelado + fallback de spinner.
- `e43d2d0` Logs de debug para progreso de streaming en evaluacion.
- `deb9776` Limpieza: remove trigger no usado y llamada directa de evento.
- `ac0acde` Forzar apagado de loading a los 2s + logs.
- `150a43f` Fix de update de estado `show_loading` antes del stream.
- `68e5621` Limpieza de ancho duplicado en loading view.
- `776184b` Nueva pantalla de loading con espera minima y typewriter visible.

Resumen rapido:
- Se consolido la migracion a Streamlit.
- Se integro KB con modos General/Estricto y debugging.
- Se agrego switching Gemini/Groq y mejoras de estabilidad en streaming.
- Se pulio UX visual (chat, sidebar, admin, evaluacion).
