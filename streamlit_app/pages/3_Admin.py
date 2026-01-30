import streamlit as st
import sys
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import plotly.express as px

# Add project root
root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from chatbot_mvp.services.submissions_store import read_submissions, summarize
from chatbot_mvp.config.settings import get_admin_password, is_demo_mode
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

if check_password():
    st.title("Panel de Administración")
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
                    st.plotly_chart(get_chart_config(fig), use_container_width=True)

            with r2c2:
                if "context_role" in df.columns:
                    df_occ = df["context_role"].value_counts().reset_index()
                    df_occ.columns = ["Ocupación", "Cantidad"]
                    fig = px.bar(df_occ, x="Ocupación", y="Cantidad", title="Ocupación Actual", color="Cantidad")
                    st.plotly_chart(get_chart_config(fig), use_container_width=True)

            with r2c3:
                if "context_area" in df.columns:
                    df_area = df["context_area"].value_counts().reset_index()
                    df_area.columns = ["Área", "Cantidad"]
                    fig = px.bar(df_area, x="Cantidad", y="Área", orientation='h', title="Área de Formación/Trabajo")
                    st.plotly_chart(get_chart_config(fig), use_container_width=True)

            # --- ROW 3: LOCATION & USAGE ---
            st.subheader("Geografía y Uso de IA")
            r3c1, r3c2 = st.columns(2)
            
            with r3c1:
                if "context_city" in df.columns:
                    # Top 10 cities to avoid clutter
                    top_cities = df["context_city"].str.title().value_counts().nlargest(10).reset_index()
                    top_cities.columns = ["Ciudad", "Cantidad"]
                    fig = px.bar(top_cities, x="Ciudad", y="Cantidad", title="Top Ciudades", color="Cantidad")
                    st.plotly_chart(get_chart_config(fig), use_container_width=True)

            with r3c2:
                if "context_frequency" in df.columns:
                    df_freq = df["context_frequency"].value_counts().reset_index()
                    df_freq.columns = ["Frecuencia", "Cantidad"]
                    fig = px.bar(df_freq, x="Frecuencia", y="Cantidad", title="Uso de Herramientas IA", color="Cantidad")
                    st.plotly_chart(get_chart_config(fig), use_container_width=True)


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
                    st.plotly_chart(get_chart_config(fig), use_container_width=True)

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
        st.header("Configuración del Sistema")
        
        st.subheader("Proveedor de IA")
        curr_provider = st.session_state.get("ai_provider", "gemini")
        
        new_provider = st.radio(
            "Selecciona el motor de IA activo:",
            ["gemini", "groq"],
            index=0 if curr_provider == "gemini" else 1,
            format_func=lambda x: x.capitalize()
        )
        
        if new_provider != curr_provider:
            st.session_state["ai_provider"] = new_provider
            st.success(f"Proveedor cambiado a: {new_provider.capitalize()}")
        
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
