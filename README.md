# Chatbot MVP (Streamlit Edition)

Este repositorio contiene un MVP de una app web en **Streamlit** para una experiencia educativa con evaluación, chat inteligente y panel de admin.

**Stack**: Python 3.10+, Streamlit, Google Gemini (GenAI SDK).

## Funcionalidades
- **Evaluación**: Cuestionario interactivo con feedback generado por IA.
- **Chat**: Asistente virtual con respuestas en **Streaming** sobre ética en IA.
- **Diseño Premium**: Interfaz moderna con modo oscuro y estilos personalizados.

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
   streamlit run streamlit_app/app.py
   ```

## Estructura

```
.
├── streamlit_app/         # Aplicación Streamlit
│   ├── app.py             # Entry point
│   ├── pages/             # Páginas (Evaluación, Chat, Admin)
│   └── assets/            # Recursos estáticos (CSS, Imágenes)
├── chatbot_mvp/           # Lógica de Negocio (Backend)
│   ├── core/              # Config y Utiles
│   ├── data/              # Definición de preguntas
│   └── services/          # Clientes IA (Gemini Streaming)
├── data/                  # Almacenamiento local (submissions.jsonl)
└── requirements.txt
```
