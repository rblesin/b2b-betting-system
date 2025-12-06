from scraper import HockeyReferenceScraper
from analyzer import B2BAnalyzer
from betting_tracker import BettingTracker
import pandas as pd
from datetime import datetime, timedelta

def main():
    """Analyze and track betting opportunities"""
    
    print("="*70)
    print("NHL B2B BETTING SYSTEM WITH KELLY CRITERION")
    print("="*70)
    
    # Initialize tracker
    tracker = BettingTracker(tracker_file='betting_tracker.json', initial_bankroll=1000)
    
    print("\n[1/5] Fetching games from Hockey-Reference...")
    scraper = HockeyReferenceScraper(season="2026")
    completed_df, upcoming_df = scraper.scrape_all_games()
    
    print("\n[2/5] Fetching standings...")
    standings = scraper.scrape_standings()
    
    print("\n[3/5] Analyzing B2B performance...")
    analyzer = B2BAnalyzer(completed_df)
    games_with_rest = analyzer.calculate_rest_days()
    results = analyzer.analyze_win_rates()
    team_stats = analyzer.analyze_team_b2b_performance()
    
    print("\n[4/5] Updating completed bets...")
    update_completed_bets(tracker, completed_df, games_with_rest)
    
    print("\n[5/5] Finding new betting opportunities...")
    upcoming_b2b = calculate_upcoming_b2b(completed_df, upcoming_df, days_ahead=7)
    
    if len(upcoming_b2b) > 0:
        add_new_bets(tracker, upcoming_b2b, team_stats, standings)
    
    # Show summary
    tracker.show_summary()
    tracker.show_recent_bets(15)


def update_completed_bets(tracker, completed_df, games_with_rest):
    """Check if any pending bets have been completed"""
    
    # Merge to get results
    merged = games_with_rest.merge(
        completed_df[['date', 'home', 'away', 'home_win']], 
        on=['date', 'home', 'away'],
        how='left',
        suffixes=('', '_result')
    )
    
    if 'home_win_result' in merged.columns:
        merged['home_win'] = merged['home_win_result']
    
    updated = 0
    for _, game in merged.iterrows():
        if pd.notna(game['home_win']):
            if tracker.update_result(game['date'], game['home'], game['away'], game['home_win']):
                updated += 1
    
    if updated > 0:
        print(f"   Updated {updated} completed bets")
    else:
        print(f"   No new results to update")


def calculate_upcoming_b2b(completed_df, upcoming_df, days_ahead=7):
    """Calculate upcoming B2B games"""
    
    today = datetime.now().date()
    cutoff_date = today + timedelta(days=days_ahead)
    
    upcoming_next_week = upcoming_df[
        (upcoming_df['date'] >= today) & 
        (upcoming_df['date'] <= cutoff_date)
    ].copy()
    
    if len(upcoming_next_week) == 0:
        return pd.DataFrame()
    
    last_game = {}
    for _, game in completed_df.sort_values('date').iterrows():
        last_game[game['home']] = game['date']
        last_game[game['away']] = game['date']
    
    results = []
    
    for _, game in upcoming_next_week.iterrows():
        home = game['home']
        away = game['away']
        game_date = game['date']
        
        home_rest = (game_date - last_game[home]).days if home in last_game else 999
        away_rest = (game_date - last_game[away]).days if away in last_game else 999
        
        home_b2b = home_rest == 1
        away_b2b = away_rest == 1
        
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
        
        last_game[home] = game_date
        last_game[away] = game_date
    
    return pd.DataFrame(results)


def add_new_bets(tracker, upcoming_b2b, team_stats, standings):
    """Add new betting opportunities to tracker"""
    
    print("\n🎯 NEW BETTING OPPORTUNITIES:")
    print("="*70)
    
    new_bets = 0
    
    for _, game in upcoming_b2b.iterrows():
        # Check if already bet on this game
        already_bet = any(
            bet['date'] == str(game['date']) and 
            bet['home'] == game['home'] and 
            bet['away'] == game['away']
            for bet in tracker.bets
        )
        
        if already_bet:
            continue
        
        # Determine pick and edge
        pick = None
        edge_pct = 0
        reason = ""
        
        if game['home_b2b'] and not game['away_b2b']:
            # Bet on rested away team
            pick = game['away']
            edge_pct = 61.1  # Historical edge
            reason = f"Rested away vs B2B home"
            
            # Boost edge if home team is terrible on B2B
            if game['home'] in team_stats:
                home_b2b_pct = team_stats[game['home']]['home_b2b_pct']
                if home_b2b_pct < 40:
                    edge_pct = 70
                    reason += f" (home {home_b2b_pct:.0f}% B2B)"
                    
        elif game['away_b2b'] and not game['home_b2b']:
            # Bet on rested home team
            pick = game['home']
            edge_pct = 70.2  # Historical edge
            reason = f"Rested home vs B2B away"
            
            # Boost edge if away team is terrible on B2B
            if game['away'] in team_stats:
                away_b2b_pct = team_stats[game['away']]['away_b2b_pct']
                if away_b2b_pct < 40:
                    edge_pct = 75
                    reason += f" (away {away_b2b_pct:.0f}% B2B)"
        
        if pick:
            tracker.add_bet(
                date=game['date'],
                home=game['home'],
                away=game['away'],
                pick=pick,
                edge_pct=edge_pct,
                reason=reason,
                odds=1.91  # Standard -110 odds
            )
            new_bets += 1
    
    if new_bets == 0:
        print("   No new bets to add")


if __name__ == "__main__":
    main()
