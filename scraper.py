import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import json
import os

class HockeyReferenceScraper:
    def __init__(self, season="2026"):
        self.season = season
        self.base_url = "https://www.hockey-reference.com"
        self.cache_dir = "cache"
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def scrape_full_schedule(self):
        """Scrape complete season schedule"""
        url = f"{self.base_url}/leagues/NHL_{self.season}_games.html"
        
        print(f"Scraping full schedule from {url}...")
        
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        games_table = soup.find('table', {'id': 'games'})
        
        if not games_table:
            print("Could not find games table")
            return pd.DataFrame(), pd.DataFrame()
        
        completed_games = []
        upcoming_games = []
        
        rows = games_table.find('tbody').find_all('tr')
        
        for row in rows:
            if 'thead' in row.get('class', []):
                continue
            
            cells = row.find_all(['td', 'th'])
            
            if len(cells) < 4:
                continue
            
            date_cell = cells[0]
            visitor_cell = cells[2] if len(cells) > 2 else None
            home_cell = cells[4] if len(cells) > 4 else None
            
            if not visitor_cell or not home_cell:
                continue
            
            try:
                date_str = date_cell.get_text(strip=True)
                game_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                away_team = visitor_cell.get_text(strip=True)
                home_team = home_cell.get_text(strip=True)
                
                # Check if game is completed (has score)
                visitor_goals_cell = cells[3] if len(cells) > 3 else None
                
                if visitor_goals_cell and visitor_goals_cell.get_text(strip=True):
                    # Completed game
                    home_goals_cell = cells[5] if len(cells) > 5 else None
                    ot_cell = cells[6] if len(cells) > 6 else None
                    
                    visitor_goals = int(visitor_goals_cell.get_text(strip=True))
                    home_goals = int(home_goals_cell.get_text(strip=True))
                    ot_so = ot_cell.get_text(strip=True) if ot_cell else ''
                    
                    completed_games.append({
                        'date': game_date,
                        'home': home_team,
                        'away': away_team,
                        'home_goals': home_goals,
                        'away_goals': visitor_goals,
                        'home_win': home_goals > visitor_goals,
                        'ot_so': ot_so
                    })
                else:
                    # Upcoming game
                    upcoming_games.append({
                        'date': game_date,
                        'home': home_team,
                        'away': away_team
                    })
            
            except Exception as e:
                continue
        
        completed_df = pd.DataFrame(completed_games)
        upcoming_df = pd.DataFrame(upcoming_games)
        
        print(f"Found {len(completed_df)} completed games and {len(upcoming_df)} upcoming games")
        
        return completed_df, upcoming_df
    
    def calculate_rest_days(self, completed_df, upcoming_df):
        """Calculate rest days for both completed and upcoming games"""
        # Combine all games chronologically
        all_games = pd.concat([
            completed_df[['date', 'home', 'away']],
            upcoming_df[['date', 'home', 'away']]
        ]).sort_values('date').reset_index(drop=True)
        
        # Track last game date for each team
        last_game = {}
        
        # Calculate rest for all games
        for idx in all_games.index:
            home = all_games.at[idx, 'home']
            away = all_games.at[idx, 'away']
            game_date = all_games.at[idx, 'date']
            
            home_rest = (game_date - last_game[home]).days if home in last_game else 999
            away_rest = (game_date - last_game[away]).days if away in last_game else 999
            
            all_games.at[idx, 'home_rest'] = home_rest
            all_games.at[idx, 'away_rest'] = away_rest
            
            last_game[home] = game_date
            last_game[away] = game_date
        
        # Split back into completed and upcoming with rest data
        completed_with_rest = all_games[all_games['date'].isin(completed_df['date'])].copy()
        upcoming_with_rest = all_games[all_games['date'].isin(upcoming_df['date'])].copy()
        
        # Merge back with original data
        completed_final = completed_df.merge(
            completed_with_rest[['date', 'home', 'away', 'home_rest', 'away_rest']],
            on=['date', 'home', 'away'],
            how='left'
        )
        
        upcoming_final = upcoming_df.merge(
            upcoming_with_rest[['date', 'home', 'away', 'home_rest', 'away_rest']],
            on=['date', 'home', 'away'],
            how='left'
        )
        
        return completed_final, upcoming_final
    
    def scrape_all_games(self):
        """Scrape and return all games with rest calculations"""
        completed_df, upcoming_df = self.scrape_full_schedule()
        
        if len(completed_df) == 0:
            return pd.DataFrame(), pd.DataFrame()
        
        # Calculate rest days for both
        completed_final, upcoming_final = self.calculate_rest_days(completed_df, upcoming_df)
        
        return completed_final, upcoming_final
    
    def scrape_standings(self):
        """Scrape current standings"""
        url = f"{self.base_url}/leagues/NHL_{self.season}.html"
        
        print(f"Scraping standings from {url}...")
        
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            standings = {}
            
            for conference in ['Eastern', 'Western']:
                table_id = f"standings_{conference}"
                table = soup.find('table', {'id': table_id})
                
                if table:
                    rows = table.find('tbody').find_all('tr')
                    
                    for row in rows:
                        team_cell = row.find('th', {'data-stat': 'team_name'})
                        rank_cell = row.find('td', {'data-stat': 'rank'})
                        
                        if team_cell and rank_cell:
                            team_name = team_cell.get_text(strip=True)
                            rank = int(rank_cell.get_text(strip=True))
                            
                            standings[team_name] = {
                                'rank': rank,
                                'conference': conference
                            }
            
            print(f"Scraped standings for {len(standings)} teams")
            return standings
            
        except Exception as e:
            print(f"Error scraping standings: {e}")
            return {}

if __name__ == "__main__":
    scraper = HockeyReferenceScraper(season="2026")
    completed, upcoming = scraper.scrape_all_games()
    
    print("\nCompleted games:", len(completed))
    print(completed.head())
    
    print("\nUpcoming games:", len(upcoming))
    print(upcoming.head())
    
    print("\nUpcoming with B2B:")
    b2b_upcoming = upcoming[
        (upcoming['home_rest'] == 1) | (upcoming['away_rest'] == 1)
    ]
    print(f"Found {len(b2b_upcoming)} games with B2B situation")
