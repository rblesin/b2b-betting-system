import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

class FullScheduleScraper:
    """Scrape NHL schedule including both completed and upcoming games"""
    
    BASE_URL = "https://www.hockey-reference.com"
    
    def __init__(self, season="2026"):
        self.season = season
        self.schedule_url = f"{self.BASE_URL}/leagues/NHL_{season}_games.html"
        
    def scrape_all_games(self):
        """Scrape full season schedule with completed AND upcoming games"""
        print(f"Scraping full schedule from {self.schedule_url}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(self.schedule_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        table = soup.find('table', {'id': 'games'})
        if not table:
            raise ValueError("Could not find games table on page")
        
        completed_games = []
        upcoming_games = []
        rows = table.find('tbody').find_all('tr')
        
        for row in rows:
            # Skip header rows
            if row.get('class') and 'thead' in row.get('class'):
                continue
            
            try:
                # Get date from the th element
                date_th = row.find('th', {'data-stat': 'date_game'})
                if not date_th or not date_th.find('a'):
                    continue
                
                date_str = date_th.find('a').text.strip()
                game_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                # Get visitor team
                visitor_td = row.find('td', {'data-stat': 'visitor_team_name'})
                if not visitor_td or not visitor_td.find('a'):
                    continue
                visitor = visitor_td.find('a').text.strip()
                
                # Get home team
                home_td = row.find('td', {'data-stat': 'home_team_name'})
                if not home_td or not home_td.find('a'):
                    continue
                home = home_td.find('a').text.strip()
                
                # Try to get goals (if game is completed)
                visitor_goals_td = row.find('td', {'data-stat': 'visitor_goals'})
                home_goals_td = row.find('td', {'data-stat': 'home_goals'})
                
                if visitor_goals_td and home_goals_td and visitor_goals_td.text.strip() and home_goals_td.text.strip():
                    # Completed game
                    visitor_goals = int(visitor_goals_td.text.strip())
                    home_goals = int(home_goals_td.text.strip())
                    
                    completed_games.append({
                        'date': game_date,
                        'home': home,
                        'away': visitor,
                        'home_goals': home_goals,
                        'away_goals': visitor_goals,
                        'home_win': home_goals > visitor_goals
                    })
                else:
                    # Upcoming game
                    upcoming_games.append({
                        'date': game_date,
                        'home': home,
                        'away': visitor
                    })
                    
            except (ValueError, AttributeError) as e:
                continue
        
        completed_df = pd.DataFrame(completed_games).sort_values('date').reset_index(drop=True) if completed_games else pd.DataFrame()
        upcoming_df = pd.DataFrame(upcoming_games).sort_values('date').reset_index(drop=True) if upcoming_games else pd.DataFrame()
        
        print(f"Found {len(completed_df)} completed games and {len(upcoming_df)} upcoming games")
        
        return completed_df, upcoming_df
