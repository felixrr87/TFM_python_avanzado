from bs4 import BeautifulSoup, Comment
import pandas as pd
import cloudscraper
import re
import time
import random
import logging
from datetime import datetime
from typing import Optional, List
from backend.pdf_generator import clean_text

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

__all__ = [
    'get_team_stats',
    'get_player_stats',
    'print_table_summaries', 
    'get_tables_from_fbref',
    'get_specific_table'
]

class FBrefError(Exception):
    """Excepción personalizada para errores de FBref"""
    pass

def get_tables_from_fbref(url: str, max_retries: int = 3) -> Optional[List]:
    """Obtiene tablas HTML de FBref con manejo de errores y delays aleatorios
    
    Args:
        url: URL de la página a scrapear
        max_retries: Número máximo de reintentos
        
    Returns:
        Lista de tablas HTML encontradas o None si falla
    """
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9',
        'Referer': 'https://www.google.com/'
    }

    for attempt in range(max_retries):
        try:
            delay = random.uniform(2, 8)
            logger.info(f"Intento {attempt + 1}: Esperando {delay:.1f}s antes de scrapear...")
            time.sleep(delay)
            
            response = scraper.get(url, headers=headers, timeout=20)
            
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 30))
                logger.warning(f"Rate limit alcanzado. Esperando {retry_after}s...")
                time.sleep(retry_after)
                continue
                
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all('table')
            
            # Buscar tablas en comentarios
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment_soup = BeautifulSoup(comment, 'html.parser')
                tables.extend(comment_soup.find_all('table'))
                
            if not tables:
                raise FBrefError("No se encontraron tablas en la página")
                
            return tables
            
        except Exception as e:
            logger.error(f"Intento {attempt + 1} fallido: {str(e)}")
            if attempt == max_retries - 1:
                raise FBrefError(f"Error después de {max_retries} intentos: {str(e)}")
            time.sleep(random.uniform(5, 10))
    
    return None
    
def get_specific_table(url: str, index: int = 0, header_row: int = 1) -> pd.DataFrame:
    """Extrae una tabla específica y la devuelve como DataFrame
    
    Args:
        url: URL de la página
        index: Índice de la tabla a extraer
        header_row: Fila a usar como encabezado
        
    Returns:
        DataFrame con los datos de la tabla
    """
    tables = get_tables_from_fbref(url)
    
    if not tables:
        raise FBrefError("No se encontraron tablas en la URL proporcionada")
        
    if index >= len(tables):
        raise IndexError(f"Índice {index} fuera de rango. Hay {len(tables)} tablas disponibles")

    try:
        df = pd.read_html(str(tables[index]), header=header_row)[0]
        logger.info(f"Tabla {index} extraída. Dimensiones: {df.shape}")
        return df
    except Exception as e:
        raise ValueError(f"Error procesando tabla {index}: {str(e)}")

def clean_dataframe(df: pd.DataFrame, data_type: str = 'player') -> pd.DataFrame:
    """Limpia y normaliza un DataFrame según el tipo de datos"""
    # Primero eliminamos filas totalmente vacías
    df = df.dropna(how='all')
    
    if data_type == 'player':
        # Eliminar filas duplicadas manteniendo la primera aparición
        df = df.drop_duplicates(subset=['Player', 'Squad'], keep='first')
        
        # Limpieza de columnas específicas
        if 'Nation' in df.columns:
            df['Nation'] = df['Nation'].str.extract(r'([A-Z]{3})')
        if 'Pos' in df.columns:
            df['Pos'] = df['Pos'].str[:2].str.upper()
        if 'Comp' in df.columns:
            # Extraer solo el nombre de la liga (segunda parte)
            df['Comp'] = df['Comp'].str.extract(r'(?:^[a-z]{2}\s)?(.+)$')
            # Mapear nombres inconsistentes
            liga_mapping = {
                'Premier League': 'Premier League',
                'La Liga': 'La Liga',
                'Serie A': 'Serie A',
                'Ligue 1': 'Ligue 1',
                'Bundesliga': 'Bundesliga'
            }
            df['Comp'] = df['Comp'].replace(liga_mapping)
            
    elif data_type == 'team':
        if 'Country' in df.columns:
            # Extraer solo el código de país (parte en mayúsculas)
            df['Country'] = df['Country'].str.extract(r'([A-Z]{2,3})$')
        
        # Eliminar filas de encabezados si existen
        df = df[~df.iloc[:, 0].str.contains('Rk|Squad', na=False)]
    
    # Convertir columnas numéricas
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='ignore')
            except AttributeError:
                pass
    
    return df.dropna(how='all')

def get_player_stats(index: int = 0) -> pd.DataFrame:
    """Obtiene estadísticas de jugadores limpios"""
    url = 'https://fbref.com/es/comps/Big5/stats/jugadores/Estadisticas-de-Las-5-grandes-ligas-europeas'
    df = get_specific_table(url, index=index, header_row=1)
    
    # Limpieza inicial
    df = clean_dataframe(df, 'player')
    
    # Mapeo de columnas mejorado
    column_mapping = {
        'Player': 'Jugador',
        'Squad': 'Equipo',
        'Pos': 'Posicion',
        'Nation': 'Pais',
        'Comp': 'Liga',
        'Age': 'Edad',
        'MP': 'Partidos',
        'Gls': 'Goles',
        'Ast': 'Asistencias',
        'xG': 'xG',
        'xAG': 'xA'
    }
    
    # Aplicar mapeo y seleccionar columnas
    df = df.rename(columns=column_mapping)
    keep_cols = [v for v in column_mapping.values() if v in df.columns]
    df = df[keep_cols]
    
    # Limpieza final
    df = df.dropna(subset=['Jugador', 'Equipo'])
    df = df[~df.duplicated(subset=['Jugador', 'Equipo'])]
    
    return df.reset_index(drop=True)

