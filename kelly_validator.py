"""
Kelly Criterion Validator
Tests different fractional Kelly values and analyzes bankroll performance
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
from dataclasses import dataclass


@dataclass
class KellyResults:
    """Results from Kelly Criterion simulation"""
    fraction: float
    final_bankroll: float
    max_drawdown: float
    max_drawdown_pct: float
    roi: float
    sharpe_ratio: float
    total_bets: int
    
    def __repr__(self):
        return (f"Kelly {self.fraction:.0%}: "
                f"Final ${self.final_bankroll:,.2f} "
                f"(ROI: {self.roi:.1%}, "
                f"Max DD: {self.max_drawdown_pct:.1%})")


class KellyValidator:
    """Validates optimal Kelly Criterion fraction through backtesting"""
    
    def __init__(self, initial_bankroll: float = 1000.0):
        """
        Initialize validator
        
        Args:
            initial_bankroll: Starting bankroll amount
        """
        self.initial_bankroll = initial_bankroll
        self.odds = 1.0  # Even money (-110 pays ~0.91, but using 1.0 for simplicity)
    
    def calculate_kelly_fraction(self, win_rate: float, odds: float = 1.0) -> float:
        """
        Calculate optimal Kelly fraction
        
        Args:
            win_rate: Historical win rate (0-1)
            odds: Net odds received (1.0 = even money)
            
        Returns:
            Optimal fraction of bankroll to bet
        """
        if win_rate <= 0.5:
            return 0.0  # No edge
        
        b = odds
        p = win_rate
        q = 1 - p
        
        kelly = (b * p - q) / b
        return max(0, kelly)
    
    def simulate_betting(self, 
                        games: pd.DataFrame, 
                        win_rate: float,
                        kelly_fraction: float = 0.25,
                        max_bet_pct: float = 0.10) -> Tuple[pd.DataFrame, KellyResults]:
        """
        Simulate betting sequence with Kelly Criterion
        
        Args:
            games: DataFrame with 'won' column (boolean)
            win_rate: Historical win rate to calculate Kelly
            kelly_fraction: Fraction of full Kelly to use (0.25 = quarter Kelly)
            max_bet_pct: Maximum bet as fraction of bankroll
            
        Returns:
            (bet_history DataFrame, KellyResults summary)
        """
        # Calculate full Kelly, then apply fraction
        full_kelly = self.calculate_kelly_fraction(win_rate, self.odds)
        fractional_kelly = full_kelly * kelly_fraction
        
        bankroll = self.initial_bankroll
        max_bankroll = bankroll
        min_bankroll = bankroll
        
        bets = []
        
        for idx, row in games.iterrows():
            # Calculate bet size
            bet_pct = min(fractional_kelly, max_bet_pct)
            bet_size = bankroll * bet_pct
            
            # Skip if bet is too small
            if bet_size < 1.0:
                continue
            
            # Determine result
            if row['won']:
                profit = bet_size * self.odds
                bankroll += profit
            else:
                bankroll -= bet_size
            
            # Track min/max
            max_bankroll = max(max_bankroll, bankroll)
            min_bankroll = min(min_bankroll, bankroll)
            
            # Record bet
            bets.append({
                'bet_num': len(bets) + 1,
                'date': row.get('date', None),
                'bet_size': bet_size,
                'won': row['won'],
                'profit': profit if row['won'] else -bet_size,
                'bankroll': bankroll,
                'kelly_pct': bet_pct * 100
            })
            
            # Stop if bankrupt
            if bankroll <= 0:
                break
        
        # Create results DataFrame
        bet_df = pd.DataFrame(bets)
        
        # Calculate metrics
        final_bankroll = bankroll
        roi = (final_bankroll - self.initial_bankroll) / self.initial_bankroll
        max_drawdown = max_bankroll - min_bankroll
        max_drawdown_pct = max_drawdown / max_bankroll if max_bankroll > 0 else 0
        
        # Calculate Sharpe ratio (risk-adjusted return)
        if len(bet_df) > 1:
            returns = bet_df['profit'] / bet_df['bet_size']
            sharpe = returns.mean() / returns.std() if returns.std() > 0 else 0
        else:
            sharpe = 0
        
        results = KellyResults(
            fraction=kelly_fraction,
            final_bankroll=final_bankroll,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            roi=roi,
            sharpe_ratio=sharpe,
            total_bets=len(bet_df)
        )
        
        return bet_df, results
    
    def test_kelly_fractions(self, 
                            games: pd.DataFrame,
                            win_rate: float,
                            fractions: List[float] = None) -> Dict[float, KellyResults]:
        """
        Test multiple Kelly fractions to find optimal
        
        Args:
            games: DataFrame with 'won' column
            win_rate: Historical win rate
            fractions: List of fractions to test (default: [0.1, 0.25, 0.5, 0.75, 1.0])
            
        Returns:
            Dictionary mapping fraction to results
        """
        if fractions is None:
            fractions = [0.10, 0.25, 0.50, 0.75, 1.00]
        
        results = {}
        
        print("\n" + "="*80)
        print("KELLY FRACTION COMPARISON")
        print("="*80)
        print(f"Historical win rate: {win_rate:.1%}")
        print(f"Testing {len(games)} games\n")
        
        for frac in fractions:
            _, result = self.simulate_betting(games, win_rate, frac)
            results[frac] = result
            
            print(f"{result}")
        
        return results
    
    def recommend_fraction(self, results: Dict[float, KellyResults]) -> float:
        """
        Recommend optimal Kelly fraction based on results
        
        Args:
            results: Results from test_kelly_fractions
            
        Returns:
            Recommended fraction
        """
        # Filter out bankrupt scenarios
        viable = {k: v for k, v in results.items() if v.final_bankroll > 0}
        
        if not viable:
            return 0.0
        
        # Score based on: ROI (60%), Sharpe (20%), Max DD (20%)
        best_score = -float('inf')
        best_fraction = 0.0
        
        for frac, res in viable.items():
            # Normalize metrics (higher is better)
            roi_score = res.roi
            sharpe_score = res.sharpe_ratio / 10  # Scale to similar range
            dd_score = 1 - res.max_drawdown_pct  # Lower drawdown is better
            
            total_score = (0.6 * roi_score + 
                          0.2 * sharpe_score + 
                          0.2 * dd_score)
            
            if total_score > best_score:
                best_score = total_score
                best_fraction = frac
        
        return best_fraction
    
    def plot_bankroll_progression(self, 
                                  games: pd.DataFrame,
                                  win_rate: float,
                                  fractions: List[float] = None,
                                  output_file: str = None):
        """
        Plot bankroll progression for different Kelly fractions
        
        Args:
            games: DataFrame with 'won' column
            win_rate: Historical win rate
            fractions: List of fractions to plot
            output_file: Optional filename to save plot
        """
        if fractions is None:
            fractions = [0.10, 0.25, 0.50, 1.00]
        
        plt.figure(figsize=(12, 7))
        
        for frac in fractions:
            bet_df, _ = self.simulate_betting(games, win_rate, frac)
            
            if len(bet_df) > 0:
                plt.plot(bet_df['bet_num'], bet_df['bankroll'], 
                        label=f'{frac:.0%} Kelly', linewidth=2)
        
        plt.axhline(y=self.initial_bankroll, color='gray', 
                   linestyle='--', label='Starting Bankroll')
        plt.xlabel('Bet Number', fontsize=12)
        plt.ylabel('Bankroll ($)', fontsize=12)
        plt.title('Bankroll Progression by Kelly Fraction', fontsize=14, fontweight='bold')
        plt.legend(loc='best')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=300)
            print(f"✓ Saved plot to {output_file}")
        else:
            plt.show()
    
    def analyze_tier_kelly(self, 
                          tier_games: pd.DataFrame,
                          tier_name: str,
                          win_rate: float) -> Dict:
        """
        Complete Kelly analysis for a specific tier
        
        Args:
            tier_games: DataFrame with games for this tier (must have 'won' column)
            tier_name: Name of the tier
            win_rate: Historical win rate
            
        Returns:
            Analysis results dictionary
        """
        print("\n" + "="*80)
        print(f"KELLY ANALYSIS - {tier_name}")
        print("="*80)
        print(f"Games: {len(tier_games)}")
        print(f"Win rate: {win_rate:.1%}")
        
        # Test different fractions
        results = self.test_kelly_fractions(tier_games, win_rate)
        
        # Recommend optimal
        recommended = self.recommend_fraction(results)
        
        print(f"\n{'='*80}")
        print(f"RECOMMENDATION: {recommended:.0%} Kelly")
        print(f"{'='*80}")
        
        if recommended > 0:
            rec_result = results[recommended]
            print(f"Expected final bankroll: ${rec_result.final_bankroll:,.2f}")
            print(f"Expected ROI: {rec_result.roi:.1%}")
            print(f"Max drawdown: {rec_result.max_drawdown_pct:.1%}")
            print(f"Sharpe ratio: {rec_result.sharpe_ratio:.2f}")
        
        return {
            'tier': tier_name,
            'games': len(tier_games),
            'win_rate': win_rate,
            'recommended_fraction': recommended,
            'test_results': {k: {
                'final_bankroll': v.final_bankroll,
                'roi': v.roi,
                'max_drawdown_pct': v.max_drawdown_pct,
                'sharpe_ratio': v.sharpe_ratio
            } for k, v in results.items()}
        }


def main():
    """Example usage"""
    import pandas as pd
    
    # Example: Create dummy tier data (replace with actual tier games)
    # This simulates a tier with 60% win rate
    np.random.seed(42)
    n_games = 100
    win_rate = 0.60
    
    dummy_games = pd.DataFrame({
        'won': np.random.random(n_games) < win_rate,
        'date': pd.date_range('2024-01-01', periods=n_games)
    })
    
    # Initialize validator
    validator = KellyValidator(initial_bankroll=1000.0)
    
    # Test different Kelly fractions
    results = validator.test_kelly_fractions(dummy_games, win_rate)
    
    # Get recommendation
    recommended = validator.recommend_fraction(results)
    print(f"\n{'='*80}")
    print(f"OPTIMAL KELLY FRACTION: {recommended:.0%}")
    print(f"{'='*80}")
    
    # Plot results
    validator.plot_bankroll_progression(
        dummy_games, 
        win_rate,
        output_file='kelly_comparison.png'
    )


if __name__ == "__main__":
    main()
