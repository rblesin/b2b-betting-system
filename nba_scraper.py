import requests
import pandas as pd
from datetime import datetime, timedelta

class NBAESPNScraper:
    def __init__(self, season="2025"):
        self.season = season
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
    
    def scrape_upcoming_games(self, days=30):
        """Scrape upcoming NBA games"""
        print(f"Scraping NBA upcoming games (next {days} days)...")
        
        all_games = []
        
        start_date = datetime.now()
        end_date = datetime.now() + timedelta(days=days)
        
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y%m%d')
            url = f"{self.base_url}/scoreboard?dates={date_str}"
            
            try:
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    events = data.get('events', [])
                    
                    for event in events:
                        competition = event['competitions'][0]
                        competitors = competition['competitors']
                        
                        home_team = next((c for c in competitors if c['homeAway'] == 'home'), None)
                        away_team = next((c for c in competitors if c['homeAway'] == 'away'), None)
                        
                        if not home_team or not away_team:
                            continue
                        
                        # Skip completed games
                        if competition['status']['type']['completed']:
                            continue
                        
                        game_date = datetime.strptime(event['date'], '%Y-%m-%dT%H:%M%SZ').date()
                        
                        game = {
                            'date': game_date,
                            'away': away_team['team']['displayName'],
                            'home': home_team['team']['displayName'],
                        }
                        
                        all_games.append(game)
            
            except Exception as e:
                pass
            
            current_date += timedelta(days=1)
        
        if len(all_games) == 0:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_games)
        
        # Calculate rest days using completed games
        try:
            completed_df = pd.read_csv('nba_completed_games_2025.csv')
            completed_df['date'] = pd.to_datetime(completed_df['date']).dt.date
            
            # Combine for rest calculation
            all_games_df = pd.concat([completed_df, df]).sort_values('date')
            
            last_game = {}
            
            for idx in all_games_df.index:
                home = all_games_df.at[idx, 'home']
                away = all_games_df.at[idx, 'away']
                game_date = all_games_df.at[idx, 'date']
                
                home_rest = (game_date - last_game[home]).days if home in last_game else 999
                away_rest = (game_date - last_game[away]).days if away in last_game else 999
                
                all_games_df.at[idx, 'home_rest'] = home_rest
                all_games_df.at[idx, 'away_rest'] = away_rest
                all_games_df.at[idx, 'home_b2b'] = home_rest == 1
                all_games_df.at[idx, 'away_b2b'] = away_rest == 1
                
                last_game[home] = game_date
                last_game[away] = game_date
            
            # Return only upcoming games
            df = all_games_df.loc[df.index]
        
        except Exception as e:
            print(f"Warning: Could not calculate rest days: {e}")
        
        print(f"✅ Found {len(df)} upcoming NBA games")
        
        return df
    
    def scrape_standings(self):
        """Scrape NBA standings from ESPN"""
        url = f"{self.base_url}/standings"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return {}
            
            data = response.json()
            standings = {}
            
            # ESPN returns standings by conference
            for group in data.get('children', []):
                conference = group.get('name', '')
                
                for standing in group.get('standings', {}).get('entries', []):
                    team = standing['team']['displayName']
                    rank = standing['stats'][8]['value']  # Conference rank
                    
                    standings[team] = {
                        'rank': int(rank),
                        'conference': conference
                    }
            
            return standings
            
        except Exception as e:
            return {}

if __name__ == "__main__":
    scraper = NBAESPNScraper()
    upcoming = scraper.scrape_upcoming_games(days=7)
    print(upcoming.head())
