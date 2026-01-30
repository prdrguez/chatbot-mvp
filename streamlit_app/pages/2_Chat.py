import streamlit as st
import sys
import time
from pathlib import Path

# Add project root
root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from chatbot_mvp.services.chat_service import create_chat_service
from chatbot_mvp.config.settings import is_demo_mode
from streamlit_app.components.sidebar import sidebar_branding, load_custom_css

st.set_page_config(page_title="Asistente IA - Chat", page_icon="💬")

load_custom_css()
sidebar_branding()

# Sidebar History
with st.sidebar:
    st.markdown("### Historial")
    if "chat_history_sessions" not in st.session_state:
        st.session_state.chat_history_sessions = []
    
    if not st.session_state.chat_history_sessions:
        st.caption("No hay chats previos.")
    else:
        for idx, session in enumerate(st.session_state.chat_history_sessions):
            st.button(f"Chat {idx+1}", key=f"hist_{idx}", width="stretch")

st.title("Conversa con la IA")
st.markdown("Pregunta sobre ética, sesgos o los resultados de tu evaluación.")

# Initial message
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Soy tu asistente de ética en IA. ¿En qué puedo ayudarte hoy?"}
    ]

# Initialize Chat Service
if "chat_service" not in st.session_state:
    try:
        st.session_state.chat_service = create_chat_service()
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
        # Stream response
        try:
            # Prepare history for service
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[:-1] 
            ]
            
            service = st.session_state.chat_service
            
            # Use streaming method
            stream = service.send_message_stream(
                message=prompt,
                conversation_history=history,
                user_context={} 
            )
            
            # Render stream
            response_text = st.write_stream(stream)
            
            # Save full response to history
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
        except Exception as e:
            st.error(f"Error en el servicio de chat: {e}")

# Sidebar info
# Sidebar info
with st.sidebar:
    st.divider()
    # Standard Chat Actions
    if st.button("Nuevo Chat", width="stretch", type="primary"):
        # Save current session to history if not empty
        if len(st.session_state.messages) > 1:
            st.session_state.chat_history_sessions.append(st.session_state.messages)
        
        st.session_state.messages = [
            {"role": "assistant", "content": "¡Hola! Soy tu asistente de ética en IA. ¿En qué puedo ayudarte hoy?"}
        ]
        st.rerun()
