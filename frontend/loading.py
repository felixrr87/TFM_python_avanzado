import streamlit as st
import time
import base64
import os

# Fondo de pantalla
def _background_css(image_path):
    with open(image_path, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode()
    return f"""
    <style>
    .stApp {{
        background: url(data:image/jpg;base64,{encoded}) center/cover no-repeat fixed;
    }}
    </style>
    """

def show_loading():
    # Aplicar fondo
    st.markdown(_background_css('assets/background.jpg'), unsafe_allow_html=True)

    # Convertir logo a base64
    logo_path = os.path.join('assets', 'sportalyze.png')
    with open(logo_path, 'rb') as f:
        logo_b64 = base64.b64encode(f.read()).decode()

    # Mostrar logo con fade-in y rotación
    st.markdown(f"""
    <style>
    @keyframes rotate {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    @keyframes fadein {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}
    .rotating-logo {{
        width: 180px;
        margin: 30px auto;
        display: block;
        animation: fadein 2s ease-in-out, rotate 3s linear infinite;
    }}
    .loading-text {{
        text-align: center;
        font-size: 2rem;
        font-family: 'Orbitron', sans-serif;
        color: white;
        margin-top: 20px;
    }}
    .console-message {{
        text-align: center;
        color: #00ffe0;
        font-family: monospace;
        font-size: 16px;
        margin-top: 10px;
    }}
    </style>
    <img class="rotating-logo" src="data:image/png;base64,{logo_b64}" />
    <div class="loading-text">SPORTALYZE</div>
    """, unsafe_allow_html=True)

    # Mensajes tipo consola
    console_logs = [
        ">> Booting neural system...",
        ">> Loading player intelligence module...",
        ">> Syncing tactical database...",
        ">> Initiating performance metrics...",
    ]
    for log in console_logs:
        st.markdown(f'<div class="console-message">{log}</div>', unsafe_allow_html=True)
        time.sleep(0.5)

    # Barra de progreso
    progress = st.progress(0)
    fases = [
       ]

    progreso_actual = 0
    for mensaje, objetivo in fases:
        while progreso_actual < objetivo:
            progreso_actual += 5
            progress.progress(progreso_actual)
            st.markdown(f'<div class="console-message">{mensaje} {progreso_actual}%</div>', unsafe_allow_html=True)
            time.sleep(0.07)

    st.session_state.loading_done = True
    st.experimental_rerun()