def get_player_stats(index: int = 0) -> pd.DataFrame:
    """Obtiene estadísticas de jugadores limpios
    
    Args:
        index: Índice de la tabla a scrapear (0 para estadísticas estándar)
        
    Returns:
        DataFrame con datos de jugadores listos para usar
    """
    url = 'https://fbref.com/es/comps/Big5/stats/jugadores/Estadisticas-de-Las-5-grandes-ligas-europeas'
    try:
        df = get_specific_table(url, index=index, header_row=1)
        
        # Mapeo completo de columnas
        column_mapping = {
            'Rk': 'Rank',
            'Player': 'Jugador',
            'Nation': 'País',
            'Pos': 'Posc',
            'Squad': 'Equipo',
            'Comp': 'Liga',
            'Age': 'Edad',
            'Born': 'Nacimiento',
            'MP': 'Partidos',
            'Starts': 'Titulares',
            'Min': 'Minutos',
            '90s': 'Minutos_90s',
            'Gls': 'Goles',
            'Ast': 'Asistencias',
            'G+A': 'Goles_Asistencias',
            'G-PK': 'Goles_sin_penalti',
            'PK': 'Penaltis_convertidos',
            'PKatt': 'Penaltis_intentados',
            'CrdY': 'Tarjetas_Amarillas',
            'CrdR': 'Tarjetas_Rojas',
            'xG': 'xG',
            'npxG': 'npxG',
            'xAG': 'xA',
            'npxG+xAG': 'npxG_xA',
            'PrgC': 'Progresion_Regates',
            'PrgP': 'Progresion_Pases',
            'PrgR': 'Progresion_Recepciones',
            # Columnas por 90 minutos
            'Gls.1': 'Goles_90',
            'Ast.1': 'Asistencias_90',
            'G+A.1': 'Goles_Asistencias_90',
            'G-PK.1': 'Goles_sin_penalti_90',
            'G+A-PK': 'Goles_Asistencias_sin_pen_90',
            'xG.1': 'xG_90',
            'xAG.1': 'xA_90',
            'xG+xAG': 'xG_xA_90',
            'npxG.1': 'npxG_90',
            'npxG+xAG.1': 'npxG_xA_90',
            'Matches': 'Enlace_Partidos'
        }
        
        # Renombrar columnas
        df = df.rename(columns=column_mapping)
        
        # Limpieza específica para jugadores
        if 'Posc' in df.columns:
            df['Posc'] = df['Posc'].str[:2].str.upper()
            
        if 'País' in df.columns:
            df['País'] = df['País'].str.extract(r'([A-Z]{2,3})')[0]
            
        # Convertir columnas numéricas
        numeric_cols = ['Edad', 'Partidos', 'Minutos', 'Goles', 'Asistencias', 'xG', 'xA']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        return df.dropna(subset=['Jugador', 'Equipo'], how='all')
        
    except Exception as e:
        logger.error(f"Error al obtener stats de jugadores: {str(e)}")
        raise FBrefError(f"No se pudieron obtener datos de jugadores: {str(e)}")

def get_team_stats(index: int = 0) -> pd.DataFrame:
    """Obtiene estadísticas de equipos limpias"""
    url = 'https://fbref.com/es/comps/Big5/Estadisticas-de-Las-5-grandes-ligas-europeas'
    try:
        # Usar header=None y luego limpiar manualmente
        df = get_specific_table(url, index=index, header_row=None)
        
        # Si la primera fila parece ser de encabezado, usarla como tal
        if df.iloc[0].str.contains('Rk|Squad|Escudo|Club').any():
            df.columns = df.iloc[0]
            df = df[1:]
        
        # Eliminar filas totalmente vacías
        df = df.dropna(how='all')
        
        # Mapeo de columnas mejorado
        column_mapping = {
            'Rk': 'Posicion',
            'Squad': 'Equipo',
            'Country': 'Pais',
            'Comp': 'Liga',
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
        }
        
        # Renombrar solo las columnas que existen
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Limpieza específica
        if 'Equipo' in df.columns:
            df['Equipo'] = df['Equipo'].str.replace(r'^\d+\s', '', regex=True)
            df['Equipo'] = df['Equipo'].str.strip()
            
        if 'Pais' in df.columns:
            df['Pais'] = df['Pais'].str.extract(r'([A-Z]{2,3})')
        
        # Convertir columnas numéricas
        numeric_cols = ['Partidos', 'Goles_Favor', 'Goles_Contra', 'Puntos', 'xG', 'xGA']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
        
        return df.dropna(subset=['Equipo']).reset_index(drop=True)
        
    except Exception as e:
        logger.error(f"Error al obtener stats de equipos: {str(e)}")
        raise FBrefError(f"No se pudieron obtener datos de equipos: {str(e)}")

def print_table_summaries(url: str) -> None:
    """Muestra resumen de las tablas disponibles para debugging
    
    Args:
        url: URL a analizar
    """
    tables = get_tables_from_fbref(url)
    
    if not tables:
        print("⚠️ No se encontraron tablas")
        return
    
    print(f"\n🔍 {len(tables)} tablas encontradas en {url}")
    
    for i, table in enumerate(tables):
        try:
            df = pd.read_html(str(table), header=1)[0]
            print(f"\n📊 Tabla {i} ({df.shape[0]} filas × {df.shape[1]} columnas)")
            print("Columnas:", df.columns[:5].tolist() + ["..."])
        except Exception as e:
            print(f"⚠️ Error en tabla {i}: {str(e)}")