import streamlit as st
import plotly.graph_objects as go
import plotly.express as px 
from pathlib import Path
import pandas as pd
import time
import random
import logging
import base64
import os
import tempfile
from datetime import datetime
from backend.fbref_scraper import get_team_stats, get_player_stats
from backend.pdf_generator import create_pdf
from io import BytesIO

logger = logging.getLogger(__name__)

def manejar_error_scraping(error, tipo_analisis):
    """Maneja y muestra errores de scraping de manera amigable"""
    error_msg = str(error)
    
    st.error(f"⚠️ Error al obtener datos de {tipo_analisis}")
    
    if "HTTP" in error_msg:
        st.markdown("""
        **Parece que hay un problema de conexión:**
        - Verifica tu conexión a internet
        - FBref puede estar temporalmente no disponible
        """)
    elif "No se encontraron tablas" in error_msg:
        st.markdown("""
        **No se encontraron datos en la página:**
        - La estructura de FBref puede haber cambiado
        - Intenta con otra opción de análisis
        """)
    else:
        st.markdown(f"""
        **Error técnico:**
        ```python
        {error_msg}
        ```
        """)
    
    logger.error(f"Error en scraping de {tipo_analisis}: {error_msg}")
    
    if st.button("🔄 Reintentar", key=f"retry_{tipo_analisis}"):
        st.rerun()

def mostrar_mensaje_carga():
    """Muestra un mensaje de carga con animación"""
    with st.spinner("Obteniendo datos de FBref. Esto puede tomar unos segundos..."):
        time.sleep(random.uniform(1, 3))
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.02)
            progress_bar.progress(i + 1)
        progress_bar.empty()

