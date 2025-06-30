from fpdf import FPDF
import plotly.io as pio
from io import BytesIO
import tempfile
import base64
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import logging
import os
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)

## Función clean_text movida al nivel superior para poder importarla
def clean_text(text):
    """Limpia caracteres especiales y emojis para evitar problemas de codificación"""
    if not isinstance(text, str):
        text = str(text)
    
    # Tabla de reemplazos ampliada
    replacements = {
        'š': 's', 'ć': 'c', 'č': 'c', 'ž': 'z', 'đ': 'dj',
        'Š': 'S', 'Ć': 'C', 'Č': 'C', 'Ž': 'Z', 'Đ': 'Dj',
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N',
        '⚽': 'Fútbol', '📊': '[CHART]', '📈': '[GRAPH]',
        '🥅': '[GOAL]', '⏳': '[CLOCK]', '🔍': '[SEARCH]',
        '🏠': '[HOME]', '✈️': '[AWAY]', '📄': '[DOC]',
        '⬇️': '[DOWN]', '💾': '[SAVE]'
    }
    
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    
    return text

class PDF(FPDF):
    """Clase PDF con tema oscuro"""
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(left=10, top=10, right=10)
        # Configuración inicial de colores
        self.set_draw_color(255, 255, 255)  # Bordes blancos
        self.set_text_color(255, 255, 255)  # Texto blanco
        self.set_fill_color(0, 0, 0)        # Fondo negro
        
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Reporte de Scouting', 0, 1, 'C')
        self.ln(10)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def add_page(self, orientation=''):
        super().add_page(orientation)
        # Fondo negro para toda la página
        self.set_fill_color(0, 0, 0)
        self.rect(0, 0, self.w, self.h, 'F')
        self.set_text_color(255, 255, 255)  # Asegurar texto blanco
        
class DarkPDF(FPDF):
    """Versión con tema oscuro para scouting"""
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(left=10, top=10, right=10)
        self.set_draw_color(255, 255, 255)
        self.set_fill_color(0, 0, 0)
        self.set_text_color(255, 255, 255)

    def header(self):
        self.set_fill_color(0, 0, 0)
        self.rect(0, 0, self.w, 20, 'F')
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Reporte de Scouting', 0, 1, 'C')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def add_page(self, orientation=''):
        super().add_page(orientation)
        self.set_fill_color(0, 0, 0)
        self.rect(0, 0, self.w, self.h, 'F')

def _generate_error_pdf(error_msg: str) -> bytes:
    """Genera un PDF de error"""
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Error generando reporte", 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    clean_msg = error_msg.encode('utf-8', errors='replace').decode('latin1')
    pdf.multi_cell(0, 10, f"Se produjo un error al generar el reporte:\n\n{clean_msg}")
    return pdf.output(dest='S').encode('utf-8')

def create_api_team_pdf(report_data: Dict[str, Any]) -> bytes:
    """Genera PDF para equipos desde API con tema oscuro"""
    pdf = PDF()
    pdf.add_page()
    
    try:
        # Configuración de texto
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Premier League Dashboard", 0, 1, 'C')
        pdf.ln(10)
        
        # Nombre del equipo
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, f"Estadísticas de {report_data['equipo']}", 0, 1, 'L')
        pdf.ln(8)
        
        # Fecha
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 8, f"Fecha del reporte: {report_data['fecha']}", 0, 1, 'L')
        pdf.ln(15)
        
        # Configuración de la tabla
        col_width = 90
        row_height = 10
        stats = report_data['stats']
        
        # Encabezados de tabla
        pdf.set_font("Arial", 'B', 12)
        pdf.set_fill_color(30, 30, 30)  # Gris oscuro para encabezados
        pdf.cell(col_width, row_height, "Métrica", border=1, fill=True)
        pdf.cell(col_width, row_height, "Valor", border=1, fill=True)
        pdf.ln(row_height)
        
        # Datos de la tabla
        pdf.set_font("Arial", size=12)
        metrics = [
            ("Posición", stats["Posición"]),
            ("Puntos", stats["Puntos"]),
            ("Partidos Jugados", stats["Partidos Jugados"]),
            ("Diferencia de Goles", stats["Diferencia de Goles"]),
            ("Goles a Favor", stats["Goles a Favor"]),
            ("Goles en Contra", stats["Goles en Contra"])
        ]
        
        for i, (metric, value) in enumerate(metrics):
            # Alternar colores de fila (grises oscuros)
            pdf.set_fill_color(20, 20, 20) if i % 2 == 0 else pdf.set_fill_color(40, 40, 40)
            pdf.cell(col_width, row_height, metric, border=1, fill=True)
            pdf.cell(col_width, row_height, str(value), border=1, fill=True)
            pdf.ln(row_height)
        
        return pdf.output(dest='S').encode('latin1', errors='replace')
        
    except Exception as e:
        logger.error(f"Error generando PDF: {str(e)}")
        return _generate_error_pdf(str(e))
    
