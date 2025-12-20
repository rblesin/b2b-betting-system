import pandas as pd
from config import *

class EnhancedB2BAnalyzer:
    """
    Pro B2B analyzer with enhancements:
    - Goalie tracking (upgrades tiers)
    - Injury filtering (skips bad bets)
    - 2-tier system (67.9% WR base)
    """
    
    def __init__(self, games_df, scraper=None):
        self.games_df = games_df.copy()
        self.team_records = {}
        self.team_streaks = {}
        self.scraper = scraper
    
    def classify_tier(self, rested_form, b2b_form, is_home, enhancements=None):
        """
        TWO-TIER classification + PRO enhancements:
        
        Base Tiers:
        - Tier S: 4-5 wins + 3+ advantage → 68.2% WR
        - Tier A: 4-5 wins + 2+ advantage → 67.5% WR
        
        Enhancements:
        - B2B backup goalie: Upgrade A → S (+3% WR)
        - Rested 2+ injuries: SKIP
        - Rested backup goalie: Note but don't skip
        """
        rested_wins = rested_form['wins']
        b2b_wins = b2b_form['wins']
        form_advantage = rested_wins - b2b_wins
        
        # Must have 4-5 wins
        if rested_wins < GOOD_FORM_WINS or rested_wins > 5:
            return None, {'reason': 'Rested team needs 4-5 wins in L5'}
        
        # Base classification
        base_tier = None
        if form_advantage >= 3:
            base_tier = 'S'
        elif form_advantage >= 2:
            base_tier = 'A'
        
        if not base_tier:
            return None, {'reason': f'Form advantage (+{form_advantage}) too small'}
        
        # Track enhancements
        confidence_info = {
            'base_tier': base_tier,
            'final_tier': base_tier,
            'enhancements': []
        }
        
        if enhancements:
            # SKIP if rested team has major injuries
            if enhancements.get('rested_injuries', 0) >= 2:
                confidence_info['reason'] = 'Rested team has 2+ injuries - SKIP'
                return None, confidence_info
            
            # UPGRADE if B2B team using backup goalie
            if enhancements.get('b2b_backup_goalie'):
                confidence_info['enhancements'].append('🥅 B2B using backup goalie')
                if base_tier == 'A':
                    confidence_info['final_tier'] = 'S'
                    confidence_info['upgraded'] = True
                    confidence_info['enhancements'].append('⬆️ Upgraded A → S')
            
            # NOTE if rested using backup (don't skip, just note)
            if enhancements.get('rested_backup_goalie'):
                confidence_info['enhancements'].append('⚠️ Rested using backup goalie')
        
        return confidence_info['final_tier'], confidence_info
    
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
                streaks[team] = {'last_5_wins': 0, 'last_5': '0-0'}
                continue
            
            recent = team_games[-last_n_games:]
            wins = sum(1 for g in recent if g['won'])
            
            streaks[team] = {
                'last_5_wins': wins,
                'last_5': f"{wins}-{len(recent)-wins}"
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
        elif home_b2b and not away_b2b:
            rested = away
            b2b = home
            is_home = False
        else:
            return self._skip("No rest advantage")
        
        # Get form
        rested_streak = self.team_streaks.get(rested, {})
        b2b_streak = self.team_streaks.get(b2b, {})
        
        rested_form = {'wins': rested_streak.get('last_5_wins', 0)}
        b2b_form = {'wins': b2b_streak.get('last_5_wins', 0)}
        
        # Check enhancements (if scraper available)
        enhancements = {}
        if self.scraper:
            game_date = game.get('date')
            
            # Check goalies
            rested_goalie = self.scraper.check_goalie(rested, game_date)
            b2b_goalie = self.scraper.check_goalie(b2b, game_date)
            
            enhancements['rested_backup_goalie'] = (rested_goalie == 'backup')
            enhancements['b2b_backup_goalie'] = (b2b_goalie == 'backup')
            
            # Check injuries
            rested_inj = self.scraper.check_injuries(rested)
            enhancements['rested_injuries'] = rested_inj[1]
        
        # Classify
        tier, confidence_info = self.classify_tier(rested_form, b2b_form, is_home, enhancements)
        
        if not tier:
            reason = confidence_info.get('reason', 'Does not meet criteria')
            return self._skip(reason)
        
        tier_info = TIERS[tier]
        form_advantage = rested_form['wins'] - b2b_form['wins']
        
        return {
            'should_bet': True,
            'sport': 'NHL',
            'pick': rested,
            'tier': tier,
            'tier_name': tier_info['name'],
            'reason': tier_info['criteria'],
            'form_advantage': form_advantage,
            'rested_wins': rested_form['wins'],
            'b2b_wins': b2b_form['wins'],
            'enhancements': confidence_info.get('enhancements', []),
            'upgraded': confidence_info.get('upgraded', False),
            'analysis': {
                'factors': {
                    'rested_team': f"{rested}: {rested_streak.get('last_5', '?')}",
                    'b2b_team': f"{b2b}: {b2b_streak.get('last_5', '?')}",
                    'form_advantage': f"+{form_advantage}",
                    'tier': tier,
                    'criteria': tier_info['criteria'],
                    'enhancements': ', '.join(confidence_info.get('enhancements', [])) or 'None'
                }
            }
        }
    
    def _skip(self, reason):
        return {
            'should_bet': False,
            'sport': 'NHL',
            'pick': None,
            'tier': None,
            'reason': reason
        }
