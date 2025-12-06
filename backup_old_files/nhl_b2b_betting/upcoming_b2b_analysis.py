from scraper import HockeyReferenceScraper
from analyzer import B2BAnalyzer
import pandas as pd
from datetime import datetime, timedelta

def main():
    """Analyze 2025-26 season and show upcoming B2B opportunities"""
    
    print("="*60)
    print("NHL 2025-26 SEASON - UPCOMING B2B ANALYSIS")
    print("="*60)
    
    # Use 2026 for 2025-26 season
    scraper = HockeyReferenceScraper(season="2026")
    
    try:
        games_df = scraper.scrape_schedule()
        print(f"Found {len(games_df)} completed games so far this season")
    except Exception as e:
        print(f"Error scraping data: {e}")
        print("\nNote: The 2025-26 season may not have started yet.")
        return
    
    # Analyze completed games
    analyzer = B2BAnalyzer(games_df)
    analyzer.calculate_rest_days()
    
    # Overall B2B win rates
    print("\n" + "="*60)
    print("SEASON STATS SO FAR")
    print("="*60)
    results = analyzer.analyze_win_rates()
    
    # Team-specific B2B performance
    team_stats = analyzer.analyze_team_b2b_performance()
    
    # Now get upcoming games
    print("\n" + "="*60)
    print("UPCOMING B2B BETTING OPPORTUNITIES (Next 7 Days)")
    print("="*60)
    
    upcoming_b2b = get_upcoming_b2b_games(analyzer, team_stats, days_ahead=7)
    
    if len(upcoming_b2b) == 0:
        print("\nNo upcoming B2B games found in the next 7 days.")
    else:
        print(f"\nFound {len(upcoming_b2b)} upcoming B2B betting opportunities:\n")
        
        for _, game in upcoming_b2b.iterrows():
            print("="*60)
            print(f"Date: {game['date']}")
            print(f"Matchup: {game['home']} (HOME) vs {game['away']} (AWAY)")
            print(f"Rest: {game['home']} has {game['home_rest']} days | {game['away']} has {game['away_rest']} days")
            
            if game['home_b2b']:
                print(f"⚠️  {game['home']} is on BACK-TO-BACK (home)")
                if game['home'] in team_stats:
                    print(f"   Historical B2B home win rate: {team_stats[game['home']]['home_b2b_pct']:.1f}%")
            
            if game['away_b2b']:
                print(f"⚠️  {game['away']} is on BACK-TO-BACK (away)")
                if game['away'] in team_stats:
                    print(f"   Historical B2B away win rate: {team_stats[game['away']]['away_b2b_pct']:.1f}%")
            
            print(f"\n💡 BETTING RECOMMENDATION:")
            if game['home_b2b'] and not game['away_b2b']:
                print(f"   BET ON: {game['away']} (rested away team)")
                print(f"   Reason: Home team on B2B, away team rested")
                if game['away'] in team_stats:
                    print(f"   Expected edge: Rested away wins ~58.7% vs B2B home")
            elif game['away_b2b'] and not game['home_b2b']:
                print(f"   BET ON: {game['home']} (rested home team)")
                print(f"   Reason: Away team on B2B, home team rested")
                if game['home'] in team_stats:
                    print(f"   Expected edge: Rested home wins ~63.0% vs B2B away")
            else:
                print(f"   SKIP: Both teams on B2B (no clear advantage)")
    
    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)


def get_upcoming_b2b_games(analyzer, team_stats, days_ahead=7):
    """
    Find upcoming B2B games by scraping the full schedule (including future games)
    and identifying which teams will be on B2B
    """
    
    # We need to scrape ALL games (including upcoming ones)
    # For now, we'll use the completed games to track team schedules
    # and identify upcoming B2B situations
    
    # This is a simplified version - in reality you'd need to:
    # 1. Scrape the full schedule including future games
    # 2. Calculate rest days for upcoming games based on last completed game
    # 3. Filter for next 7 days
    
    # For demonstration, let's create a placeholder
    # You would need to modify the scraper to also get upcoming games
    
    print("\n⚠️  Note: Full upcoming game analysis requires scraping future games.")
    print("This feature needs the scraper to be modified to include unplayed games.")
    
    return pd.DataFrame()  # Empty for now


if __name__ == "__main__":
    main()
