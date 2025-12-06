"""
NHL B2B Multi-Season Analysis Runner
Complete workflow for analyzing betting system across multiple seasons
"""

import pandas as pd
import numpy as np
from multi_season_scraper import MultiSeasonScraper
from multi_season_analyzer import MultiSeasonAnalyzer
from kelly_validator import KellyValidator
import json
from datetime import datetime


def print_header(text: str, char: str = "="):
    """Print a formatted header"""
    print(f"\n{char * 80}")
    print(f"{text:^80}")
    print(f"{char * 80}\n")


def run_complete_analysis(seasons: list = None, 
                         force_refresh: bool = False,
                         initial_bankroll: float = 1000.0):
    """
    Run complete multi-season analysis pipeline
    
    Args:
        seasons: List of season years to analyze (default: last 3 seasons)
        force_refresh: Force data refresh from web
        initial_bankroll: Starting bankroll for simulations
    """
    
    if seasons is None:
        seasons = ["2022", "2023", "2024"]
    
    print_header("NHL B2B MULTI-SEASON ANALYSIS")
    print(f"Analyzing seasons: {', '.join([f'{s}-{int(s)+1}' for s in seasons])}")
    print(f"Starting bankroll: ${initial_bankroll:,.2f}")
    print(f"Force refresh: {force_refresh}")
    
    # ========================================================================
    # STEP 1: SCRAPE DATA
    # ========================================================================
    print_header("STEP 1: DATA COLLECTION", "-")
    
    scraper = MultiSeasonScraper(seasons=seasons)
    df = scraper.get_complete_dataset(force_refresh=force_refresh)
    
    if df.empty:
        print("ERROR: No data collected. Check your internet connection.")
        return None
    
    # Save raw data
    raw_data_file = "multi_season_games.csv"
    df.to_csv(raw_data_file, index=False)
    print(f"✓ Saved raw data to {raw_data_file}")
    
    # ========================================================================
    # STEP 2: ANALYZE TIERS
    # ========================================================================
    print_header("STEP 2: TIER ANALYSIS", "-")
    
    analyzer = MultiSeasonAnalyzer(df)
    tier_results = analyzer.analyze_all_tiers()
    
    # ========================================================================
    # STEP 3: COMPARE HOME VS AWAY
    # ========================================================================
    print_header("STEP 3: HOME VS AWAY COMPARISON", "-")
    
    comparison = analyzer.compare_home_vs_away()
    
    print("Overall rested vs B2B performance:\n")
    print(f"HOME RESTED:")
    print(f"  Games: {comparison['home_rested']['games']}")
    print(f"  Win rate: {comparison['home_rested']['win_rate']:.1%}")
    print(f"  Record: {comparison['home_rested']['wins']}-"
          f"{comparison['home_rested']['games'] - comparison['home_rested']['wins']}")
    
    print(f"\nAWAY RESTED:")
    print(f"  Games: {comparison['away_rested']['games']}")
    print(f"  Win rate: {comparison['away_rested']['win_rate']:.1%}")
    print(f"  Record: {comparison['away_rested']['wins']}-"
          f"{comparison['away_rested']['games'] - comparison['away_rested']['wins']}")
    
    # ========================================================================
    # STEP 4: KELLY CRITERION ANALYSIS
    # ========================================================================
    print_header("STEP 4: KELLY CRITERION VALIDATION", "-")
    
    validator = KellyValidator(initial_bankroll=initial_bankroll)
    kelly_results = {}
    
    # Analyze each profitable tier
    for tier_key, perf in tier_results.items():
        if perf.games >= 30 and perf.win_rate >= 0.51:  # Minimum viable
            print(f"\n{'*' * 80}")
            print(f"Analyzing: {perf.name}")
            print(f"{'*' * 80}")
            
            # Get games for this tier
            tier_games_full = analyzer.analyze_tier(tier_key, return_games=True)
            
            # Create DataFrame with results
            tier_df = pd.DataFrame([
                {
                    'date': g['date'],
                    'won': g['won']
                }
                for g in tier_games_full.sample_games
            ])
            
            if len(tier_df) > 0:
                # Run Kelly analysis
                kelly_analysis = validator.analyze_tier_kelly(
                    tier_df,
                    perf.name,
                    perf.win_rate
                )
                kelly_results[tier_key] = kelly_analysis
    
    # ========================================================================
    # STEP 5: GENERATE RECOMMENDATIONS
    # ========================================================================
    print_header("STEP 5: FINAL RECOMMENDATIONS", "-")
    
    recommended_tiers = analyzer.get_tier_recommendations(
        min_games=30,
        min_winrate=0.525
    )
    
    print(f"Tiers meeting profitability criteria (≥30 games, ≥52.5% win rate):")
    
    if recommended_tiers:
        print("")
        for i, tier_key in enumerate(recommended_tiers, 1):
            perf = tier_results[tier_key]
            kelly_frac = kelly_results.get(tier_key, {}).get('recommended_fraction', 0.25)
            
            print(f"{i}. {perf.name}")
            print(f"   Win rate: {perf.win_rate:.1%} over {perf.games} games")
            print(f"   Record: {perf.wins}-{perf.losses}")
            print(f"   Recommended Kelly: {kelly_frac:.0%}")
            print("")
    else:
        print("\n⚠️  No tiers currently meet profitability criteria")
        print("   Consider:")
        print("   - Adjusting tier definitions")
        print("   - Collecting more data")
        print("   - Lowering minimum sample size")
    
    # ========================================================================
    # STEP 6: EXPORT RESULTS
    # ========================================================================
    print_header("STEP 6: EXPORTING RESULTS", "-")
    
    # Generate updated config
    config = analyzer.generate_config_update(min_games=30)
    config['kelly_recommendations'] = {
        tier_key: {
            'fraction': kelly_results[tier_key]['recommended_fraction'],
            'expected_roi': kelly_results[tier_key]['test_results'].get(
                kelly_results[tier_key]['recommended_fraction'], {}
            ).get('roi', 0)
        }
        for tier_key in kelly_results.keys()
    }
    
    config_file = "recommended_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✓ Saved recommended config to {config_file}")
    
    # Export detailed results for top tiers
    for tier_key in recommended_tiers[:3]:  # Top 3 tiers
        tier_name = tier_results[tier_key].name.replace(' ', '_').lower()
        export_file = f"tier_details_{tier_name}.json"
        analyzer.export_tier_details(tier_key, export_file)
    
    # Create summary report
    summary = {
        'analysis_date': datetime.now().isoformat(),
        'seasons_analyzed': [f"{s}-{int(s)+1}" for s in seasons],
        'total_games': len(df),
        'total_rested_vs_b2b': df['rested_vs_b2b'].sum(),
        'home_vs_away': comparison,
        'tier_summary': {
            tier_key: {
                'name': perf.name,
                'games': perf.games,
                'wins': perf.wins,
                'losses': perf.losses,
                'win_rate': round(perf.win_rate, 4),
                'recommended': tier_key in recommended_tiers
            }
            for tier_key, perf in tier_results.items()
            if perf.games > 0
        },
        'recommended_tiers': recommended_tiers
    }
    
    summary_file = "analysis_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Saved analysis summary to {summary_file}")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print_header("ANALYSIS COMPLETE")
    
    print(f"Total games analyzed: {len(df):,}")
    print(f"Rested vs B2B matchups: {df['rested_vs_b2b'].sum():,}")
    print(f"Tiers evaluated: {len(tier_results)}")
    print(f"Profitable tiers found: {len(recommended_tiers)}")
    
    if recommended_tiers:
        best_tier_key = recommended_tiers[0]
        best_tier = tier_results[best_tier_key]
        print(f"\nBest performing tier:")
        print(f"  {best_tier.name}")
        print(f"  {best_tier.win_rate:.1%} over {best_tier.games} games")
        
        if best_tier_key in kelly_results:
            best_kelly = kelly_results[best_tier_key]
            print(f"  Recommended Kelly: {best_kelly['recommended_fraction']:.0%}")
    
    print("\nGenerated files:")
    print(f"  • {raw_data_file} - Complete game data")
    print(f"  • {config_file} - Recommended configuration")
    print(f"  • {summary_file} - Analysis summary")
    
    return {
        'df': df,
        'tier_results': tier_results,
        'kelly_results': kelly_results,
        'recommended_tiers': recommended_tiers,
        'config': config
    }


def run_quick_validation(season: str = "2024"):
    """
    Quick validation on a single season (for testing)
    
    Args:
        season: Season year to validate
    """
    print_header(f"QUICK VALIDATION - {season}-{int(season)+1}")
    
    scraper = MultiSeasonScraper(seasons=[season])
    df = scraper.get_complete_dataset(force_refresh=False)
    
    if df.empty:
        print("No data available")
        return
    
    analyzer = MultiSeasonAnalyzer(df)
    results = analyzer.analyze_all_tiers()
    
    print("\nTop 3 tiers by win rate:")
    sorted_tiers = sorted(
        [(k, v) for k, v in results.items() if v.games >= 10],
        key=lambda x: x[1].win_rate,
        reverse=True
    )
    
    for i, (tier_key, perf) in enumerate(sorted_tiers[:3], 1):
        print(f"{i}. {perf.name}: {perf.win_rate:.1%} ({perf.wins}-{perf.losses})")


if __name__ == "__main__":
    # Run complete analysis on last 3 seasons
    results = run_complete_analysis(
        seasons=["2022", "2023", "2024"],
        force_refresh=False,
        initial_bankroll=1000.0
    )
    
    # Uncomment to run quick validation instead:
    # run_quick_validation("2024")
