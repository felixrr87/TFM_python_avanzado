import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from backend.ml_model import get_player_ml
from fpdf import FPDF
import base64
from io import BytesIO
import tempfile
import os
from backend.pdf_generator import create_ml_scouting_pdf
from backend.pdf_generator import create_pdf

from datetime import datetime
# Configuración de colores y estilo
COLORES = {
    'DF': px.colors.qualitative.Vivid[0],
    'MF': px.colors.qualitative.Vivid[1],
    'FW': px.colors.qualitative.Vivid[2],
    'GK': px.colors.qualitative.Vivid[3]
}

METRICAS_POR_POSICION = {
    'DF': ['MP', 'Gls', 'Ast', 'CrdY'],
    'MF': ['MP', 'Gls', 'Ast', 'xG', 'xAG'],
    'FW': ['MP', 'Gls', 'xG', 'G+A', 'npxG'],
    'GK': ['MP', 'Starts', 'Min', 'CrdY', 'PKatt']
}

class PDF(FPDF):
    """Clase personalizada para generar PDFs con estilo oscuro."""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(left=10, top=10, right=10)
        self.set_draw_color(255, 255, 255)  # Bordes blancos
        self.set_fill_color(0, 0, 0)        # Fondo negro
        self.set_text_color(255, 255, 255)  # Texto blanco

    def header(self):
        """Encabezado personalizado para cada página."""
        self.set_fill_color(0, 0, 0)
        self.rect(0, 0, self.w, 20, 'F')
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, '⚽ Scouting de Jugadores Jóvenes (16-22 años)', 0, 1, 'C')
        self.ln(15)

    def footer(self):
        """Pie de página personalizado."""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def aplicar_estilo_color(val, min_val, max_val):
    """Aplica un gradiente de color rojo según el valor"""
    if pd.isna(val) or max_val == min_val:
        return 'background-color: white'
    normalized = (val - min_val) / (max_val - min_val)
    r = 255
    g = int(255 * (1 - normalized))
    b = int(255 * (1 - normalized))
    return f'background-color: rgba({r},{g},{b},0.7); color: black'

def generar_pdf(fig, df_seleccionados, posicion_seleccionada):
    """Genera un PDF con el gráfico y la tabla de jugadores seleccionados"""
    pdf = PDF()
    pdf.add_page()
    
    # Título del reporte
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Scouting de {posicion_seleccionada}", 0, 1, 'C')
    pdf.ln(10)
    
    # Guardar el gráfico como imagen temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmpfile:
        fig.write_image(tmpfile.name, width=800, height=500)
        pdf.image(tmpfile.name, x=10, w=190)
        os.unlink(tmpfile.name)
    
    pdf.ln(10)
    
    # Tabla de jugadores seleccionados
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Detalle de Jugadores Seleccionados", 0, 1)
    pdf.ln(5)
    
    # Configuración de la tabla
    col_widths = [60, 30, 30] + [30] * (len(df_seleccionados.columns) - 3)
    row_height = 8
    
    # Cabecera
    pdf.set_font("Arial", 'B', 10)
    for col in df_seleccionados.columns:
        pdf.cell(col_widths[df_seleccionados.columns.get_loc(col)], row_height, str(col)[:15], border=1)
    pdf.ln(row_height)
    
    # Datos
    pdf.set_font("Arial", size=8)
    for _, row in df_seleccionados.iterrows():
        for col in df_seleccionados.columns:
            valor = row[col]
            pdf.cell(col_widths[df_seleccionados.columns.get_loc(col)], row_height, str(valor)[:15], border=1)
        pdf.ln(row_height)
    
    # Guardar el PDF en un buffer
    pdf_buffer = BytesIO()
    pdf_buffer.write(pdf.output(dest='S').encode('latin1'))
    pdf_buffer.seek(0)
    
    return pdf_buffer

