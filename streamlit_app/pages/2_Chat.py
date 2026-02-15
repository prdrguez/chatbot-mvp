import html
import sys
import logging
from pathlib import Path

import streamlit as st

from chatbot_mvp.config.settings import get_env_value, get_runtime_ai_provider
from chatbot_mvp.knowledge import KB_MODE_GENERAL, KB_MODE_STRICT, normalize_kb_mode
from chatbot_mvp.services.chat_service import create_chat_service
from streamlit_app.components.sidebar import load_custom_css, sidebar_branding

# Add project root
root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

st.set_page_config(page_title="Asistente IA - Chat", page_icon="💬", layout="wide")
load_custom_css()
logger = logging.getLogger(__name__)

INITIAL_ASSISTANT_MESSAGE = (
    "Hola. Soy tu asistente de etica en IA. En que puedo ayudarte hoy?"
)

st.markdown(
    """
    <style>
      .msg-row { display: flex; align-items: flex-start; gap: 12px; margin: 10px 0; }
      .msg-row.user { justify-content: flex-end; }
      .msg-row.assistant { justify-content: flex-start; }
      .msg { max-width: 70%; padding: 0; background: transparent; border: none; }
      .msg.user { text-align: right; }
      .avatar { width: 38px; height: 38px; border-radius: 999px; display: flex;
                align-items: center; justify-content: center; font-size: 20px; font-weight: 700; }
      .avatar.user { background: #2f6fed; color: #ffffff; }
      .avatar.assistant { background: #ff8a00; color: #111111; }
    </style>
    """,
    unsafe_allow_html=True,
)


def reset_chat_messages() -> None:
    st.session_state.messages = [
        {"role": "assistant", "content": INITIAL_ASSISTANT_MESSAGE}
    ]


def render_message_html(role: str, content: str) -> str:
    safe = html.escape(content).replace("\n", "<br/>")
    if role == "assistant":
        return (
            '<div class="msg-row assistant">'
            '<div class="avatar assistant">🤖</div>'
            f'<div class="msg assistant">{safe}</div>'
            "</div>"
        )
    return (
        '<div class="msg-row user">'
        f'<div class="msg user">{safe}</div>'
        '<div class="avatar user">🙂</div>'
        "</div>"
    )


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
kb_text = st.session_state.get("kb_text", "")
kb_name = st.session_state.get("kb_name", "")
kb_mode = normalize_kb_mode(st.session_state.get("kb_mode", KB_MODE_GENERAL))
kb_debug = bool(st.session_state.get("kb_debug", False))
kb_hash = st.session_state.get("kb_hash", "")
kb_chunks = st.session_state.get("kb_chunks", [])
kb_index = st.session_state.get("kb_index", {})
kb_top_k = int(st.session_state.get("kb_top_k", 4))
kb_min_score = float(st.session_state.get("kb_min_score", 0.0))
kb_max_context_chars = int(st.session_state.get("kb_max_context_chars", 3200))
kb_mode_label = "Solo KB (estricto)" if kb_mode == KB_MODE_STRICT else "General"
if kb_text and kb_name:
    st.caption(f"KB activa: {kb_name}")
else:
    st.caption("KB activa: ninguna")
st.caption(f"Modo: {kb_mode_label}")
if kb_name and not kb_text:
    st.warning("Hay nombre de KB activo pero el contenido esta vacio.")

if kb_debug:
    debug_payload = st.session_state.get("chat_kb_debug")
    with st.expander("Debug KB retrieval", expanded=False):
        if not debug_payload:
            st.caption("Aun no hay retrieval para mostrar.")
        else:
            st.caption(f"KB: {debug_payload.get('kb_name', 'ninguna')}")
            st.caption(f"Modo: {debug_payload.get('kb_mode', 'general')}")
            st.caption(
                f"Query: {debug_payload.get('query', '')} | "
                f"Motivo: {debug_payload.get('reason', '')}"
            )
            st.caption(f"Query expandida: {debug_payload.get('query_expanded', '')}")
            st.caption(
                f"Intent: {debug_payload.get('intent', '')} | "
                f"Tags: {', '.join(debug_payload.get('tags', []))}"
            )
            st.caption(
                f"Chunks recuperados: {debug_payload.get('retrieved_count', 0)} | "
                f"Contexto usado: {debug_payload.get('used_context', False)}"
            )
            rows = debug_payload.get("chunks", [])
            if not rows:
                st.caption("0 hits. Revisa query/threshold y chunking.")
            for row in rows:
                source = row.get("source") or row.get("source_label", "")
                section = row.get("section", "")
                score = row.get("score", 0.0)
                match_type = row.get("match_type", "")
                snippet = row.get("preview") or row.get("snippet", "")
                st.caption(
                    f"{source} | section={section} | score={score} | match={match_type} | snippet={snippet}"
                )

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

if "messages" not in st.session_state:
    reset_chat_messages()

if (
    "chat_service" not in st.session_state
    or st.session_state.get("chat_service_provider") != active_provider
):
    try:
        st.session_state.chat_service = create_chat_service()
        st.session_state.chat_service_provider = active_provider
    except Exception as e:
        st.error(f"Error inicializando servicio de chat: {e}")

for msg in st.session_state.messages:
    st.markdown(render_message_html(msg["role"], msg["content"]), unsafe_allow_html=True)

if prompt := st.chat_input("Escribe tu pregunta..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(render_message_html("user", prompt), unsafe_allow_html=True)

    placeholder = st.empty()
    try:
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[:-1]
        ]
        user_context = {
            "kb_mode": kb_mode,
            "kb_text": kb_text,
            "kb_name": kb_name,
            "kb_hash": kb_hash,
            "kb_chunks": kb_chunks,
            "kb_index": kb_index,
            "kb_updated_at": st.session_state.get("kb_updated_at", ""),
            "kb_top_k": kb_top_k,
            "kb_min_score": kb_min_score,
            "kb_max_context_chars": kb_max_context_chars,
        }
        if kb_debug:
            logger.info(
                "KB debug send | kb_name=%s | kb_text_len=%s | kb_mode=%s",
                kb_name,
                len(kb_text or ""),
                kb_mode,
            )

        service = st.session_state.chat_service
        stream = service.send_message_stream(
            message=prompt,
            conversation_history=history,
            user_context=user_context,
        )
        if hasattr(service, "get_last_kb_debug"):
            st.session_state["chat_kb_debug"] = service.get_last_kb_debug()

        response_text = ""
        for chunk in stream:
            response_text += chunk
            placeholder.markdown(
                render_message_html("assistant", response_text),
                unsafe_allow_html=True,
            )

        st.session_state.messages.append(
            {"role": "assistant", "content": response_text}
        )
        if hasattr(service, "get_last_kb_debug"):
            st.session_state["chat_kb_debug"] = service.get_last_kb_debug()
    except Exception as e:
        st.error(f"Error en el servicio de chat: {e}")

sidebar_branding()
