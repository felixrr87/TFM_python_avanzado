import streamlit as st
import os
import time
import base64

# Función para establecer un fondo personalizado desde una imagen local
def add_bg_from_local(image_path):
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
    
    # Inyectamos CSS personalizado con la imagen de fondo y estilos generales
    st.markdown(
        f"""
        <style>
        /* Fondo de pantalla con imagen fija, centrada y cubierta */
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        /* Contenedor de login (no se está usando actualmente, puedes eliminarlo si no lo necesitas) */
        .login-container {{
            background-color: rgba(0, 0, 0, 0.7);
            padding: 2rem;
            border-radius: 20px;
            max-width: 400px;
            margin: 100px auto;
            box-shadow: 0 0 25px rgba(0, 255, 255, 0.3);
            text-align: center;
        }}

        /* Título principal */
        h1 {{
            color: #00ffff;
            font-family: 'Orbitron', sans-serif;
        }}

        /* Estilo para los campos de texto */
        .stTextInput>div>div>input {{
            background-color: rgba(255, 255, 255, 0.2);
            color: black;
        }}

        /* Estilo para las etiquetas de los campos */
        label {{
            color: white !important;
            font-weight: bold;
        }}

        /* Botón principal (Entrar) */
        button[kind="primary"] {{
            background-color: red;
            color: black;
            font-weight: bold;
            border-radius: 10px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Función que muestra la pantalla de login
def show_login():
    add_bg_from_local("assets/background.jpg")

    # Contenedor principal centrado
    st.markdown("""
    <div style='display: flex; flex-direction: column; align-items: center;'>
    """, unsafe_allow_html=True)

    # Logo perfectamente centrado
    logo_base64 = base64.b64encode(open("assets/sportalyze.png", "rb").read()).decode()
    st.markdown(f"""
    <div style='display: flex; justify-content: center; width: 100%; margin-bottom: 20px;'>
        <img src='data:image/png;base64,{logo_base64}' width='300'>
    </div>
    """, unsafe_allow_html=True)

    # Título
    st.markdown(
        "<h1 style='text-align: center; color: white; margin-bottom: 20px;'>Bienvenido a SPORTALYZE</h1>",
        unsafe_allow_html=True
    )

    # CSS corregido
    st.markdown("""
    <style>
        /* Inputs */
        .stTextInput {
            max-width: 300px;
            margin: 0 auto;
        }
        
        .stTextInput>div>div>input {
            width: 100%;
            height: 38px;
            padding: 8px 12px;
            border: 1px solid #ccc;
            border-radius: 6px;
            background-color: white;
            font-size: 14px;
        }
        
        .stTextInput>label {
            width: 100%;
            text-align: center;
            color: white;
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 8px;
        }
        
        /* Botón */
        div.stButton>button {
            display: block;
            margin: 15px auto 0 auto;
            width: 250px;
            height: 42px;
            border-radius: 8px;
            background-color: #00ffe0;
            color: black;
            font-weight: bold;
            border: none;
            transition: all 0.3s;
        }
        
        div.stButton>button:hover {
            background-color: #00ccbb;
        }
    </style>
    """, unsafe_allow_html=True)

    # Campos de entrada
    usuario = st.text_input("Usuario")
    contraseña = st.text_input("Contraseña", type="password")

    # Botón de login
    if st.button("Entrar"):
        if usuario == "admin" and contraseña == "admin":
            st.session_state.logged_in = True
            st.success("Acceso concedido")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

    st.markdown("</div>", unsafe_allow_html=True)