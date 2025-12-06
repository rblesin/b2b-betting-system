import pandas as pd

class B2BAnalyzer:
    """Analyze back-to-back game performance"""
    
    def __init__(self, games_df):
        self.games_df = games_df.copy()
        self.games_with_rest = None
        
    def calculate_rest_days(self):
        """Calculate rest days for each team in each game"""
        df = self.games_df.sort_values('date').reset_index(drop=True)
        
        last_game = {}
        results = []
        
        for _, game in df.iterrows():
            game_date = game['date']
            home = game['home']
            away = game['away']
            
            if home in last_game:
                home_rest = (game_date - last_game[home]).days
            else:
                home_rest = 999
            
            if away in last_game:
                away_rest = (game_date - last_game[away]).days
            else:
                away_rest = 999
            
            results.append({
                'date': game_date,
                'home': home,
                'away': away,
                'home_goals': game['home_goals'],
                'away_goals': game['away_goals'],
                'home_win': game['home_win'],
                'home_rest': home_rest,
                'away_rest': away_rest,
                'home_b2b': home_rest == 1,
                'away_b2b': away_rest == 1,
                'rest_advantage': 'home' if home_rest > away_rest else ('away' if away_rest > home_rest else 'equal')
            })
            
            last_game[home] = game_date
            last_game[away] = game_date
        
        self.games_with_rest = pd.DataFrame(results)
        return self.games_with_rest
    
    def get_b2b_games(self):
        """Get only games where at least one team is on B2B"""
        if self.games_with_rest is None:
            self.calculate_rest_days()
        
        b2b_games = self.games_with_rest[
            (self.games_with_rest['home_b2b']) | 
            (self.games_with_rest['away_b2b'])
        ].copy()
        
        return b2b_games
    
    def analyze_win_rates(self):
        """Calculate win rates for different rest scenarios"""
        if self.games_with_rest is None:
            self.calculate_rest_days()
        
        b2b = self.get_b2b_games()
        
        if len(b2b) == 0:
            return {
                'rested_home_b2b_away': pd.DataFrame(), 
                'b2b_home_rested_away': pd.DataFrame(), 
                'both_b2b': pd.DataFrame()
            }
        
        rested_home_b2b_away = b2b[~b2b['home_b2b'] & b2b['away_b2b']]
        b2b_home_rested_away = b2b[b2b['home_b2b'] & ~b2b['away_b2b']]
        both_b2b = b2b[b2b['home_b2b'] & b2b['away_b2b']]
        
        return {
            'rested_home_b2b_away': rested_home_b2b_away,
            'b2b_home_rested_away': b2b_home_rested_away,
            'both_b2b': both_b2b
        }

    def analyze_team_b2b_performance(self):
        """Analyze each team's performance in B2B situations"""
        if self.games_with_rest is None:
            self.calculate_rest_days()
        
        team_stats = {}
        
        all_teams = set(self.games_with_rest['home'].unique()) | set(self.games_with_rest['away'].unique())
        
        for team in sorted(all_teams):
            home_b2b_games = self.games_with_rest[
                (self.games_with_rest['home'] == team) & 
                (self.games_with_rest['home_b2b'] == True)
            ]
            
            away_b2b_games = self.games_with_rest[
                (self.games_with_rest['away'] == team) & 
                (self.games_with_rest['away_b2b'] == True)
            ]
            
            home_b2b_wins = home_b2b_games['home_win'].sum()
            away_b2b_wins = (~away_b2b_games['home_win']).sum()
            
            total_b2b_games = len(home_b2b_games) + len(away_b2b_games)
            total_b2b_wins = home_b2b_wins + away_b2b_wins
            
            if total_b2b_games > 0:
                team_stats[team] = {
                    'total_b2b': total_b2b_games,
                    'total_wins': total_b2b_wins,
                    'win_pct': (total_b2b_wins / total_b2b_games) * 100,
                    'home_b2b': len(home_b2b_games),
                    'home_b2b_wins': home_b2b_wins,
                    'home_b2b_pct': (home_b2b_wins / len(home_b2b_games) * 100) if len(home_b2b_games) > 0 else 0,
                    'away_b2b': len(away_b2b_games),
                    'away_b2b_wins': away_b2b_wins,
                    'away_b2b_pct': (away_b2b_wins / len(away_b2b_games) * 100) if len(away_b2b_games) > 0 else 0
                }
        
        return team_stats
