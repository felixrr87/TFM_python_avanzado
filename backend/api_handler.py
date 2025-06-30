import requests
import pandas as pd
from typing import Dict, List, Optional
import logging
import streamlit as st

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FootballDataHandler:
    BASE_URL = "http://api.football-data.org/v4"
    
    def __init__(self, api_key: str):
        self.headers = {'X-Auth-Token': api_key}
    
    @st.cache_data(ttl=3600)  # Cache por 1 hora
    def _make_request(_self, endpoint: str) -> Optional[Dict]:
        try:
            response = requests.get(
                f"{_self.BASE_URL}/{endpoint}",
                headers=_self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API Error: {str(e)}")
            return None

    @st.cache_data(ttl=3600)
    def get_league_standings(_self, competition_code: str = "PL") -> pd.DataFrame:
        """Obtiene la tabla de posiciones de la Premier League"""
        data = _self._make_request(f"competitions/{competition_code}/standings")
        
        if not data or not data.get('standings'):
            return pd.DataFrame()
            
        standings = []
        for table in data['standings']:
            if table['type'] == 'TOTAL':
                for team in table['table']:
                    standings.append({
                        'position': team['position'],
                        'team': team['team']['name'],
                        'played': team['playedGames'],
                        'won': team['won'],
                        'draw': team['draw'],
                        'lost': team['lost'],
                        'goalsFor': team['goalsFor'],
                        'goalsAgainst': team['goalsAgainst'],
                        'goalDifference': team['goalDifference'],
                        'points': team['points'],
                        'form': team['form']
                    })
        return pd.DataFrame(standings)

    @st.cache_data(ttl=3600)
    def get_team_matches(_self, team_id: int) -> pd.DataFrame:
        """Obtiene los partidos de un equipo específico"""
        data = _self._make_request(f"teams/{team_id}/matches?status=FINISHED&limit=10")
        
        if not data or not data.get('matches'):
            return pd.DataFrame()
            
        matches = []
        for match in data['matches']:
            matches.append({
                'date': pd.to_datetime(match['utcDate']).strftime('%Y-%m-%d'),
                'competition': match['competition']['name'],
                'homeTeam': match['homeTeam']['name'],
                'awayTeam': match['awayTeam']['name'],
                'score': f"{match['score']['fullTime']['home']}-{match['score']['fullTime']['away']}",
                'status': match['status']
            })
        return pd.DataFrame(matches)

    @st.cache_data(ttl=3600)
    def get_competition_teams(_self, competition_code: str = "PL") -> pd.DataFrame:
        """Obtiene todos los equipos de una competición"""
        data = _self._make_request(f"competitions/{competition_code}/teams")
        
        if not data or not data.get('teams'):
            return pd.DataFrame()
            
        teams = []
        for team in data['teams']:
            teams.append({
                'id': team['id'],
                'name': team['name'],
                'shortName': team['shortName'],
                'tla': team['tla'],
                'crest': team['crest'],
                'venue': team['venue'],
                'coach': team['coach']['name'] if 'coach' in team and team['coach'] else 'Desconocido'
            })
        return pd.DataFrame(teams)