def _create_team_pdf(pdf: PDF, report_data: Dict[str, Any]) -> None:
    """Crea PDF para comparativa de equipos con gestión inteligente de espacio"""
    try:
        # Configuración inicial
        pdf.set_fill_color(0, 0, 0)
        pdf.rect(0, 0, pdf.w, pdf.h, 'F')
        pdf.set_text_color(255, 255, 255)
        
        # Margen superior
        pdf.set_y(15)
        
        # 1. Sección de encabezado (compacta)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 8, "Comparativa de Equipos", 0, 1, 'C')
        
        equipos = report_data.get('equipo', 'Equipos').split(', ')
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 6, f"Equipos: {', '.join(equipos)}", 0, 1, 'C')
        
        pdf.set_font("Arial", size=8)
        pdf.cell(0, 5, f"Fecha: {report_data.get('fecha_creacion', 'N/A')}", 0, 1)
        pdf.ln(5)
        
        # 2. Insertar gráfico (tamaño flexible)
        y_pos_antes_grafico = pdf.get_y()
        
        if 'fig_comparativa' in report_data and report_data['fig_comparativa']:
            try:
                img_data = base64.b64decode(report_data['fig_comparativa'])
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                    tmp_img.write(img_data)
                    
                    # Altura del gráfico basada en espacio disponible
                    espacio_disponible = pdf.h - y_pos_antes_grafico - 40  # 40mm para sección inferior
                    altura_grafico = min(90, espacio_disponible)  # Máximo 90mm, mínimo lo que quepa
                    
                    pdf.image(tmp_img.name, x=10, y=pdf.get_y(), w=pdf.w-20, h=altura_grafico)
                    os.unlink(tmp_img.name)
                
                pdf.set_y(pdf.get_y() + altura_grafico + 2)
                pdf.set_font("Arial", 'I', 7)
                pdf.cell(0, 4, "Comparativa de métricas clave", 0, 1, 'C')
                pdf.ln(3)
            except Exception as e:
                logger.error(f"Error al insertar gráfico: {str(e)}")
                pdf.set_font("Arial", size=8)
                pdf.cell(0, 5, f"Error al cargar el gráfico", 0, 1)
                pdf.ln(5)
        
        # 3. Verificar si hay espacio para la tabla
        espacio_restante = pdf.h - pdf.get_y() - 20  # 20mm para margen inferior
        altura_tabla_estimada = 6 * 9  # 6mm por fila × 9 filas (encabezado + 8 métricas)
        
        if espacio_restante < altura_tabla_estimada:
            # No cabe - crear nueva página
            pdf.add_page()
            pdf.set_y(15)  # Restablecer posición Y en nueva página
        
        # 4. Sección de estadísticas detalladas
        _crear_tabla_estadisticas(pdf, report_data)
        
    except Exception as e:
        logger.error(f"Error crítico al generar PDF: {str(e)}")
        raise

