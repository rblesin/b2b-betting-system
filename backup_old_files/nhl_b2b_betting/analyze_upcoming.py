from full_schedule_scraper import FullScheduleScraper
from analyzer import B2BAnalyzer
import pandas as pd
from datetime import datetime, timedelta

def main():
    """Analyze 2025-26 season and show upcoming B2B opportunities"""
    
    print("="*60)
    print("NHL 2025-26 SEASON - UPCOMING B2B BETTING ANALYSIS")
    print("="*60)
    
    # Get both completed and upcoming games
    scraper = FullScheduleScraper(season="2026")
    
    try:
        completed_df, upcoming_df = scraper.scrape_all_games()
    except Exception as e:
        print(f"Error scraping data: {e}")
        return
    
    if len(completed_df) == 0:
        print("\nNo completed games yet this season. Season hasn't started.")
        return
    
    # Analyze completed games to get team B2B stats
    print("\n" + "="*60)
    print("ANALYZING COMPLETED GAMES")
    print("="*60)
    
    analyzer = B2BAnalyzer(completed_df)
    analyzer.calculate_rest_days()
    results = analyzer.analyze_win_rates()
    team_stats = analyzer.analyze_team_b2b_performance()
    
    # Find upcoming B2B games
    print("\n" + "="*60)
    print("UPCOMING B2B BETTING OPPORTUNITIES (Next 7 Days)")
    print("="*60)
    
    if len(upcoming_df) == 0:
        print("\nNo upcoming games found.")
        return
    
    # Calculate which teams will be on B2B for upcoming games
    upcoming_b2b = calculate_upcoming_b2b(completed_df, upcoming_df, days_ahead=7)
    
    if len(upcoming_b2b) == 0:
        print("\nNo B2B situations in the next 7 days.")
    else:
        print_betting_opportunities(upcoming_b2b, team_stats)


def calculate_upcoming_b2b(completed_df, upcoming_df, days_ahead=7):
    """Calculate which upcoming games involve B2B situations"""
    
    today = datetime.now().date()
    cutoff_date = today + timedelta(days=days_ahead)
    
    # Filter upcoming games to next N days
    upcoming_next_week = upcoming_df[
        (upcoming_df['date'] >= today) & 
        (upcoming_df['date'] <= cutoff_date)
    ].copy()
    
    if len(upcoming_next_week) == 0:
        return pd.DataFrame()
    
    # Track last game date for each team (from completed games)
    last_game = {}
    all_games = completed_df.sort_values('date')
    
    for _, game in all_games.iterrows():
        last_game[game['home']] = game['date']
        last_game[game['away']] = game['date']
    
    # Calculate rest for upcoming games
    results = []
    
    for _, game in upcoming_next_week.iterrows():
        home = game['home']
        away = game['away']
        game_date = game['date']
        
        # Calculate rest days
        home_rest = (game_date - last_game[home]).days if home in last_game else 999
        away_rest = (game_date - last_game[away]).days if away in last_game else 999
        
        home_b2b = home_rest == 1
        away_b2b = away_rest == 1
        
        # Only include games with at least one team on B2B
        if home_b2b or away_b2b:
            results.append({
                'date': game_date,
                'home': home,
                'away': away,
                'home_rest': home_rest,
                'away_rest': away_rest,
                'home_b2b': home_b2b,
                'away_b2b': away_b2b
            })
        
        # Update last_game tracker for future iterations
        last_game[home] = game_date
        last_game[away] = game_date
    
    return pd.DataFrame(results)


def print_betting_opportunities(upcoming_b2b, team_stats):
    """Print formatted betting opportunities"""
    
    print(f"\nFound {len(upcoming_b2b)} upcoming B2B betting opportunities:\n")
    
    for _, game in upcoming_b2b.iterrows():
        print("="*70)
        print(f"📅 Date: {game['date']}")
        print(f"🏒 Matchup: {game['home']} (HOME) vs {game['away']} (AWAY)")
        print(f"😴 Rest: {game['home']} = {game['home_rest']} days | {game['away']} = {game['away_rest']} days")
        
        if game['home_b2b']:
            print(f"\n⚠️  {game['home']} is on BACK-TO-BACK (playing at home)")
            if game['home'] in team_stats:
                stats = team_stats[game['home']]
                print(f"   Season B2B record: {stats['home_b2b_wins']}-{stats['home_b2b']-stats['home_b2b_wins']} ({stats['home_b2b_pct']:.1f}% at home)")
        
        if game['away_b2b']:
            print(f"\n⚠️  {game['away']} is on BACK-TO-BACK (playing away)")
            if game['away'] in team_stats:
                stats = team_stats[game['away']]
                print(f"   Season B2B record: {stats['away_b2b_wins']}-{stats['away_b2b']-stats['away_b2b_wins']} ({stats['away_b2b_pct']:.1f}% away)")
        
        print(f"\n💡 BETTING RECOMMENDATION:")
        if game['home_b2b'] and not game['away_b2b']:
            print(f"   ✅ BET ON: {game['away']} (RESTED AWAY TEAM)")
            print(f"   📊 Historical edge: Rested away teams win ~58.7% vs B2B home")
        elif game['away_b2b'] and not game['home_b2b']:
            print(f"   ✅ BET ON: {game['home']} (RESTED HOME TEAM)")
            print(f"   📊 Historical edge: Rested home teams win ~63.0% vs B2B away")
        else:
            print(f"   ⏭️  SKIP: Both teams on B2B (no edge)")
        
        print()


if __name__ == "__main__":
    main()
