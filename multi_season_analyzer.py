"""
Multi-Season B2B Analyzer
Validates betting tiers across multiple seasons and identifies profitable strategies
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json


@dataclass
class TierPerformance:
    """Performance metrics for a betting tier"""
    name: str
    description: str
    games: int
    wins: int
    losses: int
    win_rate: float
    sample_games: List[Dict]
    
    def __repr__(self):
        return (f"{self.name}: {self.wins}-{self.losses} "
                f"({self.win_rate:.1%}) over {self.games} games")


class MultiSeasonAnalyzer:
    """Analyzes B2B betting strategies across multiple seasons"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize analyzer with game data
        
        Args:
            df: DataFrame from MultiSeasonScraper with all calculations
        """
        self.df = df
        self.tier_definitions = self._define_tiers()
    
    def _define_tiers(self) -> Dict:
        """
        Define betting tier criteria
        Can be expanded based on analysis results
        """
        return {
            'S_home': {
                'name': 'Tier S - Elite Home',
                'description': 'Home rested vs B2B opponent, good form (3-5 wins in L5)',
                'criteria': lambda row: (
                    row['home_b2b'] == False and
                    row['visitor_b2b'] == True and
                    pd.notna(row['home_form_wins']) and
                    row['home_form_wins'] >= 3 and
                    row['home_form_wins'] <= 5
                ),
                'pick': 'home'
            },
            'A_away': {
                'name': 'Tier A - Good Away',
                'description': 'Away rested vs B2B opponent, good form (3-5 wins in L5)',
                'criteria': lambda row: (
                    row['visitor_b2b'] == False and
                    row['home_b2b'] == True and
                    pd.notna(row['visitor_form_wins']) and
                    row['visitor_form_wins'] >= 3 and
                    row['visitor_form_wins'] <= 5
                ),
                'pick': 'visitor'
            },
            'B_home_medium': {
                'name': 'Tier B - Medium Home',
                'description': 'Home rested vs B2B opponent, medium form (2 wins in L5)',
                'criteria': lambda row: (
                    row['home_b2b'] == False and
                    row['visitor_b2b'] == True and
                    pd.notna(row['home_form_wins']) and
                    row['home_form_wins'] == 2
                ),
                'pick': 'home'
            },
            'C_away_medium': {
                'name': 'Tier C - Medium Away',
                'description': 'Away rested vs B2B opponent, medium form (2 wins in L5)',
                'criteria': lambda row: (
                    row['visitor_b2b'] == False and
                    row['home_b2b'] == True and
                    pd.notna(row['visitor_form_wins']) and
                    row['visitor_form_wins'] == 2
                ),
                'pick': 'visitor'
            },
            'D_home_hot': {
                'name': 'Tier D - Hot Streak Home',
                'description': 'Home rested vs B2B, on 3+ game win streak',
                'criteria': lambda row: (
                    row['home_b2b'] == False and
                    row['visitor_b2b'] == True and
                    pd.notna(row['home_form_wins']) and
                    row['home_form_wins'] == 5  # 5 wins in last 5 = hot streak
                ),
                'pick': 'home'
            },
            'E_away_hot': {
                'name': 'Tier E - Hot Streak Away',
                'description': 'Away rested vs B2B, on 3+ game win streak',
                'criteria': lambda row: (
                    row['visitor_b2b'] == False and
                    row['home_b2b'] == True and
                    pd.notna(row['visitor_form_wins']) and
                    row['visitor_form_wins'] == 5  # 5 wins in last 5 = hot streak
                ),
                'pick': 'visitor'
            },
            'F_relative_form': {
                'name': 'Tier F - Relative Form Advantage',
                'description': 'Rested team has 2+ more wins in L5 than B2B opponent',
                'criteria': lambda row: self._check_relative_form(row),
                'pick': 'dynamic'  # Depends on which team is rested
            }
        }
    
    def _check_relative_form(self, row) -> bool:
        """Check if rested team has significant form advantage"""
        # Home rested vs away B2B
        if (row['home_b2b'] == False and row['visitor_b2b'] == True and
            pd.notna(row['home_form_wins']) and pd.notna(row['visitor_form_wins'])):
            return (row['home_form_wins'] - row['visitor_form_wins']) >= 2
        
        # Away rested vs home B2B
        if (row['visitor_b2b'] == False and row['home_b2b'] == True and
            pd.notna(row['visitor_form_wins']) and pd.notna(row['home_form_wins'])):
            return (row['visitor_form_wins'] - row['home_form_wins']) >= 2
        
        return False
    
    def _get_pick_for_tier(self, row, tier_key: str) -> str:
        """Determine which team to pick for a given tier"""
        tier = self.tier_definitions[tier_key]
        
        if tier['pick'] == 'home':
            return 'home'
        elif tier['pick'] == 'visitor':
            return 'visitor'
        elif tier['pick'] == 'dynamic':
            # For relative form tier
            if row['home_b2b'] == False and row['visitor_b2b'] == True:
                return 'home'
            elif row['visitor_b2b'] == False and row['home_b2b'] == True:
                return 'visitor'
        
        return None
    
    def _check_win(self, row, pick: str) -> bool:
        """Check if the pick won the game"""
        if pick == 'home':
            return row['home_goals'] > row['visitor_goals']
        elif pick == 'visitor':
            return row['visitor_goals'] > row['home_goals']
        return False
    
    def analyze_tier(self, tier_key: str, return_games: bool = False) -> TierPerformance:
        """
        Analyze performance of a specific tier
        
        Args:
            tier_key: Key from tier_definitions
            return_games: Whether to return full game details
            
        Returns:
            TierPerformance object with results
        """
        tier = self.tier_definitions[tier_key]
        
        # Filter games matching tier criteria
        mask = self.df.apply(tier['criteria'], axis=1)
        tier_games = self.df[mask].copy()
        
        if len(tier_games) == 0:
            return TierPerformance(
                name=tier['name'],
                description=tier['description'],
                games=0,
                wins=0,
                losses=0,
                win_rate=0.0,
                sample_games=[]
            )
        
        # Determine picks and results
        tier_games['pick'] = tier_games.apply(
            lambda row: self._get_pick_for_tier(row, tier_key), axis=1
        )
        tier_games['won'] = tier_games.apply(
            lambda row: self._check_win(row, row['pick']), axis=1
        )
        
        wins = tier_games['won'].sum()
        losses = len(tier_games) - wins
        win_rate = wins / len(tier_games) if len(tier_games) > 0 else 0
        
        # Prepare sample games
        sample_games = []
        if return_games:
            for _, row in tier_games.iterrows():
                sample_games.append({
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'matchup': f"{row['visitor_team']} @ {row['home_team']}",
                    'pick': row['pick'],
                    'score': f"{row['visitor_goals']}-{row['home_goals']}",
                    'won': row['won'],
                    'season': row['season']
                })
        
        return TierPerformance(
            name=tier['name'],
            description=tier['description'],
            games=len(tier_games),
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            sample_games=sample_games
        )
    
    def analyze_all_tiers(self) -> Dict[str, TierPerformance]:
        """
        Analyze all defined tiers
        
        Returns:
            Dictionary mapping tier keys to performance metrics
        """
        results = {}
        
        print("\n" + "="*80)
        print("MULTI-SEASON TIER ANALYSIS")
        print("="*80)
        
        for tier_key in self.tier_definitions.keys():
            perf = self.analyze_tier(tier_key, return_games=False)
            results[tier_key] = perf
            
            # Print summary
            if perf.games > 0:
                print(f"\n{perf.name}")
                print(f"  {perf.description}")
                print(f"  Record: {perf.wins}-{perf.losses} ({perf.win_rate:.1%})")
                print(f"  Sample size: {perf.games} games")
                
                # Color code by profitability (assuming -110 odds)
                if perf.win_rate >= 0.525:  # Profitable at -110
                    print(f"  Status: ✓ PROFITABLE")
                elif perf.win_rate >= 0.51:
                    print(f"  Status: ≈ MARGINAL")
                else:
                    print(f"  Status: ✗ UNPROFITABLE")
            else:
                print(f"\n{perf.name}")
                print(f"  No games found matching criteria")
        
        return results
    
    def get_tier_recommendations(self, min_games: int = 30, min_winrate: float = 0.525) -> List[str]:
        """
        Get list of tiers that meet profitability criteria
        
        Args:
            min_games: Minimum sample size required
            min_winrate: Minimum win rate for profitability (default 52.5% for -110 odds)
            
        Returns:
            List of tier keys to bet on
        """
        results = self.analyze_all_tiers()
        
        recommended = []
        for tier_key, perf in results.items():
            if perf.games >= min_games and perf.win_rate >= min_winrate:
                recommended.append(tier_key)
        
        return recommended
    
    def generate_config_update(self, min_games: int = 30) -> Dict:
        """
        Generate updated config.py based on multi-season results
        
        Args:
            min_games: Minimum sample size for inclusion
            
        Returns:
            Dictionary with recommended config settings
        """
        results = self.analyze_all_tiers()
        
        config = {
            'tiers': {},
            'metadata': {
                'analyzed_seasons': self.df['season'].unique().tolist(),
                'total_games': len(self.df),
                'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d'),
                'min_sample_size': min_games
            }
        }
        
        for tier_key, perf in results.items():
            if perf.games >= min_games:
                config['tiers'][tier_key] = {
                    'name': perf.name,
                    'description': perf.description,
                    'historical_winrate': round(perf.win_rate, 4),
                    'sample_size': perf.games,
                    'record': f"{perf.wins}-{perf.losses}",
                    'recommended': perf.win_rate >= 0.525,
                    'confidence': self._calculate_confidence(perf)
                }
        
        return config
    
    def _calculate_confidence(self, perf: TierPerformance) -> str:
        """Calculate confidence level based on sample size and win rate"""
        if perf.games < 30:
            return "LOW"
        elif perf.games < 50:
            return "MEDIUM" if perf.win_rate >= 0.55 else "LOW"
        elif perf.games < 100:
            return "HIGH" if perf.win_rate >= 0.55 else "MEDIUM"
        else:
            if perf.win_rate >= 0.60:
                return "VERY HIGH"
            elif perf.win_rate >= 0.55:
                return "HIGH"
            else:
                return "MEDIUM"
    
    def export_tier_details(self, tier_key: str, output_file: str):
        """Export detailed game results for a specific tier"""
        perf = self.analyze_tier(tier_key, return_games=True)
        
        if perf.games == 0:
            print(f"No games found for {tier_key}")
            return
        
        # Save to JSON
        output = {
            'tier': perf.name,
            'description': perf.description,
            'summary': {
                'games': perf.games,
                'wins': perf.wins,
                'losses': perf.losses,
                'win_rate': perf.win_rate
            },
            'games': perf.sample_games
        }
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"✓ Exported {perf.games} games to {output_file}")
    
    def compare_home_vs_away(self) -> Dict:
        """Compare home rested vs away rested performance"""
        # All home rested vs B2B scenarios
        home_mask = (
            (self.df['home_b2b'] == False) &
            (self.df['visitor_b2b'] == True) &
            self.df['home_form_wins'].notna()
        )
        home_games = self.df[home_mask].copy()
        home_games['won'] = home_games['home_goals'] > home_games['visitor_goals']
        
        # All away rested vs B2B scenarios
        away_mask = (
            (self.df['visitor_b2b'] == False) &
            (self.df['home_b2b'] == True) &
            self.df['visitor_form_wins'].notna()
        )
        away_games = self.df[away_mask].copy()
        away_games['won'] = away_games['visitor_goals'] > away_games['home_goals']
        
        return {
            'home_rested': {
                'games': len(home_games),
                'wins': home_games['won'].sum(),
                'win_rate': home_games['won'].mean() if len(home_games) > 0 else 0
            },
            'away_rested': {
                'games': len(away_games),
                'wins': away_games['won'].sum(),
                'win_rate': away_games['won'].mean() if len(away_games) > 0 else 0
            }
        }


def main():
    """Example usage"""
    import pandas as pd
    
    # Load multi-season data (assumes you've run multi_season_scraper.py first)
    try:
        df = pd.read_csv('multi_season_games.csv', parse_dates=['date'])
    except FileNotFoundError:
        print("Error: Run multi_season_scraper.py first to generate data")
        return
    
    # Initialize analyzer
    analyzer = MultiSeasonAnalyzer(df)
    
    # Analyze all tiers
    results = analyzer.analyze_all_tiers()
    
    # Get recommendations
    print("\n" + "="*80)
    print("BETTING RECOMMENDATIONS")
    print("="*80)
    recommended = analyzer.get_tier_recommendations(min_games=30, min_winrate=0.525)
    
    if recommended:
        print(f"\nRecommended tiers to bet (>30 games, >52.5% win rate):")
        for tier_key in recommended:
            perf = results[tier_key]
            print(f"  • {perf.name}: {perf.win_rate:.1%} over {perf.games} games")
    else:
        print("\nNo tiers meet profitability criteria yet")
    
    # Compare home vs away
    print("\n" + "="*80)
    print("HOME VS AWAY COMPARISON")
    print("="*80)
    comparison = analyzer.compare_home_vs_away()
    print(f"\nHome rested vs B2B opponent:")
    print(f"  {comparison['home_rested']['wins']}-"
          f"{comparison['home_rested']['games'] - comparison['home_rested']['wins']} "
          f"({comparison['home_rested']['win_rate']:.1%}) "
          f"over {comparison['home_rested']['games']} games")
    
    print(f"\nAway rested vs B2B opponent:")
    print(f"  {comparison['away_rested']['wins']}-"
          f"{comparison['away_rested']['games'] - comparison['away_rested']['wins']} "
          f"({comparison['away_rested']['win_rate']:.1%}) "
          f"over {comparison['away_rested']['games']} games")
    
    # Generate config
    config = analyzer.generate_config_update(min_games=30)
    with open('recommended_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    print(f"\n✓ Saved recommended config to recommended_config.json")


if __name__ == "__main__":
    main()