def _crear_tabla_estadisticas(pdf: PDF, report_data: Dict[str, Any]) -> None:
    """Crea la tabla de estadísticas detalladas"""
    equipos = report_data.get('equipo', 'Equipos').split(', ')
    datos_equipos = report_data.get('datos_equipos', {})
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 6, "Estadísticas Detalladas", 0, 1)
    pdf.ln(3)
    
    if not datos_equipos:
        pdf.set_font("Arial", size=8)
        pdf.cell(0, 5, "No se encontraron datos completos", 0, 1)
        return
    
    # Configuración de tabla
    col_width = (pdf.w - 30) / (len(equipos) + 1)
    row_height = 6
    
    # Encabezado
    pdf.set_fill_color(50, 50, 50)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(30, row_height, "Métrica", border=1, fill=True)
    
    for equipo in equipos:
        pdf.cell(col_width, row_height, equipo[:12], border=1, fill=True)
    pdf.ln(row_height)
    
    # Métricas a mostrar
    metricas = [
        ('Pos', 'LgRk'),
        ('Pts', 'Puntos'),
        ('PJ', 'Partidos'),
        ('GF', 'Goles_Favor'),
        ('GC', 'Goles_Contra'),
        ('Dif', 'Diferencia_Goles'),
        ('xG', 'xG'),
        ('xGA', 'xGA')
    ]
    
    # Filas de datos
    pdf.set_font("Arial", size=7)
    for i, (nombre_metrica, clave_metrica) in enumerate(metricas):
        fill_color = (30, 30, 30) if i % 2 == 0 else (40, 40, 40)
        pdf.set_fill_color(*fill_color)
        
        pdf.cell(30, row_height, nombre_metrica, border=1, fill=True)
        
        for equipo in equipos:
            valor = datos_equipos.get(equipo, {}).get(clave_metrica, 'N/A')
            if isinstance(valor, float):
                valor = f"{valor:.1f}"
            pdf.cell(col_width, row_height, str(valor), border=1, fill=True)
        
        pdf.ln(row_height)
            
def create_player_comparison_pdf(report_data: Dict[str, Any]) -> bytes:
    """Genera PDF de comparación entre jugadores"""
    pdf = PDF()
    pdf.add_page()
    
    try:
        # 1. Encabezado
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Comparativa de Jugadores", 0, 1, 'C')
        pdf.ln(5) 

        # Info básica (jugadores, posición, fecha)
        pdf.set_font("Arial", size=10)  # Fuente más pequeña
        pdf.cell(0, 6, f"Jugador 1: {report_data['jugador1']}", 0, 1)
        pdf.cell(0, 6, f"Jugador 2: {report_data['jugador2']}", 0, 1)
        pdf.cell(0, 6, f"Posición: {report_data['posicion']}", 0, 1)
        pdf.cell(0, 6, f"Fecha: {report_data['fecha_creacion']}", 0, 1)
        pdf.ln(8)  

        # 2. Gráfico 
        if 'fig_comparativa' in report_data and report_data['fig_comparativa']:
            try:
                img_data = base64.b64decode(report_data['fig_comparativa'])
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmpfile:
                    tmpfile.write(img_data)
                    pdf.image(tmpfile.name, x=10, w=pdf.w - 20, h=90)
                    os.unlink(tmpfile.name)
                pdf.ln(5)
            except Exception as e:
                logger.error(f"Error al insertar gráfico: {str(e)}")

        # 3. Tabla de métricas
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "Métricas Comparadas", 0, 1, 'C')
        pdf.ln(5)

        metricas = report_data.get('metricas_utilizadas', [])
        datos_jugadores = report_data.get('datos_comparacion', [])

        if metricas and len(datos_jugadores) >= 2:
            # Configuración de la tabla
            col_widths = [60, 40, 40]  # Ajuste de anchos
            row_height = 8
            pdf.set_font("Arial", size=8)  # Fuente más pequeña

            # Encabezados
            pdf.set_fill_color(50, 50, 50)
            pdf.cell(col_widths[0], row_height, "Métrica", border=1, fill=True)
            pdf.cell(col_widths[1], row_height, report_data['jugador1'][:12], border=1, fill=True)
            pdf.cell(col_widths[2], row_height, report_data['jugador2'][:12], border=1, fill=True)
            pdf.ln(row_height)

            # Datos
            for i, metrica in enumerate(metricas):
                fill_color = (30, 30, 30) if i % 2 == 0 else (40, 40, 40)
                pdf.set_fill_color(*fill_color)

                val1 = datos_jugadores[0].get(metrica, 'N/A')
                val2 = datos_jugadores[1].get(metrica, 'N/A')

                if isinstance(val1, float):
                    val1 = f"{val1:.2f}"
                if isinstance(val2, float):
                    val2 = f"{val2:.2f}"

                pdf.cell(col_widths[0], row_height, metrica, border=1, fill=True)
                pdf.cell(col_widths[1], row_height, str(val1), border=1, fill=True)
                pdf.cell(col_widths[2], row_height, str(val2), border=1, fill=True)
                pdf.ln(row_height)

    except Exception as e:
        logger.error(f"Error en create_player_comparison_pdf: {str(e)}", exc_info=True)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Error al generar el PDF: {str(e)[:100]}", 0, 1)

    return pdf.output(dest='S').encode('latin1', errors='replace')

