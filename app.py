import streamlit as st
import sys
import os
from pathlib import Path

# Configurar rutas primero
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# Luego configurar Streamlit (esto debe ser lo primero)
st.set_page_config(
    page_title="SPORTALYZE",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importar después de configurar rutas
from frontend.login import show_login
from frontend.loading import show_loading
from frontend.home import show_home

if __name__ == "__main__":
    # Inicializar estado de sesión
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'loading_done' not in st.session_state:
        st.session_state.loading_done = False

    # Lógica de flujo
    if not st.session_state.logged_in:
        show_login()
    elif not st.session_state.loading_done:
        show_loading()
    else:
        show_home()