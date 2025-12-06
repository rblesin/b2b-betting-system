import pandas as pd
from config import *

class EnhancedB2BAnalyzer:
    """Multi-tier analyzer with relative form analysis"""
    
    def __init__(self, games_df):
        self.games_df = games_df.copy()
        self.team_records = {}
        self.team_streaks = {}
    
    def classify_tier(self, rested_form, b2b_form, is_home):
        """
        Classify game into tier based on absolute and relative form
        
        Tier S: Rested team has 4-5 wins in L5 AND 2+ win advantage
        Tier A: Rested team has 4-5 wins in L5 AND 1+ win advantage
        Tier B: Form advantage ≥2 (any form level)
        """
        rested_wins = rested_form['wins']
        b2b_wins = b2b_form['wins']
        
        # Calculate form advantage
        form_advantage = rested_wins - b2b_wins
        
        # Tier S: 4-5 wins AND 2+ advantage
        if rested_wins >= GOOD_FORM_WINS and rested_wins <= 5:
            if form_advantage >= 2:
                return 'S'
        
        # Tier A: 4-5 wins AND 1+ advantage
        if rested_wins >= GOOD_FORM_WINS and rested_wins <= 5:
            if form_advantage >= 1:
                return 'A'
        
        # Tier B: 2+ advantage (any form)
        if form_advantage >= 2:
            return 'B'
        
        return None
    
    def calculate_team_records(self):
        records = {}
        for team in set(self.games_df['home'].unique()) | set(self.games_df['away'].unique()):
            home_games = self.games_df[self.games_df['home'] == team]
            away_games = self.games_df[self.games_df['away'] == team]
            home_wins = home_games['home_win'].sum()
            away_wins = (~away_games['home_win']).sum()
            total_games = len(home_games) + len(away_games)
            total_wins = home_wins + away_wins
            win_pct = (total_wins / total_games * 100) if total_games > 0 else 0
            records[team] = {'games': total_games, 'wins': total_wins, 'win_pct': win_pct}
        self.team_records = records
        return records
    
    def calculate_team_streaks(self, last_n_games=RECENT_FORM_GAMES):
        streaks = {}
        sorted_games = self.games_df.sort_values('date')
        
        for team in set(sorted_games['home'].unique()) | set(sorted_games['away'].unique()):
            team_games = []
            for _, game in sorted_games.iterrows():
                if game['home'] == team:
                    team_games.append({'won': game['home_win']})
                elif game['away'] == team:
                    team_games.append({'won': not game['home_win']})
            
            if len(team_games) == 0:
                streaks[team] = {'last_5_wins': 0, 'last_5': '0-0', 'current_streak': 0, 'streak_type': 'none'}
                continue
            
            recent = team_games[-last_n_games:]
            wins = sum(1 for g in recent if g['won'])
            
            current_streak = 0
            if len(team_games) > 0:
                last_result = team_games[-1]['won']
                for game in reversed(team_games):
                    if game['won'] == last_result:
                        current_streak += 1
                    else:
                        break
                streak_type = 'W' if last_result else 'L'
            else:
                streak_type = 'none'
            
            streaks[team] = {
                'last_5_wins': wins,
                'last_5': f"{wins}-{len(recent)-wins}",
                'current_streak': current_streak,
                'streak_type': streak_type
            }
        
        self.team_streaks = streaks
        return streaks
    
    def should_bet(self, game, team_stats, standings):
        if not self.team_records:
            self.calculate_team_records()
        if not self.team_streaks:
            self.calculate_team_streaks()
        
        home = game['home']
        away = game['away']
        home_b2b = game.get('home_b2b', False)
        away_b2b = game.get('away_b2b', False)
        
        # Determine rest advantage
        if not home_b2b and away_b2b:
            rested = home
            b2b = away
            is_home = True
            scenario = "Rested home vs B2B away"
        elif home_b2b and not away_b2b:
            rested = away
            b2b = home
            is_home = False
            scenario = "Rested away vs B2B home"
        else:
            return self._skip("No rest advantage")
        
        # Get current form for BOTH teams
        rested_streak = self.team_streaks.get(rested, {})
        b2b_streak = self.team_streaks.get(b2b, {})
        
        rested_form = {
            'wins': rested_streak.get('last_5_wins', 0),
            'streak': rested_streak.get('current_streak', 0),
            'streak_type': rested_streak.get('streak_type', 'none')
        }
        
        b2b_form = {
            'wins': b2b_streak.get('last_5_wins', 0),
            'streak': b2b_streak.get('current_streak', 0),
            'streak_type': b2b_streak.get('streak_type', 'none')
        }
        
        # Classify into tier using RELATIVE form
        tier = self.classify_tier(rested_form, b2b_form, is_home)
        
        if not tier:
            reason = (f"{rested} doesn't qualify (L5: {rested_streak.get('last_5', '?')}) "
                     f"vs {b2b} (L5: {b2b_streak.get('last_5', '?')})")
            return self._skip(reason)
        
        tier_info = TIERS[tier]
        
        # Build recommendation
        rank = standings.get(rested, {}).get('rank', '?')
        form_advantage = rested_form['wins'] - b2b_form['wins']
        
        factors = {
            'sport': 'NHL',
            'tier': f"TIER {tier}: {tier_info['name']}",
            'scenario': scenario,
            'rested_team': f"#{rank} {rested}: {rested_streak.get('last_5', '?')} ({rested_form['wins']} wins)",
            'b2b_team': f"{b2b}: {b2b_streak.get('last_5', '?')} ({b2b_form['wins']} wins)",
            'form_advantage': f"+{form_advantage} win advantage",
            'criteria': tier_info['nhl_criteria']
        }
        
        return {
            'should_bet': True,
            'sport': 'NHL',
            'pick': rested,
            'confidence': tier_info['name'],
            'tier': tier,
            'tier_name': tier_info['name'],
            'edge': 0,
            'reason': f"{tier_info['nhl_criteria']} (Form advantage: +{form_advantage})",
            'form_advantage': form_advantage,
            'rested_wins': rested_form['wins'],
            'b2b_wins': b2b_form['wins'],
            'analysis': {
                'factors': factors,
                'red_flags': [],
                'green_flags': [f"Form advantage: +{form_advantage}", tier_info['nhl_criteria']]
            }
        }
    
    def _skip(self, reason):
        return {
            'should_bet': False,
            'sport': 'NHL',
            'pick': None,
            'confidence': 'SKIP',
            'tier': None,
            'edge': 0,
            'reason': reason,
            'analysis': {'factors': {}, 'red_flags': [reason], 'green_flags': []}
        }
