import streamlit as st
from pathlib import Path
from chatbot_mvp.config.settings import is_demo_mode

def load_custom_css():
    """Load custom CSS for unified theming across all pages."""
    css_path = Path(__file__).parent.parent / "assets" / "style.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def sidebar_branding():
    """
    Renders standard Jano branding in the sidebar.
    Logo and badge positioned at the BOTTOM of sidebar.
    """
    with st.sidebar:
        # Spacer to push content to bottom
        st.markdown("<br>" * 10, unsafe_allow_html=True)
        
        # Divider before footer section
        st.markdown("---")
        
        # Footer text
        st.markdown(
            """
            <div style="text-align: center; color: #8b949e; font-size: 0.8rem; margin-bottom: 12px;">
                <strong>Jano</strong> by <span style="color: #d63384;">Iguales</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Logo at the bottom
        try:
            st.image("streamlit_app/assets/logo.png", width="stretch")
        except:
            pass
        
        # Demo badge below logo (if demo mode)
        if is_demo_mode():
            st.markdown(
                """
                <div style="
                    background-color: #f63366; 
                    color: white; 
                    padding: 2px 8px; 
                    border-radius: 3px; 
                    text-align: center; 
                    font-weight: bold; 
                    margin-top: 8px;
                    font-size: 0.65rem;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                ">
                    MODO DEMO
                </div>
                """, 
                unsafe_allow_html=True
            )
