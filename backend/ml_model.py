import pandas as pd
import cloudscraper
import re
from bs4 import BeautifulSoup, Comment
from functools import lru_cache

@lru_cache(maxsize=32)
def get_tables_from_fbref(url):
    """Obtiene tablas de FBref con cache para mejor rendimiento"""
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment_soup = BeautifulSoup(comment, 'html.parser')
            tables.extend(comment_soup.find_all('table'))
            
        return tables
    except Exception as e:
        raise ConnectionError(f"Error al acceder a {url}: {str(e)}")

def get_specific_table(url, index=0, header_row=1):
    """Extrae una tabla específica de FBref"""
    tables = get_tables_from_fbref(url)
    
    if not tables:
        raise ValueError("No se pudieron obtener tablas de la página")
    
    if index >= len(tables):
        index = 0  # Usar primera tabla si el índice es inválido
    
    try:
        return pd.read_html(str(tables[index]), header=header_row)[0]
    except Exception as e:
        raise ValueError(f"Error al procesar tabla: {str(e)}")

def clean_player_data(df):
    """Limpieza básica de datos"""
    if df.empty:
        return df
        
    # Eliminar filas totalmente vacías y duplicados de columnas
    df = df.dropna(how='all')
    df = df.loc[:, ~df.columns.duplicated()]
    
    # Eliminar filas que no son jugadores (encabezados)
    if 'Player' in df.columns:
        df = df[~df['Player'].str.contains('Player|Rk', na=True)]
    
    return df

def clean_player_ml(df):
    """Limpieza avanzada para análisis ML"""
    if df.empty:
        return df
    
    # Mantener solo las dos primeras letras de la posición
    if 'Pos' in df.columns:
        df['Pos'] = df['Pos'].str[:2].str.upper()
    
    # Filtrar por edad (16-22 años)
    if 'Age' in df.columns:
        df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
        df = df[(df['Age'] >= 16) & (df['Age'] <= 22)].dropna(subset=['Age'])
    
    if 'Nation' in df.columns:
            df['Nation'] = df['Nation'].str.extract(r'([A-Z]{2,3})')[0]

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
            
    # Convertir columnas numéricas clave
    numeric_cols = ['MP', 'Min', 'Gls', 'Ast', 'xG', 'xAG', 'npxG']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df.reset_index(drop=True)

def get_player_ml(index=0):
    """Función principal para obtener datos limpios"""
    url = 'https://fbref.com/es/comps/Big5/stats/jugadores/Estadisticas-de-Las-5-grandes-ligas-europeas'
    df = get_specific_table(url, index=index, header_row=1)
    return clean_player_ml(clean_player_data(df))