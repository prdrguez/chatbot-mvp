# Chatbot MVP (Streamlit Edition)

Este repositorio contiene un MVP de una app web en **Streamlit** para una experiencia educativa con evaluación, chat inteligente y panel de admin.

**Stack**: Python 3.10+, Streamlit, Google Gemini (GenAI SDK).

## Funcionalidades
- **Evaluación**: Cuestionario interactivo con feedback generado por IA.
- **Chat**: Asistente virtual con respuestas en **Streaming** sobre ética en IA.
- **Diseño Premium**: Interfaz moderna con modo oscuro y estilos personalizados.

## Quickstart (local)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run streamlit_app/Inicio.py
```

## Instalación y Ejecución

1. **Crear entorno virtual**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar Variables de Entorno**:
   ```bash
   cp .env.example .env
   # Editar .env con tus claves (GEMINI_API_KEY, etc.)
   ```

4. **Ejecutar App**:
   ```bash
   streamlit run streamlit_app/Inicio.py
   ```

Notas:
- `AI_PROVIDER` por defecto es `gemini` (requiere `GEMINI_API_KEY` o `GOOGLE_API_KEY`).
- Admin usa `ADMIN_PASSWORD` (en demo, default `123`).

## Estructura

```
.
|-- streamlit_app/          # Aplicacion Streamlit
|   |-- Inicio.py           # Entry point (Home)
|   |-- pages/              # Paginas (Evaluacion, Chat, Admin)
|   `-- assets/             # Recursos estaticos (CSS, imagenes)
|-- chatbot_mvp/            # Logica de negocio
|   |-- config/
|   |-- data/               # Preguntas y settings locales
|   `-- services/           # Servicios IA y persistencia
|-- data/                   # submissions.jsonl (runtime)
`-- requirements.txt
```
