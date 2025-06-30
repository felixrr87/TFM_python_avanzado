import streamlit as st
import base64
import os
from datetime import datetime
from frontend.api_data import show_api_data
from frontend.scraping_data import show_scraping_data  
from frontend.ml_scouting import scouting_page

def set_background(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded_string}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        color: white !important;
    }}

    .logo-fixed {{
        position: fixed;
        top: 60;
        right: 10px;
        width: 80px;
        z-index: 80;
        filter: drop-shadow(0 0 5px rgba(0,0,0,0.7));
    }}

    .main * {{
        color: white !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.85) !important;
        border-radius: 10px;
        padding: 10px;
    }}

    section[data-testid="stSidebar"] * {{
        color: black !important;
    }}

    section[data-testid="stSidebar"] .stSelectbox > div > div {{
        color: black !important;
        background-color: white !important;
    }}

    section[data-testid="stSidebar"] .stSelectbox [role="listbox"] div {{
        color: black !important;
        background-color: white !important;
    }}

    section[data-testid="stSidebar"] .stRadio label {{
        color: black !important;
    }}

    section[data-testid="stSidebar"] .stTextInput input {{
        color: black !important;
    }}

    section[data-testid="stSidebar"] label {{
        color: black !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def show_home():
    bg_path = os.path.join('assets', 'background.jpg')
    logo_path = os.path.join('assets', 'sportalyze.png')

    set_background(bg_path)

    with open(logo_path, "rb") as logo_file:
        logo_b64 = base64.b64encode(logo_file.read()).decode()
    st.markdown(
        f'<img class="logo-fixed" src="data:image/png;base64,{logo_b64}" alt="SPORTALYZE Logo">',
        unsafe_allow_html=True,
    )

    st.sidebar.title("🏟️ SPORTALYZE")
    section = st.sidebar.selectbox("Selecciona sección", ["🏠 Home", "📊 Stats", "🤖 Machine Learning"])

    if section == "🏠 Home":
        st.markdown("""
        <div style='text-align: center; font-family: "Helvetica Neue", Arial, sans-serif;'>
            <h1 style='margin-bottom: 5px; color: #ffffff;'>SPORTALYZE</h1>
            <p style='font-size: 20px; margin-top: 0; color: #eeeeee;'>
                Plataforma de Análisis Futbolístico Avanzado
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Descripción principal
        st.markdown("""
        <div style='text-align: center; max-width: 800px; margin: 0 auto; color: #ffffff;'>
            <p style='font-size: 16px; line-height: 1.6;'>
                Sistema profesional de análisis deportivo que combina <b>scraping de datos</b>, 
                <b>APIs en tiempo real</b> y <b>machine learning</b> para scouting y análisis táctico.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Funcionalidades con formato mejorado
        st.markdown("""
        <div style='background-color: rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 15px; max-width: 700px; margin: 25px auto;'>
            <h4 style='text-align: center; color: #ffffff; margin-bottom: 15px;'>FUNCIONALIDADES PRINCIPALES</h4>
            <ul style='text-align: left; color: #ffffff; font-size: 15px; padding-left: 20px;'>
                <li style='margin-bottom: 8px;'><b>Integración de datos:</b> FBref + API-Football</li>
                <li style='margin-bottom: 8px;'><b>Métricas avanzadas:</b> xG, xA, progresión de pases</li>
                <li style='margin-bottom: 8px;'><b>Talento juvenil:</b> Modelo para jugadores 16-22 años</li>
                <li><b>Reportes automatizados:</b> Generación de PDFs técnicos</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # Créditos con mejor contraste
        st.markdown("""
        <div style='text-align: center; margin-top: 40px; color: #bbbbbb; font-size: 14px;'>
            <p>
                Desarrollo técnico: <span style='color: #ffffff;'>Félix Ramírez Ramírez</span><br>
            </p>
        </div>
        """, unsafe_allow_html=True)

    elif section == "📊 Stats":
        stats_source = st.sidebar.radio("Datos desde:", ["API", "Scraping FBref"])
        if stats_source == "API":
            show_api_data()
        elif stats_source == "Scraping FBref":
            show_scraping_data()

    elif section == "🤖 Machine Learning":
        scouting_page()

if __name__ == "__main__":
    show_home()