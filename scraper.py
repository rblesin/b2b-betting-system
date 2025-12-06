import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

class HockeyReferenceScraper:
    """Scrape NHL schedule and results from Hockey-Reference.com"""
    
    BASE_URL = "https://www.hockey-reference.com"
    
    def __init__(self, season="2026"):
        self.season = season
        self.schedule_url = f"{self.BASE_URL}/leagues/NHL_{season}_games.html"
        self.standings_url = f"{self.BASE_URL}/leagues/NHL_{season}.html"
        
    def scrape_all_games(self):
        """Scrape both completed AND upcoming games"""
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
            if row.get('class') and 'thead' in row.get('class'):
                continue
            
            try:
                date_th = row.find('th', {'data-stat': 'date_game'})
                if not date_th:
                    continue
                
                date_link = date_th.find('a')
                if date_link:
                    date_str = date_link.text.strip()
                else:
                    date_str = date_th.text.strip()
                
                if not date_str:
                    continue
                    
                game_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                visitor_td = row.find('td', {'data-stat': 'visitor_team_name'})
                if not visitor_td:
                    continue
                visitor_link = visitor_td.find('a')
                visitor = visitor_link.text.strip() if visitor_link else visitor_td.text.strip()
                
                if not visitor:
                    continue
                
                home_td = row.find('td', {'data-stat': 'home_team_name'})
                if not home_td:
                    continue
                home_link = home_td.find('a')
                home = home_link.text.strip() if home_link else home_td.text.strip()
                
                if not home:
                    continue
                
                visitor_goals_td = row.find('td', {'data-stat': 'visitor_goals'})
                home_goals_td = row.find('td', {'data-stat': 'home_goals'})
                
                if (visitor_goals_td and home_goals_td and 
                    visitor_goals_td.text.strip() and home_goals_td.text.strip()):
                    
                    visitor_goals = int(visitor_goals_td.text.strip())
                    home_goals = int(home_goals_td.text.strip())
                    
                    # FIXED: Check for OT/SO in 'overtimes' column
                    overtimes_td = row.find('td', {'data-stat': 'overtimes'})
                    ot_so = overtimes_td.text.strip() if overtimes_td else ''
                    
                    completed_games.append({
                        'date': game_date,
                        'home': home,
                        'away': visitor,
                        'home_goals': home_goals,
                        'away_goals': visitor_goals,
                        'home_win': home_goals > visitor_goals,
                        'ot_so': ot_so
                    })
                else:
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
    
    def scrape_standings(self):
        """Scrape current NHL standings from both conferences"""
        print(f"Scraping standings from {self.standings_url}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(self.standings_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            standings = {}
            overall_rank = 1
            
            # Get both Eastern and Western conference tables
            for conf_table_id in ['standings_EAS', 'standings_WES']:
                table = soup.find('table', {'id': conf_table_id})
                if not table:
                    continue
                
                rows = table.find('tbody').find_all('tr')
                
                for row in rows:
                    if row.get('class') and 'thead' in row.get('class'):
                        continue
                    
                    # Get team name
                    team_cell = row.find('td', {'data-stat': 'team_name'})
                    if not team_cell:
                        team_cell = row.find('th', {'data-stat': 'team_name'})
                    
                    if team_cell:
                        team_link = team_cell.find('a')
                        if team_link:
                            team_name = team_link.text.strip()
                            
                            # Get points
                            pts_cell = row.find('td', {'data-stat': 'points'})
                            points = int(pts_cell.text.strip()) if pts_cell and pts_cell.text.strip() else 0
                            
                            standings[team_name] = {
                                'rank': overall_rank,
                                'points': points
                            }
                            overall_rank += 1
            
            # Sort by points to get true league-wide ranking
            sorted_standings = sorted(standings.items(), key=lambda x: x[1]['points'], reverse=True)
            
            # Reassign ranks based on points
            final_standings = {}
            for rank, (team, data) in enumerate(sorted_standings, 1):
                final_standings[team] = {
                    'rank': rank,
                    'points': data['points']
                }
            
            print(f"Scraped standings for {len(final_standings)} teams")
            return final_standings
            
        except Exception as e:
            print(f"⚠️  Could not scrape standings: {e}")
            return {}
