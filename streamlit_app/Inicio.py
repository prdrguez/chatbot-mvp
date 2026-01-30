import streamlit as st
import sys
from pathlib import Path

# Add project root to python path to allow importing chatbot_mvp packages
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from chatbot_mvp.config.settings import is_demo_mode

st.set_page_config(
    page_title="IA Ética - MVP",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

def load_css():
    css_path = Path(__file__).parent / "assets" / "style.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

st.title("IA Ética: Conceptos y Reflexión")

st.markdown("""
### Bienvenido

Esta experiencia interactiva está diseñada para explorar conceptos clave sobre la **Ética en la Inteligencia Artificial**.

A través de esta herramienta podrás:
1. **Evaluar tu conocimiento**: Participa en un breve juego de preguntas y respuestas sobre sesgos, justicia y responsabilidad.
2. **Dialogar con una IA**: Conversa con un asistente virtual para profundizar en estos temas.
3. **Ver resultados (Admin)**: Visualizar estadísticas agregadas (requiere acceso).

---

### ¿Cómo funciona?

- Usa el menú lateral para navegar entre las secciones.
- **Evaluación**: Responde el cuestionario para obtener tu nivel y feedback personalizado.
- **Chat**: Interactúa libremente con el asistente.
""")

if is_demo_mode():
    st.info("Modo DEMO activado. Algunas funciones pueden estar simuladas.", icon="ℹ️")

from streamlit_app.components.sidebar import sidebar_branding

# Sidebar Branding
sidebar_branding()

# No extra footer needed manually here as it is in the component
# but kept just in case specific logic was there.

