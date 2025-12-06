import pandas as pd
from datetime import timedelta

class B2BAnalyzer:
    """Analyze back-to-back game performance"""
    
    def __init__(self, games_df):
        self.games_df = games_df.copy()
        self.games_with_rest = None
        
    def calculate_rest_days(self):
        """Calculate rest days for each team in each game"""
        print("\nCalculating rest days for all games...")
        
        df = self.games_df.sort_values('date').reset_index(drop=True)
        
        # Track last game date for each team
        last_game = {}
        
        results = []
        
        for _, game in df.iterrows():
            game_date = game['date']
            home = game['home']
            away = game['away']
            
            # Calculate home rest
            if home in last_game:
                home_rest = (game_date - last_game[home]).days
            else:
                home_rest = 999  # First game of season
            
            # Calculate away rest
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
                'home_b2b': home_rest == 0,
                'away_b2b': away_rest == 0,
                'rest_advantage': 'home' if home_rest > away_rest else ('away' if away_rest > home_rest else 'equal')
            })
            
            # Update last game dates
            last_game[home] = game_date
            last_game[away] = game_date
        
        self.games_with_rest = pd.DataFrame(results)
        print(f"Processed {len(self.games_with_rest)} games with rest calculations")
        
        return self.games_with_rest
    
    def get_b2b_games(self):
        """Get only games where at least one team is on B2B"""
        if self.games_with_rest is None:
            self.calculate_rest_days()
        
        b2b_games = self.games_with_rest[
            (self.games_with_rest['home_b2b']) | 
            (self.games_with_rest['away_b2b'])
        ].copy()
        
        print(f"\nFound {len(b2b_games)} games with B2B situations")
        return b2b_games
    
    def analyze_win_rates(self):
        """Calculate win rates for different rest scenarios"""
        if self.games_with_rest is None:
            self.calculate_rest_days()
        
        b2b = self.get_b2b_games()
        
        print("\n" + "="*60)
        print("B2B BETTING ANALYSIS - WIN RATES")
        print("="*60)
        
        # Overall stats
        total_b2b_games = len(b2b)
        print(f"\nTotal games with B2B situation: {total_b2b_games}")
        
        # Scenario 1: Rested home vs B2B away
        rested_home_b2b_away = b2b[~b2b['home_b2b'] & b2b['away_b2b']]
        if len(rested_home_b2b_away) > 0:
            win_rate = rested_home_b2b_away['home_win'].mean() * 100
            print(f"\n1. RESTED HOME vs B2B AWAY")
            print(f"   Games: {len(rested_home_b2b_away)}")
            print(f"   Home team win rate: {win_rate:.1f}%")
        
        # Scenario 2: B2B home vs Rested away
        b2b_home_rested_away = b2b[b2b['home_b2b'] & ~b2b['away_b2b']]
        if len(b2b_home_rested_away) > 0:
            win_rate = b2b_home_rested_away['home_win'].mean() * 100
            print(f"\n2. B2B HOME vs RESTED AWAY")
            print(f"   Games: {len(b2b_home_rested_away)}")
            print(f"   Home team win rate: {win_rate:.1f}%")
            print(f"   Away team win rate: {100-win_rate:.1f}%")
        
        # Scenario 3: Both on B2B
        both_b2b = b2b[b2b['home_b2b'] & b2b['away_b2b']]
        if len(both_b2b) > 0:
            print(f"\n3. BOTH TEAMS ON B2B")
            print(f"   Games: {len(both_b2b)}")
            print(f"   (No rest advantage)")
        
        # Overall: Team with rest advantage
        rest_advantage_games = b2b[b2b['rest_advantage'] != 'equal']
        if len(rest_advantage_games) > 0:
            # Calculate win rate for team with rest advantage
            wins = 0
            for _, game in rest_advantage_games.iterrows():
                if game['rest_advantage'] == 'home' and game['home_win']:
                    wins += 1
                elif game['rest_advantage'] == 'away' and not game['home_win']:
                    wins += 1
            
            win_rate = (wins / len(rest_advantage_games)) * 100
            print(f"\n4. OVERALL: TEAM WITH REST ADVANTAGE")
            print(f"   Games: {len(rest_advantage_games)}")
            print(f"   Win rate: {win_rate:.1f}%")
        
        print("\n" + "="*60)
        
        return {
            'rested_home_b2b_away': rested_home_b2b_away,
            'b2b_home_rested_away': b2b_home_rested_away,
            'both_b2b': both_b2b
        }
    
    def get_upcoming_b2b_opportunities(self, days_ahead=7):
        """
        Identify upcoming B2B betting opportunities
        Note: This requires upcoming games data (not yet played)
        """
        # This would work with future games once we add that capability
        pass
