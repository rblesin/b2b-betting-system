import pandas as pd
import numpy as np
from itertools import product

class HistoricalAnalyzer:
    """Analyze and optimize B2B betting strategy across multiple seasons"""
    
    def __init__(self, b2b_games_csv, completed_games_csv):
        """Load historical data"""
        self.b2b_df = pd.read_csv(b2b_games_csv)
        self.b2b_df['date'] = pd.to_datetime(self.b2b_df['date']).dt.date
        
        self.completed_df = pd.read_csv(completed_games_csv)
        self.completed_df['date'] = pd.to_datetime(self.completed_df['date']).dt.date
        
        print(f"Loaded {len(self.b2b_df)} B2B games and {len(self.completed_df)} total games")
        print(f"Seasons: {sorted(self.b2b_df['season'].unique())}")
    
    def calculate_team_form(self, team, game_date, season_df, last_n=5):
        """Calculate team's form (wins in last N games) before a specific date"""
        # Get all games for this team before game_date
        team_games = season_df[
            ((season_df['home'] == team) | (season_df['away'] == team)) &
            (season_df['date'] < game_date)
        ].sort_values('date')
        
        if len(team_games) == 0:
            return 0
        
        # Get last N games
        recent = team_games.tail(last_n)
        
        # Count wins
        wins = 0
        for _, game in recent.iterrows():
            if game['home'] == team and game['home_win']:
                wins += 1
            elif game['away'] == team and not game['home_win']:
                wins += 1
        
        return wins
    
    def classify_game(self, game, season_df, tier_criteria):
        """
        Classify a B2B game based on tier criteria
        
        tier_criteria: dict with keys:
            - min_rested_wins: minimum wins for rested team (for S/A)
            - min_form_adv_s: minimum form advantage for Tier S
            - min_form_adv_a: minimum form advantage for Tier A
            - min_form_adv_b: minimum form advantage for Tier B (can be any form)
        """
        # Determine who has rest advantage
        if game['rest_advantage'] == 'home':
            rested = game['home']
            b2b = game['away']
            result = game['home_win']
        elif game['rest_advantage'] == 'away':
            rested = game['away']
            b2b = game['home']
            result = not game['home_win']
        else:
            return None, None  # No clear advantage
        
        # Calculate form for both teams
        rested_wins = self.calculate_team_form(rested, game['date'], season_df)
        b2b_wins = self.calculate_team_form(b2b, game['date'], season_df)
        form_advantage = rested_wins - b2b_wins
        
        # Classify into tier
        if rested_wins >= tier_criteria['min_rested_wins']:
            if form_advantage >= tier_criteria['min_form_adv_s']:
                return 'S', result
            elif form_advantage >= tier_criteria['min_form_adv_a']:
                return 'A', result
        
        # Tier B: any form level with sufficient advantage
        if form_advantage >= tier_criteria['min_form_adv_b']:
            return 'B', result
        
        return None, None
    
    def backtest_criteria(self, tier_criteria, verbose=False):
        """Test tier criteria across all seasons"""
        results_by_season = {}
        tier_results = {'S': [], 'A': [], 'B': []}
        
        for season in sorted(self.b2b_df['season'].unique()):
            season_b2b = self.b2b_df[self.b2b_df['season'] == season]
            season_all = self.completed_df[self.completed_df['season'] == season]
            
            season_tiers = {'S': [], 'A': [], 'B': []}
            
            for _, game in season_b2b.iterrows():
                tier, result = self.classify_game(game, season_all, tier_criteria)
                
                if tier and result is not None:
                    season_tiers[tier].append(result)
                    tier_results[tier].append(result)
            
            # Calculate season stats
            season_stats = {}
            for tier in ['S', 'A', 'B']:
                if len(season_tiers[tier]) > 0:
                    wins = sum(season_tiers[tier])
                    total = len(season_tiers[tier])
                    wr = wins / total * 100
                    season_stats[tier] = {'wins': wins, 'total': total, 'wr': wr}
                else:
                    season_stats[tier] = {'wins': 0, 'total': 0, 'wr': 0}
            
            results_by_season[season] = season_stats
        
        # Calculate overall stats
        overall_stats = {}
        for tier in ['S', 'A', 'B']:
            if len(tier_results[tier]) > 0:
                wins = sum(tier_results[tier])
                total = len(tier_results[tier])
                wr = wins / total * 100
                # Standard error for binomial
                std_err = np.sqrt((wr/100 * (1-wr/100)) / total) * 100
                overall_stats[tier] = {
                    'wins': wins,
                    'total': total,
                    'wr': wr,
                    'std_err': std_err
                }
            else:
                overall_stats[tier] = {'wins': 0, 'total': 0, 'wr': 0, 'std_err': 0}
        
        if verbose:
            print(f"\nCriteria: {tier_criteria}")
            for tier in ['S', 'A', 'B']:
                stats = overall_stats[tier]
                print(f"Tier {tier}: {stats['wins']}-{stats['total']-stats['wins']} ({stats['wr']:.1f}% ± {stats['std_err']:.1f}%)")
        
        return overall_stats, results_by_season
    
    def optimize_criteria(self, target_min_games=150):
        """
        Find optimal tier criteria by testing various combinations
        
        Goal: Maximize win rate while maintaining reasonable sample size
        """
        print("\n" + "="*60)
        print("OPTIMIZING TIER CRITERIA")
        print("="*60)
        
        best_configs = []
        
        # Test ranges
        min_rested_wins_range = [3, 4]  # 3-4 or 4-5 wins
        form_adv_s_range = [2, 3]  # S tier form advantage
        form_adv_a_range = [1, 2]  # A tier form advantage
        form_adv_b_range = [2, 3]  # B tier form advantage
        
        configs_tested = 0
        
        for min_rw, fa_s, fa_a, fa_b in product(
            min_rested_wins_range,
            form_adv_s_range,
            form_adv_a_range,
            form_adv_b_range
        ):
            # Skip invalid combinations
            if fa_a >= fa_s:  # A should be less strict than S
                continue
            if fa_b > fa_s:  # B advantage shouldn't exceed S
                continue
            
            criteria = {
                'min_rested_wins': min_rw,
                'min_form_adv_s': fa_s,
                'min_form_adv_a': fa_a,
                'min_form_adv_b': fa_b
            }
            
            overall, by_season = self.backtest_criteria(criteria)
            
            # Check if tiers meet minimum game threshold
            total_games = sum(t['total'] for t in overall.values())
            
            if total_games >= target_min_games:
                avg_wr = np.mean([t['wr'] for t in overall.values() if t['total'] > 0])
                
                best_configs.append({
                    'criteria': criteria,
                    'overall': overall,
                    'by_season': by_season,
                    'total_games': total_games,
                    'avg_wr': avg_wr
                })
            
            configs_tested += 1
        
        # Sort by average win rate
        best_configs.sort(key=lambda x: x['avg_wr'], reverse=True)
        
        print(f"\nTested {configs_tested} configurations")
        print(f"Found {len(best_configs)} valid configurations (>={target_min_games} games)")
        print("\n" + "="*60)
        print("TOP 5 CONFIGURATIONS:")
        print("="*60)
        
        for i, config in enumerate(best_configs[:5], 1):
            print(f"\n#{i} - Avg WR: {config['avg_wr']:.1f}%")
            print(f"Criteria: {config['criteria']}")
            for tier in ['S', 'A', 'B']:
                stats = config['overall'][tier]
                if stats['total'] > 0:
                    print(f"  Tier {tier}: {stats['wins']}-{stats['total']-stats['wins']} ({stats['wr']:.1f}%, n={stats['total']})")
        
        return best_configs
    
    def analyze_by_season(self, tier_criteria):
        """Detailed season-by-season analysis"""
        overall, by_season = self.backtest_criteria(tier_criteria, verbose=True)
        
        print("\n" + "="*60)
        print("SEASON-BY-SEASON BREAKDOWN")
        print("="*60)
        
        season_df_list = []
        
        for season in sorted(by_season.keys()):
            stats = by_season[season]
            print(f"\n{season}:")
            
            tier_s = stats['S']
            tier_a = stats['A']
            tier_b = stats['B']
            
            total = tier_s['total'] + tier_a['total'] + tier_b['total']
            wins = tier_s['wins'] + tier_a['wins'] + tier_b['wins']
            
            if total > 0:
                wr = wins / total * 100
                print(f"  Overall: {wins}-{total-wins} ({wr:.1f}%, n={total})")
                print(f"  Tier S: {tier_s['wins']}-{tier_s['total']-tier_s['wins']} ({tier_s['wr']:.1f}%, n={tier_s['total']})")
                print(f"  Tier A: {tier_a['wins']}-{tier_a['total']-tier_a['wins']} ({tier_a['wr']:.1f}%, n={tier_a['total']})")
                print(f"  Tier B: {tier_b['wins']}-{tier_b['total']-tier_b['wins']} ({tier_b['wr']:.1f}%, n={tier_b['total']})")
                
                season_df_list.append({
                    'Season': season,
                    'S_WR': tier_s['wr'] if tier_s['total'] > 0 else None,
                    'S_Games': tier_s['total'],
                    'A_WR': tier_a['wr'] if tier_a['total'] > 0 else None,
                    'A_Games': tier_a['total'],
                    'B_WR': tier_b['wr'] if tier_b['total'] > 0 else None,
                    'B_Games': tier_b['total'],
                    'Total_WR': wr,
                    'Total_Games': total
                })
        
        return pd.DataFrame(season_df_list)

if __name__ == "__main__":
    # Load data
    analyzer = HistoricalAnalyzer(
        'nhl_b2b_games_2015_2025.csv',
        'nhl_completed_games_2015_2025.csv'
    )
    
    # Current criteria
    current_criteria = {
        'min_rested_wins': 4,
        'min_form_adv_s': 2,
        'min_form_adv_a': 1,
        'min_form_adv_b': 2
    }
    
    print("\n" + "="*60)
    print("CURRENT STRATEGY PERFORMANCE")
    print("="*60)
    season_df = analyzer.analyze_by_season(current_criteria)
    print("\n", season_df.to_string(index=False))
    
    # Optimize
    print("\n")
    best_configs = analyzer.optimize_criteria()