def create_ml_scouting_pdf(report_data: Dict[str, Any]) -> bytes:
    """Genera PDF para scouting con machine learning"""
    pdf = DarkPDF()
    pdf.add_page()
    
    try:
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, clean_text("Reporte de Scouting - Modelo ML"), 0, 1, 'C')
        pdf.ln(8)
        
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, clean_text(f"Posición: {report_data.get('posicion', 'N/A')}"), 0, 1)
        pdf.cell(0, 10, clean_text(f"Fecha: {report_data.get('fecha', 'N/A')}"), 0, 1)
        pdf.ln(15)

        if 'fig' in report_data:
            try:
                fig = report_data['fig']
                fig.update_layout({
                    'plot_bgcolor': 'rgba(0,0,0,0)',
                    'paper_bgcolor': 'rgba(0,0,0,0)'
                })
                
                img_bytes = pio.to_image(fig, format='png', width=800)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmpfile:
                    tmpfile.write(img_bytes)
                    pdf.image(tmpfile.name, x=10, w=190)
                    os.unlink(tmpfile.name)
                
                pdf.ln(10)
                pdf.set_font("Arial", 'I', 10)
                pdf.cell(0, 8, clean_text("Comparativa de métricas clave"), 0, 1, 'C')
                pdf.ln(15)
            except Exception as e:
                logger.error(f"Error gráfico: {str(e)}")
                pdf.set_font("Arial", 'I', 10)
                pdf.cell(0, 8, clean_text("Gráfico no disponible"), 0, 1)

        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, clean_text("Jugadores Recomendados"), 0, 1, 'C')
        pdf.ln(10)
        
        jugadores = report_data.get('jugadores', [])
        metricas = report_data.get('metricas', [])
        
        if jugadores and metricas:
            col_widths = [50] + [30] * len(metricas)
            
            pdf.set_fill_color(50, 50, 50)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(col_widths[0], 10, clean_text("Jugador"), border=1, fill=True)
            for metrica in metricas:
                pdf.cell(col_widths[1], 10, clean_text(metrica)[:8], border=1, fill=True)
            pdf.ln()
            
            pdf.set_font("Arial", size=9)
            for idx, jugador in enumerate(jugadores):
                pdf.set_fill_color(30, 30, 30) if idx % 2 == 0 else pdf.set_fill_color(50, 50, 50)
                
                pdf.cell(col_widths[0], 8, clean_text(jugador.get('Player', '')[:20]), border=1, fill=True)
                for metrica in metricas:
                    valor = str(jugador.get(metrica, ''))[:6]
                    pdf.cell(col_widths[1], 8, clean_text(valor), border=1, fill=True)
                pdf.ln()
        else:
            pdf.set_font("Arial", 'I', 12)
            pdf.cell(0, 10, clean_text("No hay datos de jugadores"), 0, 1)
            
    except Exception as e:
        logger.error(f"Error crítico al generar PDF: {str(e)}")
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, clean_text(f"Error al generar reporte: {str(e)[:100]}"), 0, 1)
    
    return pdf.output(dest='S').encode('latin-1', errors='replace')

def create_pdf(report_data: Dict[str, Any], report_type: str) -> bytes:
    """Función principal para crear PDFs"""
    try:
        if report_type == "api_team":
            return create_api_team_pdf(report_data)
            
        elif report_type == "fbref_team":
            # Validación de datos esenciales
            required_keys = ['equipo', 'fecha_creacion', 'datos_equipos']
            if not all(k in report_data for k in required_keys):
                raise ValueError(f"Datos incompletos para reporte de equipo. Faltan: {[k for k in required_keys if k not in report_data]}")
            
            pdf = PDF()
            pdf.add_page()
            _create_team_pdf(pdf, report_data)
            return pdf.output(dest='S').encode('latin1', errors='replace')
            
        elif report_type == "fbref_player":
            return create_player_comparison_pdf(report_data)
            
        elif report_type == "ml_scouting":
            return create_ml_scouting_pdf(report_data)
            
        else:
            raise ValueError(f"Tipo de reporte desconocido: {report_type}")
            
    except Exception as e:
        logger.error(f"Error generando PDF: {str(e)}", exc_info=True)
        return _generate_error_pdf(str(e))