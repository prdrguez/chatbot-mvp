import streamlit as st
import sys
from pathlib import Path
import time
import asyncio

# Ensure project root is in path
root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from chatbot_mvp.data.juego_etico import QUESTIONS
from chatbot_mvp.services.submissions_store import append_submission
from chatbot_mvp.config.settings import is_demo_mode
from streamlit_app.components.sidebar import sidebar_branding

# --- Page Config ---
st.set_page_config(page_title="Evaluación - IA Ética", page_icon="📝")
sidebar_branding()

# --- Constants & Helpers ---
CONSENT_QUESTION = next(q for q in QUESTIONS if q.get("type") == "consent")
NON_CONSENT_QUESTIONS = [q for q in QUESTIONS if q.get("type") != "consent"]

def get_current_question_index():
    return st.session_state.get("current_index", 0)

def next_step():
    st.session_state.current_index = st.session_state.get("current_index", 0) + 1

def prev_step():
    st.session_state.current_index = max(0, st.session_state.get("current_index", 0) - 1)

def submit_quiz():
    # Calculate score
    score = 0
    total_scored = 0
    
    for q in QUESTIONS:
        if not q.get("scored") or not q.get("correct"):
            continue
        
        total_scored += 1
        q_id = q["id"]
        user_response = st.session_state.responses.get(q_id)
        
        if not isinstance(user_response, str):
            continue
            
        # Basic normalization for matching "A) Option..." to "A"
        normalized = user_response.strip()
        correct = q["correct"]
        
        match = False
        if normalized.startswith(correct + ")") or normalized.startswith(correct + ".") or normalized == correct:
             match = True
        
        # If user selected full text "A) Answer", check if it starts with correct letter
        if not match and len(normalized) > 1:
             if normalized.upper().startswith(correct):
                 match = True

        if match:
            score += 1
            
    # Determine level
    if score <= 5:
        level = "Bajo"
    elif score <= 10:
        level = "Medio"
    else:
        level = "Alto"
        
    st.session_state.quiz_result = {
        "score": score,
        "total_scored": total_scored,
        "level": level,
        "score_percent": int((score / total_scored) * 100) if total_scored else 0
    }
    
    # Generate AI Feedback
    with st.spinner("Generando feedback personalizado con IA..."):
        try:
            from chatbot_mvp.services.gemini_client import generate_evaluation_feedback
            
            # Prepare payload matching the service expectation
            questions_payload = []
            for q in NON_CONSENT_QUESTIONS:
                q_id = q["id"]
                resp = st.session_state.responses.get(q_id)
                answer_text = str(resp) if resp is not None else ""
                if isinstance(resp, list):
                    answer_text = ", ".join(resp)
                elif isinstance(resp, bool):
                    answer_text = "Acepto" if resp else "No acepto"

                questions_payload.append({
                    "id": q_id,
                    "section": q.get("section", ""),
                    "prompt": q.get("prompt", ""),
                    "answer": answer_text,
                    "type": q.get("type", ""),
                    "scored": q.get("scored", False)
                })

            payload = {
                "summary": {
                    "score": score,
                    "correct_count": score,
                    "total_scored": total_scored,
                    "score_percent": st.session_state.quiz_result["score_percent"],
                    "level": level
                },
                "questions": questions_payload
            }
            
            feedback = generate_evaluation_feedback(payload)
            st.session_state.quiz_result["ai_feedback"] = feedback
            
        except Exception as e:
            st.error(f"Error generando feedback IA: {e}")
            st.session_state.quiz_result["ai_feedback"] = "No se pudo generar el feedback automático."

    # Save submission
    try:
        append_submission(
            answers=st.session_state.responses,
            score=score,
            level=level,
            demo_mode=is_demo_mode(),
            correct_count=score,
            total_scored=total_scored,
            score_percent=st.session_state.quiz_result["score_percent"],
            ai_feedback=st.session_state.quiz_result.get("ai_feedback", "")
        )
    except Exception as e:
        st.error(f"Error guardando resultados: {e}")
        
    st.session_state.step = "finished"

# --- Page Config removed (moved to top)

if "responses" not in st.session_state:
    st.session_state.responses = {}
if "step" not in st.session_state:
    st.session_state.step = "consent"
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

# --- Views ---

def show_results():
    res = st.session_state.quiz_result
    st.title("Resultados de la Evaluación")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Puntaje", f"{res['score']} / {res['total_scored']}")
    col2.metric("Nivel", res['level'])
    col3.metric("Porcentaje", f"{res['score_percent']}%")
    
    st.divider()
    
    st.subheader("Análisis de IA")
    if "ai_feedback" in res:
        st.info(res["ai_feedback"])
    
    if st.button("Volver al inicio"):
        # Reset state
        for key in ["responses", "step", "current_index", "quiz_result"]:
                del st.session_state[key]
        st.switch_page("Inicio.py")

def show_question_form():
    idx = get_current_question_index()
    if idx >= len(NON_CONSENT_QUESTIONS):
        submit_quiz()
        st.rerun()
        
    q = NON_CONSENT_QUESTIONS[idx]
    
    # Progress bar
    progress = (idx + 1) / len(NON_CONSENT_QUESTIONS)
    st.progress(progress, text=f"Pregunta {idx + 1} de {len(NON_CONSENT_QUESTIONS)}")
    
    st.subheader(q.get("section", "Pregunta"))
    st.markdown(f"**{q['prompt']}**")
    
    q_id = q["id"]
    prev_val = st.session_state.responses.get(q_id)
    
    new_val = None
    
    if q["type"] == "text":
        new_val = st.text_input("Tu respuesta", value=prev_val if prev_val else "", placeholder=q.get("placeholder", ""))
    elif q["type"] == "single":
        opts = q.get("options", [])
        idx_sel = opts.index(prev_val) if prev_val in opts else None
        new_val = st.radio("Selecciona una opción:", opts, index=idx_sel, key=f"radio_{q_id}")
    elif q["type"] == "multi":
        opts = q.get("options", [])
        default = prev_val if isinstance(prev_val, list) else []
        new_val = st.multiselect("Selecciona opciones:", opts, default=default, key=f"multi_{q_id}")
        
    # Navigation
    col_prev, col_next = st.columns([1, 1])
    
    if col_prev.button("Anterior", disabled=(idx == 0)):
        if new_val is not None:
             st.session_state.responses[q_id] = new_val
        prev_step()
        st.rerun()
        
    label_next = "Finalizar" if idx == len(NON_CONSENT_QUESTIONS) - 1 else "Siguiente"
    
    if col_next.button(label_next, type="primary"):
        if not new_val and q.get("required", False):
            st.error("Por favor completa este campo para continuar.")
        else:
            st.session_state.responses[q_id] = new_val
            if idx == len(NON_CONSENT_QUESTIONS) - 1:
                submit_quiz()
            else:
                next_step()
            st.rerun()

def show_consent():
    st.title("Consentimiento Informado")
    st.markdown(CONSENT_QUESTION["prompt"])
    
    accepted = st.checkbox(CONSENT_QUESTION["options"][0])
    
    if st.button("Comenzar Evaluación", type="primary", disabled=not accepted):
        st.session_state.responses[CONSENT_QUESTION["id"]] = True
        st.session_state.step = "questions"
        st.rerun()

# --- Main Dispatcher ---

if st.session_state.step == "finished":
    show_results()
elif st.session_state.step == "questions":
    show_question_form()
else:
    show_consent()
