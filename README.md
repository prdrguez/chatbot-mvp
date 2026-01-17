# Chatbot MVP (Reflex)

Este repositorio contiene un MVP de una app web en Reflex para una experiencia
educativa con evaluacion, chat y panel de admin.
El objetivo es validar flujo completo: onboarding simple, evaluacion guiada,
registro de respuestas y visualizacion basica de KPIs.
El MVP tambien incluye un modo demo para mostrar UI extra (Admin y UI Gallery).
No hay integraciones externas obligatorias; los datos se guardan localmente.
Esta documentacion apunta a desarrollo y mantenimiento del estado actual.

## Correr local

1) Crear y activar entorno virtual
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Instalar dependencias
```bash
pip install -r requirements.txt
```

3) (Opcional) Variables de entorno
```bash
cp .env.example .env
# DEMO_MODE=1 para demo, DEMO_MODE=0 para ocultar /ui y el link a /admin
```

4) Ejecutar
```bash
reflex run
```

5) Abrir en el navegador
- Frontend: http://localhost:3000 (verificar en consola)
- Backend API: http://localhost:8000 (verificar en consola)

## Rutas principales

- `/` inicio con links a evaluacion y chat.
- `/evaluacion` juego etico con preguntas y resultado final.
- `/chat` chat de demo con respuestas predefinidas.
- `/admin` panel de KPIs, theme editor y export (visible en demo).
- `/ui` catalogo de componentes (solo demo).

## Modo demo

El demo se activa con `DEMO_MODE=1` (por defecto si no se define).
Habilita:
- Link y acceso a `/ui` (UI Gallery).
- Link visible a `/admin` en el header.
- Mensajes de demo en el chat.

Definicion: `chatbot_mvp/config/settings.py -> is_demo_mode()`.

## Estructura de carpetas (resumen)

```
.
├── chatbot_mvp/
│   ├── chatbot_mvp.py
│   ├── components/
│   ├── pages/
│   ├── state/
│   ├── services/
│   ├── ui/
│   └── data/
├── assets/
├── data/
├── exports/
├── requirements.txt
├── rxconfig.py
└── .env.example
```

## Troubleshooting

- `reflex: command not found`:
  instala dependencias y usa `python3 -m reflex run` si el binario no esta en PATH.
- `Address already in use` en puertos 3000/8000:
  cerrar el proceso previo o cambiar puertos (ver salida de `reflex run`).
- Error por usar Vars en `if`:
  en Reflex no hagas `if state_var:`; usa `rx.cond(...)`.
- Props invalidas en grid (`columns=["1","2"]`):
  usar `columns="2"` o `columns=rx.breakpoints(...)`.
- Charts que colapsan en alto:
  usar `recharts.responsive_container` con `height` fijo.

## Documentacion adicional

- Estado del proyecto: `docs/STATUS.md`
- Notas de desarrollo: `docs/DEV_NOTES.md`
- Changelog reciente: `docs/CHANGELOG_RECENT.md`
