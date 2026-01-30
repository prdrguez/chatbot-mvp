import streamlit as st
import sys
from pathlib import Path
import time
import asyncio
import uuid

# Ensure project root is in path
root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from chatbot_mvp.data.juego_etico import QUESTIONS
from chatbot_mvp.services.submissions_store import append_submission
from chatbot_mvp.config.settings import is_demo_mode
from streamlit_app.components.sidebar import sidebar_branding, load_custom_css

# --- Page Config ---
st.set_page_config(page_title="Evaluación - IA Ética", page_icon="📝", layout="wide")
load_custom_css()
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
    st.session_state.quiz_result["result_id"] = str(uuid.uuid4())
    
    
    # Static feedback templates based on level
    FEEDBACK_TEMPLATES = {
        "Bajo": """Tu resultado indica que estás en un nivel inicial de comprensión sobre ética en IA. 
        
**Fortalezas:**  
Has dado el primer paso al completar esta evaluación, lo cual demuestra tu interés en el tema.

**Áreas de mejora:**  
Es importante profundizar en conceptos clave como la discriminación algorítmica, los sesgos en datos de entrenamiento y la importancia de la transparencia en los sistemas de IA.

**Recomendaciones:**  
1. Revisa los conceptos de sesgo algorítmico y cómo los datos históricos pueden perpetuar desigualdades.  
2. Aprende sobre principios éticos fundamentales como justicia, transparencia y supervisión humana en IA.  
3. Explora casos reales de discriminación algorítmica para comprender sus impactos.

¡No te desanimes! La ética en IA es un campo complejo, y este ejercicio es el inicio de tu aprendizaje. Continúa estudiando y estarás mejor preparado para usar IA de manera responsable.""",
        
        "Medio": """Has alcanzado un nivel medio de comprensión sobre ética en IA, lo cual refleja que tienes una base sólida en los principios fundamentales.

**Fortalezas:**  
Comprendes conceptos clave como la discriminación algorítmica y los principios éticos básicos. Esto te posiciona bien para seguir avanzando.

**Áreas de mejora:**  
Aún quedan aspectos por reforzar, especialmente en temas de mitigación de sesgos, marcos de gobernanza y la aplicación práctica de la transparencia algorítmica.

**Recomendaciones:**  
1. Profundiza en estrategias para reducir sesgos: diversificación de datos, auditorías y supervisión humana.  
2. Investiga frameworks legales como el AI Act de la UE y su impacto en el desarrollo responsable de IA.  
3. Practica el análisis crítico de salidas de IA para detectar posibles sesgos.

Sigue trabajando en estas áreas y pronto tendrás el conocimiento necesario para abordar desafíos más complejos en ética de IA.""",
        
        "Alto": """¡Felicitaciones! Has alcanzado un nivel alto de comprensión sobre ética en inteligencia artificial.

**Fortalezas:**  
Demuestras un conocimiento sólido sobre discriminación algorítmica, principios éticos, transparencia y responsabilidad. Comprendes la importancia de la supervisión humana y las auditorías de modelos.

**Oportunidades de crecimiento:**  
Aunque tu nivel es alto, la ética en IA es un campo en constante evolución. Mantente actualizado sobre nuevas regulaciones, técnicas de mitigación y casos emergentes.

**Recomendaciones:**  
1. Participa en comunidades de ética en IA para compartir conocimientos y aprender de casos reales.  
2. Aplica tus conocimientos en proyectos prácticos, auditando modelos o diseñando sistemas con enfoque ético.  
3. Mantente al día con marcos legales como el AI Act y guías de desarrollo responsable.

Tu comprensión te permite liderar conversaciones críticas sobre el uso justo e inclusivo de la IA. ¡Sigue adelante!"""
    }
    
    # Assign feedback based on level
    st.session_state.quiz_result["ai_feedback"] = FEEDBACK_TEMPLATES.get(level, "Evaluación completada.")

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
    result_id = res.get("result_id")
    already_streamed = (
        result_id
        and st.session_state.get("analysis_streamed_for_eval_id") == result_id
    )
    if "ai_feedback" in res:
        if not already_streamed:
            # Simulate typing effect
            import time
            def typing_effect(text):
                """Generator that yields text character by character for typing effect."""
                for char in text:
                    yield char
                    time.sleep(0.01) # Small delay for natural feel

            st.write_stream(typing_effect(res["ai_feedback"]))
            if result_id:
                st.session_state.analysis_streamed_for_eval_id = result_id
        else:
            st.markdown(res["ai_feedback"])
    
    if st.button("Volver al inicio"):
        # Reset state
        for key in [
            "responses",
            "step",
            "current_index",
            "quiz_result",
            "analysis_streamed_for_eval_id",
        ]:
            if key in st.session_state:
                del st.session_state[key]
        st.switch_page("Inicio.py")
        st.stop()

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