def scouting_page():
    st.title("Scouting de Jugadores Jóvenes (16-22 años)")
    
    with st.spinner("Cargando datos de jugadores..."):
        try:
            df = get_player_ml(index=0)
            
            if df.empty:
                st.warning("No se encontraron datos de jugadores")
                return
                
            # Convertir edad a enteros y limpiar datos
            df['Age'] = df['Age'].astype(int)
            
            # Asegurar que las métricas sean numéricas
            for pos, metrics in METRICAS_POR_POSICION.items():
                for metric in metrics:
                    if metric in df.columns:
                        df[metric] = pd.to_numeric(df[metric], errors='coerce')
            
            st.write(f"Total de jugadores jóvenes cargados: {len(df)}")
            
            # --- FILTROS ---
            st.sidebar.header("Filtros")
            
            # 1. Selección de posición
            posiciones_disponibles = sorted(df['Pos'].dropna().unique())
            posicion_seleccionada = st.sidebar.selectbox(
                "Seleccionar posición",
                options=posiciones_disponibles,
                index=0
            )
            
            # 2. Rango de edad (dentro de 16-22)
            edad_min, edad_max = st.sidebar.slider(
                "Rango de edad a analizar",
                min_value=16,
                max_value=22,
                value=(16, 22)
            )
            
            # --- APLICAR FILTROS ---
            mask = (df['Pos'] == posicion_seleccionada) & (df['Age'] >= edad_min) & (df['Age'] <= edad_max)
            df_filtrado = df[mask].sort_values('Gls', ascending=False)
            
            # --- MOSTRAR TABLA COMPLETA CON COLORES ---
            st.write(f"**Jugadores {posicion_seleccionada} que cumplen los criterios ({len(df_filtrado)}):**")
            
            if not df_filtrado.empty:
                # Aplicar estilo de colores a TODAS las columnas numéricas
                numeric_cols = df_filtrado.select_dtypes(include=[np.number]).columns.tolist()
                
                # Crear un estilo para cada columna numérica
                styles = []
                for col in numeric_cols:
                    if col in df_filtrado.columns:
                        min_val = df_filtrado[col].min()
                        max_val = df_filtrado[col].max()
                        styles.append({
                            col: [aplicar_estilo_color(x, min_val, max_val) for x in df_filtrado[col]]
                        })
                
                # Aplicar todos los estilos
                styled_df = df_filtrado.style
                for style in styles:
                    for col, props in style.items():
                        styled_df = styled_df.apply(lambda x: props, subset=[col])
                
                st.dataframe(
                    styled_df,
                    height=600,
                    use_container_width=True
                )
                
                # --- SELECCIÓN DE JUGADORES PARA COMPARAR ---
                st.markdown("---")
                st.subheader("Comparativa de Jugadores")
                
                jugadores_comparar = st.multiselect(
                    "Selecciona jugadores para comparar (máx. 5)",
                    options=df_filtrado['Player'].tolist(),
                    default=df_filtrado['Player'].head(3).tolist(),
                    max_selections=5
                )
                
                if jugadores_comparar:
                    df_comparacion = df_filtrado[df_filtrado['Player'].isin(jugadores_comparar)]
                    
                    # --- GRÁFICO DE COMPARACIÓN ---
                    st.subheader(f"Comparativa de {posicion_seleccionada}")
                    
                    # Seleccionar métricas relevantes para la posición
                    metricas_comparacion = [m for m in METRICAS_POR_POSICION.get(posicion_seleccionada, []) 
                                          if m in df_comparacion.columns]
                    
                    if not metricas_comparacion:
                        st.warning("No hay métricas disponibles para comparar")
                    else:
                        # Paleta de colores más vivos
                        colores_vivos = px.colors.qualitative.Vivid
                        
                        fig = px.bar(
                            df_comparacion,
                            x='Player',
                            y=metricas_comparacion,
                            barmode='group',
                            title=f'Comparativa de {posicion_seleccionada}',
                            labels={'value': 'Valor', 'variable': 'Métrica'},
                            color_discrete_sequence=colores_vivos,
                            height=500,
                            opacity=0.85
                        )
                        
                        # Configuración completa del estilo
                        fig.update_layout(
                            xaxis_title="Jugador",
                            yaxis_title="Valor",
                            legend_title="Métricas",
                            hovermode="x unified",
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='white', size=12),
                            xaxis=dict(
                                tickfont=dict(color='white'),
                                title_font=dict(color='white')
                            ),
                            yaxis=dict(
                                tickfont=dict(color='white'),
                                title_font=dict(color='white')
                            ),
                            legend=dict(
                                font=dict(color='white'),
                                title_font=dict(color='white')
                            ),
                            title_font=dict(color='white'),
                            margin=dict(l=20, r=20, t=60, b=20)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # --- TABLA DE JUGADORES SELECCIONADOS ---
                        st.markdown("---")
                        st.subheader("Detalle de Jugadores Seleccionados")
                        
                        # Seleccionar columnas a mostrar
                        columnas_base = ['Player', 'Age', 'Squad', 'Nation']
                        columnas_mostrar = columnas_base + metricas_comparacion
                        
                        # Crear tabla con estilo
                        df_seleccionados = df_comparacion[columnas_mostrar].copy()
                        
                        # Aplicar estilo de colores solo a las métricas
                        styles_seleccionados = []
                        for col in metricas_comparacion:
                            if col in df_seleccionados.columns:
                                min_val = df_seleccionados[col].min()
                                max_val = df_seleccionados[col].max()
                                styles_seleccionados.append({
                                    col: [aplicar_estilo_color(x, min_val, max_val) for x in df_seleccionados[col]]
                                })
                        
                        # Aplicar estilos
                        styled_seleccionados = df_seleccionados.style
                        for style in styles_seleccionados:
                            for col, props in style.items():
                                styled_seleccionados = styled_seleccionados.apply(lambda x: props, subset=[col])
                        
                        st.dataframe(
                            styled_seleccionados,
                            height=(35 + 35 * len(df_seleccionados)),
                            use_container_width=True
                        )
                        
                        # --- BOTÓN DE GENERAR PDF ---
                        st.markdown("---")
                        if st.button("📄 Generar Reporte PDF"):
                            with st.spinner("Generando PDF..."):
                                try:
                                    # Limpiar datos antes de crear el PDF
                                    df_comparacion_clean = df_comparacion.fillna('').copy()
                                    
                                    report_data = {
                                        "fig": fig,
                                        "jugadores": df_comparacion_clean.to_dict('records'),
                                        "posicion": posicion_seleccionada,
                                        "metricas": metricas_comparacion,
                                        "fecha": datetime.now().strftime("%Y-%m-%d")
                                    }
                                    
                                    pdf_bytes = create_pdf(report_data, "ml_scouting")
                                    
                                    st.success("PDF generado correctamente")
                                    st.download_button(
                                        label="⬇️ Descargar PDF",
                                        data=pdf_bytes,
                                        file_name=f"scouting_{posicion_seleccionada}.pdf",
                                        mime="application/pdf"
                                    )
                                except Exception as e:
                                    st.error(f"Error al generar PDF: {str(e)}")
            else:
                st.warning("No hay jugadores que coincidan con los filtros seleccionados")
                
        except Exception as e:
            st.error(f"Error al cargar datos: {str(e)}")
            st.error("Por favor intenta recargar la página o verifica tu conexión a internet")