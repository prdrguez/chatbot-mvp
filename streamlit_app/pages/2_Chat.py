import streamlit as st
import sys
from pathlib import Path

# Add project root
root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from chatbot_mvp.services.chat_service import create_chat_service
from chatbot_mvp.config.settings import get_runtime_ai_provider, get_env_value
from streamlit_app.components.sidebar import sidebar_branding, load_custom_css

st.set_page_config(page_title="Asistente IA - Chat", page_icon="💬", layout="wide")

load_custom_css()

INITIAL_ASSISTANT_MESSAGE = (
    "¡Hola! Soy tu asistente de ética en IA. ¿En qué puedo ayudarte hoy?"
)


def reset_chat_messages() -> None:
    st.session_state.messages = [
        {"role": "assistant", "content": INITIAL_ASSISTANT_MESSAGE}
    ]


provider_labels = {"gemini": "Gemini", "groq": "Groq"}

title_col, action_col = st.columns([6, 1])
with title_col:
    st.title("Conversa con la IA")
    st.markdown("Pregunta sobre ética, sesgos o los resultados de tu evaluación.")

with action_col:
    with st.popover("⋯", use_container_width=True):
        if st.button("Nuevo chat", use_container_width=True):
            reset_chat_messages()
            st.rerun()

active_provider = get_runtime_ai_provider()
st.caption(f"Proveedor activo: {provider_labels.get(active_provider, active_provider)}")

if active_provider == "gemini":
    if not get_env_value("GEMINI_API_KEY") and not get_env_value("GOOGLE_API_KEY"):
        st.warning("Falta GEMINI_API_KEY/GOOGLE_API_KEY. Se usara modo demo.")
    try:
        from google import genai  # noqa: F401
    except Exception:
        st.error(
            "Falta google-genai o hay conflicto con el paquete google. "
            "Recomendado: pip uninstall google y pip install google-genai."
        )
elif active_provider == "groq":
    if not get_env_value("GROQ_API_KEY"):
        st.warning("Falta GROQ_API_KEY. Se usara modo demo.")
    try:
        import openai  # noqa: F401
    except Exception:
        st.error("Falta openai para Groq. Instala: pip install openai.")

# Initial message
if "messages" not in st.session_state:
    reset_chat_messages()

# Initialize Chat Service
if (
    "chat_service" not in st.session_state
    or st.session_state.get("chat_service_provider") != active_provider
):
    try:
        st.session_state.chat_service = create_chat_service()
        st.session_state.chat_service_provider = active_provider
    except Exception as e:
        st.error(f"Error inicializando servicio de chat: {e}")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Escribe tu pregunta..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        try:
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[:-1]
            ]

            service = st.session_state.chat_service
            stream = service.send_message_stream(
                message=prompt,
                conversation_history=history,
                user_context={},
            )

            response_text = st.write_stream(stream)
            st.session_state.messages.append(
                {"role": "assistant", "content": response_text}
            )

        except Exception as e:
            st.error(f"Error en el servicio de chat: {e}")

sidebar_branding()
