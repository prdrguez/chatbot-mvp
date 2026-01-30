import streamlit as st
from chatbot_mvp.config.settings import is_demo_mode

def sidebar_branding():
    """
    Renders standard Jano branding in the sidebar.
    Includes Logo (top) and Footer (bottom).
    """
    with st.sidebar:
        # Logo at the top (if available)
        try:
            st.image("streamlit_app/assets/logo.png", width="stretch")
        except:
            st.title("Jano")

        # Config section (can be expanded later via args if needed per page)
        # For now, we put common things here if requested, but user asked for specific layouts per page.
        # So we keep this function mainly for Branding.

        # Spacer to push content down if needed, but sidebar flow usually stacks.
        
        # Footer
        st.markdown("---")
        st.markdown(
            """
            <div style="text-align: center; color: #8b949e; font-size: 0.8rem;">
                <strong>Jano</strong> by <span style="color: #d63384;">Iguales</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Hide default Streamlit footer/menu via CSS if desired locally, 
        # but globally style.css handles most things.

def sidebar_demo_badge():
    """Renders a visual badge if in Demo mode."""
    if is_demo_mode():
        st.sidebar.markdown(
            """
            <div style="
                background-color: #f63366; 
                color: white; 
                padding: 2px 8px; 
                border-radius: 3px; 
                text-align: center; 
                font-weight: bold; 
                margin-bottom: 16px;
                font-size: 0.65rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            ">
                MODO DEMO
            </div>
            """, 
            unsafe_allow_html=True
        )
