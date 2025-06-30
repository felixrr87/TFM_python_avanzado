import streamlit as st
from backend.api_handler import FootballDataHandler
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
import traceback
from io import BytesIO
from backend.pdf_generator import create_pdf, clean_text

# Configuración
API_KEY = "18f8f363554247f69bba9b7a9d049da8"
COMPETITION = "PL"

def load_data():
    """Carga los datos de la API"""
    handler = FootballDataHandler(API_KEY)
    standings = handler.get_league_standings(COMPETITION)
    teams = handler.get_competition_teams(COMPETITION)
    
    if standings.empty or teams.empty:
        st.error("No se pudieron cargar los datos desde la API")
        return None, None
    
    merged_data = pd.merge(teams, standings, left_on='name', right_on='team', how='inner')
    return merged_data, handler

def show_standings_table(data):
    """Muestra la tabla de clasificación completa"""
    st.subheader("📊 Tabla de Clasificación - Premier League")
    st.dataframe(
        data[['position', 'name', 'played', 'won', 'draw', 'lost', 'goalsFor', 'goalsAgainst', 'goalDifference', 'points']],
        column_config={
            "position": "Posición",
            "name": "Equipo",
            "played": "PJ",
            "won": "G",
            "draw": "E",
            "lost": "P",
            "goalsFor": "GF",
            "goalsAgainst": "GC",
            "goalDifference": "DG",
            "points": "Pts"
        },
        hide_index=True,
        use_container_width=True
    )
    st.markdown("---")

def show_team_selector(data):
    """Muestra el selector de equipo en el sidebar"""
    st.sidebar.title("🔍 Seleccionar Equipo")
    selected_team = st.sidebar.selectbox(
        "Elige un equipo para ver detalles:",
        options=data['name'].sort_values().unique(),
        index=0
    )
    return selected_team

def show_team_stats(team_data, handler):
    """Muestra las estadísticas detalladas del equipo seleccionado"""
    if team_data.empty:
        st.warning("No se encontraron datos para este equipo.")
        return
    
    st.subheader(f"📊 Estadísticas de {team_data['name'].iloc[0]}")
    
    # Verificar datos
    if pd.isna(team_data['won'].iloc[0]) or pd.isna(team_data['draw'].iloc[0]) or pd.isna(team_data['lost'].iloc[0]):
        st.warning("Datos incompletos para este equipo. No se pueden mostrar gráficos.")
        return
    
    # Métricas básicas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Posición", int(team_data['position'].iloc[0]))
        st.metric("Puntos", int(team_data['points'].iloc[0]))
    with col2:
        st.metric("Partidos Jugados", int(team_data['played'].iloc[0]))
        st.metric("Diferencia de Goles", int(team_data['goalDifference'].iloc[0]))
    with col3:
        st.metric("Goles a Favor", int(team_data['goalsFor'].iloc[0]))
        st.metric("Goles en Contra", int(team_data['goalsAgainst'].iloc[0]))
    
    # Gráficos
    if team_data['played'].iloc[0] > 0:
        show_results_charts(team_data)
        show_goals_chart(team_data)
        show_team_matches(team_data['name'].iloc[0], team_data['id'].iloc[0], handler)

def show_results_charts(team_data):
    """Muestra gráficos de resultados (G-E-P)"""
    st.subheader("📈 Distribución de Resultados")
    
    results_data = {
        'Resultado': ['Ganados', 'Empatados', 'Perdidos'],
        'Cantidad': [
            int(team_data['won'].iloc[0]),
            int(team_data['draw'].iloc[0]),
            int(team_data['lost'].iloc[0])
        ]
    }
    
    fig, ax = plt.subplots(1, 2, figsize=(14, 5))
    ax[0].pie(results_data['Cantidad'], 
             labels=results_data['Resultado'], 
             autopct='%1.1f%%',
             colors=['#4CAF50', '#FFC107', '#F44336'])
    ax[0].set_title('Distribución de Resultados')
    
    sns.barplot(x='Resultado', y='Cantidad', data=pd.DataFrame(results_data), 
                palette=['#4CAF50', '#FFC107', '#F44336'], ax=ax[1])
    ax[1].set_title('Resultados por Cantidad')
    ax[1].set_ylabel('')
    
    st.pyplot(fig)
    plt.close()