def mostrar_comparativa_jugadores(df, pos_options, pos):
    """Muestra la comparativa entre jugadores seleccionados"""
    # Validar datos de entrada
    if df.empty:
        st.warning("No hay datos de jugadores para mostrar")
        return
        
    if pos not in pos_options and pos != "Todos":
        st.error(f"Posición {pos} no válida")
        return
        
    col1, col2 = st.columns(2)
    jugadores_list = df['Jugador'].unique().tolist()  # ← Nueva línea añadida
    jugador1 = col1.selectbox("Jugador 1", [""] + jugadores_list, index=0)
    jugador2 = col2.selectbox("Jugador 2", [""] + jugadores_list, index=0)

    if jugador1 != "" and jugador2 != "" and jugador1 == jugador2:
        st.warning("Selecciona dos jugadores distintos para comparar.")
        return

    jugadores_seleccionados = [j for j in [jugador1, jugador2] if j != ""]
    
    if len(jugadores_seleccionados) < 2:
        st.info("Selecciona dos jugadores para comparar")
        return
    
    # Filtrar datos de los jugadores seleccionados
    jugador1_df = df[df['Jugador'] == jugador1].iloc[0]
    jugador2_df = df[df['Jugador'] == jugador2].iloc[0]
    
    # Mostrar métricas clave
    st.markdown("### 📊 Comparativa Detallada")
    cols = st.columns(2)
    
    with cols[0]:
        st.markdown(f"#### {jugador1}")
        st.metric("Equipo", jugador1_df['Equipo'])
        st.metric("Edad", jugador1_df['Edad'])
        st.metric("Partidos jugados", jugador1_df['Partidos'])
        st.metric("Goles", jugador1_df['Goles'])
        st.metric("Asistencias", jugador1_df['Asistencias'])
        
    with cols[1]:
        st.markdown(f"#### {jugador2}")
        st.metric("Equipo", jugador2_df['Equipo'])
        st.metric("Edad", jugador2_df['Edad'])
        st.metric("Partidos jugados", jugador2_df['Partidos'])
        st.metric("Goles", jugador2_df['Goles'])
        st.metric("Asistencias", jugador2_df['Asistencias'])
    
    # Gráfico comparativo - actualizado con las nuevas métricas
    metricas_comparar = [
        'Partidos', 'Goles', 'Asistencias', 'Goles_Asistencias',
        'xG', 'xA', 'xG_xA_90', 'Progresivo_Regates', 'Progresivo_Pases'
    ]
    metricas_presentes = [m for m in metricas_comparar if m in df.columns]
    
    if metricas_presentes:
        st.markdown("### 📈 Comparativa de Métricas")
        
        # Preparar datos para el gráfico
        data = {
            'Metrica': [],
            'Valor': [],
            'Jugador': []
        }
        
        for metrica in metricas_presentes:
            data['Metrica'].append(metrica)
            data['Valor'].append(jugador1_df[metrica])
            data['Jugador'].append(jugador1)
            
            data['Metrica'].append(metrica)
            data['Valor'].append(jugador2_df[metrica])
            data['Jugador'].append(jugador2)
        
        # Crear gráfico
        fig = px.bar(
            pd.DataFrame(data),
            x='Metrica',
            y='Valor',
            color='Jugador',
            barmode='group',
            text='Valor',
            color_discrete_sequence=['#1f77b4', '#ff7f0e']
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': 'white', 'family': "Arial"},
            xaxis={
                'gridcolor': 'rgba(255,255,255,0.2)',
                'tickfont': {'color': 'white'},
                'title': {'font': {'color': 'white'}}
            },
            yaxis={
                'gridcolor': 'rgba(255,255,255,0.2)',
                'tickfont': {'color': 'white'},
                'title': {'font': {'color': 'white'}}
            },
            legend={'font': {'color': 'white'}},
            title=dict(
                text="<b>Comparativa de Métricas Clave</b>",
                font=dict(color='white', size=20),
                x=0.5,
                xanchor='center'
            ),
            height=500,
            margin=dict(l=50, r=50, b=100, t=100, pad=10)
        )
        
        fig.update_traces(
            texttemplate='%{text:.2f}',
            textposition='outside',
            textfont_size=14,
            marker_line_color='rgba(255,255,255,0.8)',
            marker_line_width=1.5,
            opacity=0.9
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Generación del PDF
        if st.button("📄 Generar Reporte PDF", key="generate_player_pdf"):
            with st.spinner("Generando PDF..."):
                try:
                    # Validar que la posición no sea "Todos"
                    posicion_pdf = pos_options.get(pos, "Varias posiciones")
                    
                    # Generar imagen del gráfico
                    img_bytes = fig.to_image(
                        format="png",
                        width=1000,
                        height=600,
                        scale=2,
                        engine="kaleido"
                    )
                    
                    if not img_bytes or len(img_bytes) < 1024:
                        raise ValueError("No se pudo generar la imagen del gráfico o está vacía")
                    
                    # Preparar datos para el PDF
                    report_data = {
                        "jugador1": jugador1,
                        "jugador2": jugador2,
                        "posicion": pos_options.get(pos, "Varias posiciones"),
                        "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "metricas_utilizadas": metricas_presentes,
                        "datos_comparacion": [
                            {m: jugador1_df.get(m, 'N/A') for m in metricas_presentes},
                            {m: jugador2_df.get(m, 'N/A') for m in metricas_presentes}
                        ],
                        "fig_comparativa": base64.b64encode(img_bytes).decode('utf-8'),
                        "conclusiones": [
                            f"Comparativa entre {jugador1} y {jugador2} en posición {pos}.",
                            f"Generado el {datetime.now().strftime('%Y-%m-%d a las %H:%M')}",
                            "Principales diferencias:",
                            f"- {jugador1} destaca en [métrica]",
                            f"- {jugador2} sobresale en [métrica]"
                        ]
                    }
                    # Generar PDF
                    pdf_bytes = create_pdf(report_data, "fbref_player")
                    
                    # Mostrar botón de descarga
                    st.success("✅ PDF generado correctamente")
                    st.download_button(
                        label="⬇️ Descargar PDF",
                        data=pdf_bytes,
                        file_name=f"Comparativa_{jugador1}_vs_{jugador2}.pdf",
                        mime="application/pdf"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Error al generar PDF: {str(e)}")
                    logger.error(f"Error en generación de PDF: {str(e)}", exc_info=True)
        
def mostrar_comparativa_equipos(df, equipos_seleccionados):
    """Muestra la comparativa entre equipos seleccionados con gráficos mejorados"""
    # Aseguramos nombres de columnas consistentes
    df = df.rename(columns={
        'Squad': 'Equipo',
        'Rk': 'LgRk',
        'MP': 'Partidos',
        'W': 'Victorias',
        'D': 'Empates',
        'L': 'Derrotas',
        'GF': 'Goles_Favor',
        'GA': 'Goles_Contra',
        'GD': 'Diferencia_Goles',
        'Pts': 'Puntos',
        'xG': 'xG',
        'xGA': 'xGA',
        'xGD': 'xGD',
        'xGD/90': 'xGD_90'
    })
    
    st.markdown("### 📊 Comparativa Detallada")
    
    # Mostrar métricas clave
    cols = st.columns(len(equipos_seleccionados))
    for idx, equipo in enumerate(equipos_seleccionados):
        equipo_df = df[df['Equipo'] == equipo]
        if not equipo_df.empty:
            with cols[idx]:
                st.markdown(f"#### {equipo}")
                metricas = [
                    ('⚽ Goles a favor', 'Goles_Favor'),
                    ('🛡️ Goles en contra', 'Goles_Contra'),
                    ('📊 Diferencia', 'Diferencia_Goles'),
                    ('🏆 Puntos', 'Puntos'),
                    ('🎯 xG', 'xG'),
                    ('🛡️ xGA', 'xGA')
                ]
                for nombre, columna in metricas:
                    if columna in equipo_df.columns:
                        valor = equipo_df[columna].values[0]
                        if isinstance(valor, float):
                            valor = f"{valor:.2f}"
                        st.metric(nombre, valor)

    # Configuración común para todos los gráficos
    config_graficos = {
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'font': {'color': 'white', 'family': "Arial"},
        'xaxis': {
            'gridcolor': 'rgba(255,255,255,0.2)',
            'tickfont': {'color': 'white'},
            'title': {'font': {'color': 'white'}}
        },
        'yaxis': {
            'gridcolor': 'rgba(255,255,255,0.2)',
            'tickfont': {'color': 'white'},
            'title': {'font': {'color': 'white'}}
        },
        'legend': {'font': {'color': 'white'}}
    }

    # Gráfico de barras comparativas
    columnas_numericas = ['LgRk','Partidos','Victorias','Empates','Derrotas','Goles_Favor','Goles_Contra', 'Diferencia_Goles', 'Puntos', 'xG', 'xGA']
    columnas_presentes = [col for col in columnas_numericas if col in df.columns]
    
    if columnas_presentes:
        st.markdown("### 📈 Comparativa de Métricas")
        fig_barras = go.Figure()
        
        colores = ['#FF6B6B', '#4ECDC4', '#FFBE0B', '#FB5607', '#8338EC', '#3A86FF']
        
        for i, equipo in enumerate(equipos_seleccionados):
            datos = df[df['Equipo'] == equipo][columnas_presentes].values[0]
            fig_barras.add_trace(
                go.Bar(
                    name=equipo,
                    x=columnas_presentes,
                    y=datos,
                    marker_color=colores[i % len(colores)],
                    text=[f"{v:.1f}" if isinstance(v, float) else str(v) for v in datos],
                    textposition='outside',
                    textfont={'color': 'white', 'size': 14},
                    marker_line_color='rgba(255,255,255,0.8)',
                    marker_line_width=1.5,
                    opacity=0.9,
                    width=0.4
                )
            )

        fig_barras.update_layout(
            **config_graficos,
            barmode='group',
            title=dict(
                text="<b>Comparativa de Métricas Clave</b>",
                font=dict(color='white', size=20),
                x=0.5,
                xanchor='center'
            ),
            height=500,
            margin=dict(l=50, r=50, b=100, t=100, pad=10),
            hoverlabel=dict(
                bgcolor="black",
                font_size=14,
                font_family="Arial"
            )
        )
        
        st.plotly_chart(fig_barras, use_container_width=True)

        # Generación del PDF - VERSIÓN CORREGIDA
        if st.button("📄 Generar Reporte PDF", key="generate_team_pdf"):
            with st.spinner("Generando PDF..."):
                try:
                    # 1. Validar que tenemos datos
                    if df.empty or not equipos_seleccionados:
                        raise ValueError("No hay datos para generar el reporte")
                    
                    # 2. Preparar datos de cada equipo
                    datos_equipos = {}
                    for equipo in equipos_seleccionados:
                        equipo_data = df[df['Equipo'] == equipo].iloc[0].to_dict()
                        datos_equipos[equipo] = equipo_data
                    
                    # 3. Generar imagen del gráfico
                    img_bytes = fig_barras.to_image(
                        format="png",
                        width=1000,
                        height=600,
                        scale=2,
                        engine="kaleido"
                    )
                    
                    if not img_bytes or len(img_bytes) < 1024:
                        raise ValueError("La imagen generada está vacía o es demasiado pequeña")
                    
                    # 4. Preparar datos para el PDF
                    report_data = {
                        "equipo": ", ".join(equipos_seleccionados),
                        "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "fig_comparativa": base64.b64encode(img_bytes).decode('utf-8'),
                        "datos_equipos": datos_equipos,
                        # Otras métricas específicas si son necesarias
                        "posicion_liga": [df[df['Equipo'] == e]['LgRk'].values[0] for e in equipos_seleccionados],
                        "puntos": [df[df['Equipo'] == e]['Puntos'].values[0] for e in equipos_seleccionados],
                        # ... otras métricas que necesites ...
                    }
                    
                    # 5. Generar PDF
                    pdf_bytes = create_pdf(report_data, "fbref_team")
                    
                    # 6. Mostrar botón de descarga
                    st.success("✅ PDF generado correctamente")
                    st.download_button(
                        label="⬇️ Descargar PDF",
                        data=pdf_bytes,
                        file_name=f"Reporte_{'_'.join(equipos_seleccionados)}.pdf",
                        mime="application/pdf"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Error al generar PDF: {str(e)}")
                    logger.error(f"Error en generación de PDF: {str(e)}", exc_info=True)
def show_scraping_data():
    """Función principal para mostrar datos de scraping"""
    st.sidebar.markdown("## ⚙️ Configuración")
    option = st.sidebar.radio("Tipo de análisis:", ["Equipos", "Jugadores"])
    
    if option == "Equipos":
        st.subheader("📊 Estadísticas de Equipos")
        try:
            mostrar_mensaje_carga()
            df = get_team_stats(index=0)
            
            if df is None or df.empty:
                st.warning("No se pudieron obtener datos de equipos")
                return
            
            if 'Equipo' not in df.columns:
                st.error("Los datos obtenidos no tienen la columna 'Equipo'")
                return
            
            st.dataframe(df.style.background_gradient(cmap='Blues'), height=400)
            
            st.markdown("---")
            st.markdown("### 🔍 Selecciona equipos para comparar")
            
            equipos = df['Equipo'].unique().tolist()
            
            if not equipos:
                st.warning("No se encontraron equipos para comparar")
                return
                
            col1, col2 = st.columns(2)
            equipo_1 = col1.selectbox("Equipo 1", [""] + equipos, index=0)
            equipo_2 = col2.selectbox("Equipo 2", [""] + equipos, index=0)

            if equipo_1 != "" and equipo_2 != "" and equipo_1 == equipo_2:
                st.warning("Selecciona dos equipos distintos para comparar.")
                return

            equipos_seleccionados = [e for e in [equipo_1, equipo_2] if e != ""]
            
            if equipos_seleccionados:
                mostrar_comparativa_equipos(df, equipos_seleccionados)
            else:
                st.info("Selecciona al menos un equipo para ver detalles.")

        except Exception as e:
            manejar_error_scraping(e, "equipos")
    
    elif option == "Jugadores":
        st.subheader("👤 Estadísticas de Jugadores")
        try:
            mostrar_mensaje_carga()
            
            # Primero obtener y mostrar todos los jugadores sin filtrar
            df = get_player_stats(index=0)
            
            if df is None or df.empty:
                st.warning("No se encontraron datos de jugadores")
                return
                
            st.dataframe(df.style.background_gradient(cmap='Blues'), height=400)
            
            st.markdown("---")
            
            # Luego añadir filtro por posición
            pos_options = {
                "GK": "Porteros",
                "DF": "Defensas", 
                "MF": "Centrocampistas",
                "FW": "Delanteros"
            }
            
            pos = st.selectbox("Filtrar por posición", 
                             options=["Todos"] + list(pos_options.keys()), 
                             format_func=lambda x: "Todos" if x == "Todos" else pos_options[x])
            
            # Aplicar filtro si no es "Todos"
            if pos != "Todos":
                if 'Posc' in df.columns:
                    df = df[df['Posc'] == pos]
                else:
                    st.warning("No se encontró la columna de posición en los datos")
                    return
            
            if df.empty:
                st.warning(f"No hay jugadores en la posición {pos_options.get(pos, pos)}")
                return
            
            # Mostrar comparativa
            mostrar_comparativa_jugadores(df, pos_options, pos)
            
        except Exception as e:
            manejar_error_scraping(e, "jugadores")
