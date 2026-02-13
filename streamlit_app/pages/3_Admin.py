import streamlit as st
import sys
import pandas as pd
import json
import hashlib
from datetime import datetime
from pathlib import Path
import plotly.express as px

# Add project root
root_path = Path(__file__).parent.parent.parent
root_path_str = str(root_path)
if root_path_str in sys.path:
    sys.path.remove(root_path_str)
sys.path.insert(0, root_path_str)

from chatbot_mvp.services.submissions_store import read_submissions, summarize
from chatbot_mvp.config.settings import get_admin_password, is_demo_mode, get_runtime_ai_provider
from chatbot_mvp.knowledge import (
    KB_MODE_GENERAL,
    KB_MODE_STRICT,
    load_kb,
    normalize_kb_mode,
)
from streamlit_app.components.sidebar import sidebar_branding, load_custom_css

st.set_page_config(page_title="Admin Panel", page_icon="📊", layout="wide")
load_custom_css()

# Simple Auth
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == get_admin_password():
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Contraseña de Administrador", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Contraseña de Administrador", type="password", on_change=password_entered, key="password"
        )
        st.error("Contraseña incorrecta")
        return False
    else:
        # Password correct.
        return True

def get_chart_config(fig):
    """Applies common premium styling to charts."""
    fig.update_layout(
        font_family="Inter",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    # Try to apply rounded corners if supported by installed plotly version
    # fallback gracefully if not
    try:
        fig.update_traces(marker=dict(cornerradius=5)) 
    except:
        pass
    return fig


def _decode_kb_bytes(raw_bytes: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode("utf-8", errors="replace")

def _sync_kb_runtime(
    text: str, name: str, kb_updated_at: str = ""
) -> dict:
    return load_kb(text=text, name=name, kb_updated_at=kb_updated_at)


def _apply_kb_runtime_bundle(kb_bundle: dict) -> None:
    st.session_state["kb_hash"] = kb_bundle.get("kb_hash", "")
    st.session_state["kb_chunks"] = kb_bundle.get("chunks", [])
    st.session_state["kb_index"] = kb_bundle.get("index", {})

if check_password():
    st.title("Panel de Administración")
    toast_message = st.session_state.pop("provider_toast", None)
    if toast_message:
        st.toast(toast_message, icon="✅")
    sidebar_branding()
    
    # Load Data
    data = read_submissions()
    
    # Create Tabs
    tab_dash, tab_data, tab_settings = st.tabs(["📊 Dashboard", "💾 Datos", "⚙️ Configuración"])
    
    # --- TAB DASHBOARD ---
    with tab_dash:
        if not data:
            st.warning("No hay envíos registrados aún.")
        else:
            summary = summarize(data)
            
            # KPIs
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Envíos", summary["total"])
            col2.metric("Promedio Correctas", summary["avg_correct"])
            col3.metric("Promedio Scored", summary["avg_total"])
            col4.metric("% Acierto Global", f"{summary['avg_percent']}%")
            
            st.divider()
            
            # Processing Data for Charts
            # We will perform a single pass or use pandas for everything easier
            flat_entries = []
            for entry in data:
                row = entry.copy()
                ans = row.pop("answers", {})
                row.update(ans) # Flatten answers to top level
                flat_entries.append(row)
            
            df = pd.DataFrame(flat_entries)
            
            # --- ROW 1: CORE DEMOGRAPHICS (Gender, Age) ---
            st.subheader("Demografía Principal")
            r1c1, r1c2 = st.columns(2)
            
            with r1c1:
                if "demo_gender" in df.columns:
                     df_gen = df["demo_gender"].value_counts().reset_index()
                     df_gen.columns = ["Género", "Cantidad"]
                     fig = px.bar(df_gen, x="Género", y="Cantidad", title="Género", color="Cantidad")
                     st.plotly_chart(get_chart_config(fig), width="stretch")
            
            with r1c2:
                if "demo_age" in df.columns:
                     df_age = df["demo_age"].value_counts().reset_index()
                     df_age.columns = ["Edad", "Cantidad"]
                     # Sort ranges if possible, usually lexicographical sort works ok for "18-25" etc
                     fig = px.bar(df_age, x="Edad", y="Cantidad", title="Rango Etario", color="Cantidad")
                     st.plotly_chart(get_chart_config(fig), width="stretch")

            # --- ROW 2: CONTEXT (Education, Occupation, Area) ---
            st.subheader("Perfil Profesional y Educativo")
            r2c1, r2c2, r2c3 = st.columns(3)
            
            with r2c1:
                if "context_education" in df.columns:
                    df_edu = df["context_education"].value_counts().reset_index()
                    df_edu.columns = ["Nivel Educativo", "Cantidad"]
                    fig = px.pie(df_edu, values="Cantidad", names="Nivel Educativo", title="Nivel Educativo", hole=0.4)
                    st.plotly_chart(get_chart_config(fig), width="stretch")

            with r2c2:
                if "context_role" in df.columns:
                    df_occ = df["context_role"].value_counts().reset_index()
                    df_occ.columns = ["Ocupación", "Cantidad"]
                    fig = px.bar(df_occ, x="Ocupación", y="Cantidad", title="Ocupación Actual", color="Cantidad")
                    st.plotly_chart(get_chart_config(fig), width="stretch")

            with r2c3:
                if "context_area" in df.columns:
                    df_area = df["context_area"].value_counts().reset_index()
                    df_area.columns = ["Área", "Cantidad"]
                    fig = px.bar(df_area, x="Cantidad", y="Área", orientation='h', title="Área de Formación/Trabajo")
                    st.plotly_chart(get_chart_config(fig), width="stretch")

            # --- ROW 3: LOCATION & USAGE ---
            st.subheader("Geografía y Uso de IA")
            r3c1, r3c2 = st.columns(2)
            
            with r3c1:
                if "context_city" in df.columns:
                    # Top 10 cities to avoid clutter
                    top_cities = df["context_city"].str.title().value_counts().nlargest(10).reset_index()
                    top_cities.columns = ["Ciudad", "Cantidad"]
                    fig = px.bar(top_cities, x="Ciudad", y="Cantidad", title="Top Ciudades", color="Cantidad")
                    st.plotly_chart(get_chart_config(fig), width="stretch")

            with r3c2:
                if "context_frequency" in df.columns:
                    df_freq = df["context_frequency"].value_counts().reset_index()
                    df_freq.columns = ["Frecuencia", "Cantidad"]
                    fig = px.bar(df_freq, x="Frecuencia", y="Cantidad", title="Uso de Herramientas IA", color="Cantidad")
                    st.plotly_chart(get_chart_config(fig), width="stretch")


            # --- ROW 4: EMOTIONS & FAIRNESS ---
            st.subheader("Percepción y Emociones")
            r4c1, r4c2 = st.columns(2)
            
            with r4c1:
                if "context_emotions" in df.columns:
                    # Emotions are lists in standard format, but CSV conversion might make them strings
                    # Need to handle list expansion
                    all_emotions = []
                    for items in df["context_emotions"]:
                        if isinstance(items, list):
                            all_emotions.extend(items)
                        elif isinstance(items, str):
                            # Try safe eval or split if it looks like a list string
                            try:
                                # Simple cleanup for "['A', 'B']"
                                cleaned = items.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
                                if cleaned:
                                    parts = [x.strip() for x in cleaned.split(",")]
                                    all_emotions.extend(parts)
                            except:
                                pass
                    
                    if all_emotions:
                        df_em = pd.Series(all_emotions).value_counts().reset_index()
                        df_em.columns = ["Emoción", "Frecuencia"]
                        df_em = df_em.sort_values(by="Frecuencia", ascending=True)
                        fig = px.bar(df_em, x="Frecuencia", y="Emoción", orientation='h', title="Emociones Generadas", color="Frecuencia")
                        st.plotly_chart(get_chart_config(fig), width="stretch")

            with r4c2:
                if "eval_reflect" in df.columns:
                    df_fair = df["eval_reflect"].value_counts().reset_index()
                    df_fair.columns = ["Respuesta", "Cantidad"]
                    fig = px.pie(df_fair, values="Cantidad", names="Respuesta", title="¿Consideras que la IA puede ser justa?", hole=0.6)
                    st.plotly_chart(get_chart_config(fig), width="stretch")

    # --- TAB DATA ---
    with tab_data:
        st.subheader("Explorador de Datos")
        if not data:
             st.info("Sin datos para mostrar.")
        else:
             # Prepare clean DF for export
             # We reuse flat_entries from above but ensure cleanliness
             clean_entries = []
             for entry in data:
                 row = entry.copy()
                 answers = row.pop("answers", {})
                 # Flatten specific keys explicitly to avoid clutter
                 for k, v in answers.items():
                     if isinstance(v, list):
                         row[k] = ", ".join(v)
                     else:
                         row[k] = v
                 clean_entries.append(row)
                 
             df_dump = pd.DataFrame(clean_entries)
             
             # Adjust column order if possible (Id, date, score, level, demographics...)
             cols = sorted(df_dump.columns.tolist())
             # Move important ones to front
             priority = ["created_at", "score", "level", "demo_age", "demo_gender"]
             for p in reversed(priority):
                 if p in cols:
                     cols.insert(0, cols.pop(cols.index(p)))
             
             df_final = df_dump[cols]
             st.dataframe(df_final, width="stretch")
             
             # Timestamped filename
             timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
             
             col_dl1, col_dl2 = st.columns(2)
             
             # CSV Export
             csv = df_final.to_csv(index=False).encode('utf-8')
             col_dl1.download_button(
                 "⬇️ Descargar CSV",
                 csv,
                 f"submissions_{timestamp}.csv",
                 "text/csv",
                 key='download-csv'
             )
             
             # JSON Export
             json_str = json.dumps(data, indent=2, ensure_ascii=False)
             col_dl2.download_button(
                 "⬇️ Descargar JSON",
                 json_str,
                 f"submissions_{timestamp}.json",
                 "application/json",
                 key='download-json'
             )
             
        # Destructive Action
        st.divider()
        if st.toggle("Modo Mantenimiento"):
             st.error("Zona de Peligro")
             if st.button("🗑️ BORRAR TODOS LOS DATOS", type="primary"):
                 try:
                     # Delete physical file
                     file_path = Path(root_path) / "data" / "submissions.jsonl"
                     if file_path.exists():
                         file_path.unlink()
                     st.success("Base de datos reiniciada. Recarga la página.")
                     st.rerun()
                 except Exception as e:
                     st.error(f"Error borrando datos: {e}")

    # --- TAB SETTINGS ---
    with tab_settings:
        st.subheader("Configuración de Sistema")
        
        # AI Provider Selection
        st.write("### Inteligencia Artificial")
        from chatbot_mvp.services.app_settings_store import set_provider_override
        
        current_p = get_runtime_ai_provider()
        col_provider, col_status = st.columns([2, 4])
        with col_provider:
            new_provider = st.radio(
                "Proveedor de IA",
                ["gemini", "groq"],
                index=0 if current_p == "gemini" else 1,
                horizontal=True,
                label_visibility="collapsed",
            )
        with col_status:
            st.caption("Cambia el motor de IA del chat y evaluación.")
        
        st.caption(f"Proveedor activo: {current_p}")

        if new_provider != current_p:
             st.session_state.ai_provider = new_provider
             set_provider_override(new_provider)
             st.session_state.pop("chat_service", None)
             st.session_state.pop("chat_service_provider", None)
             st.session_state.provider_toast = f"Proveedor actualizado: {new_provider}"
             st.rerun()
        
        st.divider()
        
        st.subheader("Apariencia")
        st.caption("Personalización básica de colores.")
        
        col_c1, col_c2 = st.columns(2)
        primary_col = col_c1.color_picker("Color Primario", "#4facfe")
        bg_col = col_c2.color_picker("Color Fondo (Sidebar)", "#161b22")
        
        if st.button("Aplicar Estilos"):
             custom_css = f"""
             <style>
                [data-testid="stSidebar"] {{
                    background-color: {bg_col} !important;
                }}
                h1 {{
                    background: linear-gradient(90deg, {primary_col} 0%, #00f2fe 100%) !important;
                    -webkit-background-clip: text !important;
                    -webkit-text-fill-color: transparent !important;
                }}
                .stButton button:hover {{
                    border-color: {primary_col} !important;
                }}
             </style>
             """
             st.markdown(custom_css, unsafe_allow_html=True)
             st.toast("Estilos aplicados")

        st.divider()
        st.subheader("Base de Conocimiento")
        st.caption("Subi una politica o protocolo en formato .txt o .md")

        if "kb_mode" not in st.session_state:
            st.session_state["kb_mode"] = KB_MODE_GENERAL
        if "kb_debug" not in st.session_state:
            st.session_state["kb_debug"] = False

        st.session_state["kb_mode"] = normalize_kb_mode(st.session_state.get("kb_mode"))

        kb_mode = st.radio(
            "Modo de respuesta",
            [KB_MODE_GENERAL, KB_MODE_STRICT],
            index=0 if st.session_state.get("kb_mode") == KB_MODE_GENERAL else 1,
            format_func=lambda value: "Solo KB (estricto)" if value == KB_MODE_STRICT else "General",
            horizontal=True,
            key="admin_kb_mode_radio",
        )
        if kb_mode != st.session_state.get("kb_mode"):
            st.session_state["kb_mode"] = normalize_kb_mode(kb_mode)
            mode_label = "Solo KB (estricto)" if kb_mode == KB_MODE_STRICT else "General"
            st.toast(f"Modo KB actualizado: {mode_label}", icon="✅")
            st.rerun()

        kb_debug = st.checkbox(
            "Debug KB",
            value=bool(st.session_state.get("kb_debug", False)),
            help="Muestra en Chat los chunks recuperados y sus scores.",
        )
        if kb_debug != bool(st.session_state.get("kb_debug", False)):
            st.session_state["kb_debug"] = kb_debug
            st.rerun()

        uploaded_kb = st.file_uploader(
            "Archivo KB",
            type=["txt", "md"],
            accept_multiple_files=False,
            key="admin_kb_uploader",
            help="Solo se permite un archivo por vez.",
        )

        if uploaded_kb is not None:
            raw_bytes = uploaded_kb.getvalue()
            uploaded_text = _decode_kb_bytes(raw_bytes)
            uploaded_text = uploaded_text.strip()
            kb_signature = f"{uploaded_kb.name}:{hashlib.sha256(raw_bytes).hexdigest()}"
            current_signature = st.session_state.get("kb_signature")
            if uploaded_text and kb_signature != current_signature:
                new_updated_at = datetime.now().isoformat(timespec="seconds")
                try:
                    kb_bundle = _sync_kb_runtime(
                        uploaded_text,
                        uploaded_kb.name,
                        kb_updated_at=new_updated_at,
                    )
                except Exception as exc:
                    st.error(f"No se pudo procesar la KB cargada: {exc}")
                else:
                    st.session_state["kb_text"] = uploaded_text
                    st.session_state["kb_name"] = uploaded_kb.name
                    st.session_state["kb_updated_at"] = new_updated_at
                    st.session_state["kb_signature"] = kb_signature
                    _apply_kb_runtime_bundle(kb_bundle)
                    st.toast(f"KB cargada: {uploaded_kb.name}", icon="✅")
                    st.rerun()
            if not uploaded_text and kb_signature != current_signature:
                st.toast("El archivo esta vacio o no se pudo leer.", icon="⚠️")

        kb_name = st.session_state.get("kb_name", "")
        kb_text = st.session_state.get("kb_text", "")
        if kb_name and kb_text:
            expected_hash = hashlib.sha256(kb_text.strip().encode("utf-8")).hexdigest()
            if st.session_state.get("kb_hash") != expected_hash:
                try:
                    kb_bundle = _sync_kb_runtime(
                        kb_text,
                        kb_name,
                        kb_updated_at=st.session_state.get("kb_updated_at", ""),
                    )
                except Exception as exc:
                    st.error(f"No se pudo sincronizar la KB activa: {exc}")
                else:
                    _apply_kb_runtime_bundle(kb_bundle)

            st.caption(f"KB cargada: {kb_name} ({len(kb_text)} caracteres)")
            if st.button("Limpiar KB", use_container_width=False):
                st.session_state.pop("kb_text", None)
                st.session_state.pop("kb_name", None)
                st.session_state.pop("kb_updated_at", None)
                st.session_state.pop("kb_signature", None)
                st.session_state.pop("kb_hash", None)
                st.session_state.pop("kb_chunks", None)
                st.session_state.pop("kb_index", None)
                st.session_state["admin_kb_uploader"] = None
                st.toast("KB limpiada", icon="⚠️")
                st.rerun()
        else:
            st.caption("KB cargada: ninguna.")
        kb_active_label = kb_name if kb_name else "ninguna"
        kb_mode_caption = "Solo KB (estricto)" if st.session_state.get("kb_mode") == KB_MODE_STRICT else "General"
        st.caption(f"KB activa: {kb_active_label}")
        st.caption(f"Modo: {kb_mode_caption}")
