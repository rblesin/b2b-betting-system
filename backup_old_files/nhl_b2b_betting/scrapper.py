import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time

class HockeyReferenceScraper:
    """Scrape NHL schedule and results from Hockey-Reference.com"""
    
    BASE_URL = "https://www.hockey-reference.com"
    
    def __init__(self, season="2026"):
        """
        Args:
            season: End year of season (e.g., "2026" for 2025-26 season)
        """
        self.season = season
        self.schedule_url = f"{self.BASE_URL}/leagues/NHL_{season}_games.html"
        
    def scrape_schedule(self):
        """Scrape full season schedule with results"""
        print(f"Scraping schedule from {self.schedule_url}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(self.schedule_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Find the games table
        table = soup.find('table', {'id': 'games'})
        if not table:
            raise ValueError("Could not find games table on page")
        
        games = []
        rows = table.find('tbody').find_all('tr')
        
        for row in rows:
            # Skip header rows
            if row.get('class') and 'thead' in row.get('class'):
                continue
                
            cols = row.find_all(['td', 'th'])
            if len(cols) < 6:
                continue
            
            # Extract data
            date_str = cols[0].text.strip()
            visitor = cols[1].text.strip()
            visitor_goals = cols[2].text.strip()
            home = cols[3].text.strip()
            home_goals = cols[4].text.strip()
            
            # Skip games not yet played
            if not visitor_goals or not home_goals:
                continue
            
            try:
                game_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                games.append({
                    'date': game_date,
                    'home': home,
                    'away': visitor,
                    'home_goals': int(home_goals),
                    'away_goals': int(visitor_goals),
                    'home_win': int(home_goals) > int(visitor_goals)
                })
            except (ValueError, AttributeError) as e:
                print(f"Skipping row: {e}")
                continue
        
        df = pd.DataFrame(games)
        df = df.sort_values('date').reset_index(drop=True)
        
        print(f"Scraped {len(df)} completed games")
        return df