def show_goals_chart(team_data):
    """Muestra gráfico comparativo de goles"""
    st.subheader("🥅 Estadísticas de Goles")
    
    goals_data = {
        'Tipo': ['Goles a Favor', 'Goles en Contra'],
        'Cantidad': [
            int(team_data['goalsFor'].iloc[0]),
            int(team_data['goalsAgainst'].iloc[0])
        ]
    }
    
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.barplot(x='Tipo', y='Cantidad', data=pd.DataFrame(goals_data), 
                palette=['#2196F3', '#F44336'])
    ax.set_title('Comparación de Goles')
    ax.set_ylabel('')
    st.pyplot(fig)
    plt.close()

def show_team_matches(team_name: str, team_id: int, handler):
    """Muestra los últimos partidos del equipo"""
    matches = handler.get_team_matches(team_id)
    
    if matches.empty:
        st.warning(f"No se encontraron partidos recientes para {team_name}.")
        return
    
    st.subheader(f"⏳ Últimos 5 partidos de {team_name}")
    
    for _, match in matches.head(5).iterrows():
        with st.expander(f"{match['date']}: {match['homeTeam']} {match['score']} {match['awayTeam']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Competición:** {match['competition']}")
                st.write(f"**Estado:** {match['status']}")
            with col2:
                if match['homeTeam'] == team_name:
                    st.write("🏠 **Partido como local**")
                    st.write(f"**Marcador:** {team_name} {match['score'].split('-')[0]} - {match['score'].split('-')[1]}")
                else:
                    st.write("✈️ **Partido como visitante**")
                    st.write(f"**Marcador:** {match['score'].split('-')[0]} - {team_name} {match['score'].split('-')[1]}")

def generate_pdf_report(team_data, selected_team):
    """Genera el reporte PDF en memoria con el formato específico para API"""
    def safe_get(value, default=0):
        try:
            return int(value) if not pd.isna(value) else default
        except (ValueError, TypeError):
            return default
    
    # Estructura de datos simplificada
    report_data = {
        "type": "api_team",
        "equipo": selected_team.replace('⚽', ''),  # Elimina emojis
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "stats": {
            "Posición": safe_get(team_data['position'].iloc[0]),
            "Puntos": safe_get(team_data['points'].iloc[0]),
            "Partidos Jugados": safe_get(team_data['played'].iloc[0]),
            "Diferencia de Goles": safe_get(team_data['goalDifference'].iloc[0]),
            "Goles a Favor": safe_get(team_data['goalsFor'].iloc[0]),
            "Goles en Contra": safe_get(team_data['goalsAgainst'].iloc[0])
        }
    }
    
    # Genera el PDF
    pdf_bytes = create_pdf(report_data, "api_team")
    
    # DEBUG: Guarda una copia temporal para inspección
    with open("debug_pdf.pdf", "wb") as f:
        f.write(pdf_bytes)
    
    return pdf_bytes, report_data

def show_api_data():
    """Función principal de la aplicación"""
    st.title("Premier League Dashboard")
    st.markdown("---")
    
    # Cargar datos
    data, handler = load_data()
    if data is None:
        return

    # Selector de equipo en sidebar
    selected_team = show_team_selector(data)
    
    # Mostrar tabla de clasificación
    show_standings_table(data)
    
    # Filtrar datos del equipo seleccionado
    team_data = data[data['name'] == selected_team]

    # Mostrar estadísticas del equipo seleccionado
    show_team_stats(team_data, handler)
    
    # --- Botón de exportación a PDF ---
    if st.button("📄 Exportar a PDF"):
        try:
            # Verificar si hay datos válidos
            if team_data.empty or pd.isna(team_data['played'].iloc[0]):
                st.warning("No hay datos suficientes para generar el reporte")
                return
                
            # Generar el PDF en memoria
            with st.spinner("Generando reporte PDF..."):
                pdf_bytes, report_data = generate_pdf_report(team_data, selected_team)
                
                # Mostrar botón de descarga
                st.success("✅ Reporte generado correctamente")
                
                # Crear botón de descarga que usa los bytes en memoria
                st.download_button(
                    label="⬇️ Descargar PDF ahora",
                    data=pdf_bytes,
                    file_name=f"Reporte_{selected_team}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
                
                # Opcional: Guardar también en disco
                if st.toggle("💾 Guardar copia en servidor", False):
                    os.makedirs("reports", exist_ok=True)
                    filename = f"reports/Reporte_{selected_team}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    with open(filename, "wb") as f:
                        f.write(pdf_bytes)
                    st.success(f"Copia guardada en: {filename}")
            
        except Exception as e:
            st.error(f"Error al exportar a PDF: {str(e)}")
            st.error(traceback.format_exc())