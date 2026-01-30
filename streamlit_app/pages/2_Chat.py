import html
import sys
from pathlib import Path

import streamlit as st

from chatbot_mvp.config.settings import get_env_value, get_runtime_ai_provider
from chatbot_mvp.services.chat_service import create_chat_service
from streamlit_app.components.sidebar import load_custom_css, sidebar_branding

# Add project root
root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

st.set_page_config(page_title="Asistente IA - Chat", page_icon="💬", layout="wide")
load_custom_css()

INITIAL_ASSISTANT_MESSAGE = (
    "Hola. Soy tu asistente de etica en IA. En que puedo ayudarte hoy?"
)

st.markdown(
    """
    <style>
      .chat-row { display: flex; align-items: flex-start; gap: 0.5rem; width: 100%; }
      .bubble { max-width: 70%; padding: 0.6rem 0.9rem; border-radius: 0.9rem; line-height: 1.4; }
      .bubble.assistant { background: #21262d; color: #e6edf3; }
      .bubble.user { background: #1f6feb; color: #f0f6fc; margin-left: auto; }
      .avatar { width: 32px; height: 32px; border-radius: 999px; display: flex;
                align-items: center; justify-content: center; font-size: 16px; }
      .avatar.assistant { background: #30363d; }
      .avatar.user { background: #1f6feb; }
    </style>
    """,
    unsafe_allow_html=True,
)


def reset_chat_messages() -> None:
    st.session_state.messages = [
        {"role": "assistant", "content": INITIAL_ASSISTANT_MESSAGE}
    ]


def render_message(role: str, content: str) -> None:
    safe = html.escape(content).replace("\n", "<br/>")
    if role == "assistant":
        col_avatar, col_bubble, col_spacer = st.columns([1, 6, 1])
        col_avatar.markdown(
            '<div class="avatar assistant">🤖</div>', unsafe_allow_html=True
        )
        col_bubble.markdown(
            f'<div class="bubble assistant">{safe}</div>', unsafe_allow_html=True
        )
        col_spacer.empty()
    else:
        col_spacer, col_bubble, col_avatar = st.columns([1, 6, 1])
        col_bubble.markdown(
            f'<div class="bubble user">{safe}</div>', unsafe_allow_html=True
        )
        col_avatar.markdown(
            '<div class="avatar user">🙂</div>', unsafe_allow_html=True
        )
        col_spacer.empty()


provider_labels = {"gemini": "Gemini", "groq": "Groq"}

title_col, action_col = st.columns([6, 1])
with title_col:
    st.title("Conversa con la IA")
    st.markdown("Pregunta sobre etica, sesgos o los resultados de tu evaluacion.")

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
    render_message(msg["role"], msg["content"])

# Chat Input
if prompt := st.chat_input("Escribe tu pregunta..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    render_message("user", prompt)

    # Generate response
    col_avatar, col_bubble, col_spacer = st.columns([1, 6, 1])
    col_avatar.markdown(
        '<div class="avatar assistant">🤖</div>', unsafe_allow_html=True
    )
    bubble_placeholder = col_bubble.empty()
    col_spacer.empty()
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

        response_text = ""
        for chunk in stream:
            response_text += chunk
            safe = html.escape(response_text).replace("\n", "<br/>")
            bubble_placeholder.markdown(
                f'<div class="bubble assistant">{safe}</div>',
                unsafe_allow_html=True,
            )

        st.session_state.messages.append(
            {"role": "assistant", "content": response_text}
        )
    except Exception as e:
        st.error(f"Error en el servicio de chat: {e}")

sidebar_branding()
