from scraper import HockeyReferenceScraper
from analyzer import B2BAnalyzer
from betting_tracker import BettingTracker
from datetime import datetime, timedelta
import pandas as pd

def main():
    print("="*70)
    print("🏒 NHL B2B BETTING SYSTEM")
    print("="*70)
    
    # Load tracker
    tracker = BettingTracker(tracker_file='betting_tracker.json', initial_bankroll=1000)
    
    # Get data
    print("\n📥 Fetching latest data...")
    scraper = HockeyReferenceScraper(season="2026")
    completed_df, upcoming_df = scraper.scrape_all_games()
    
    # Analyze
    print("📊 Analyzing B2B performance...")
    analyzer = B2BAnalyzer(completed_df)
    games_with_rest = analyzer.calculate_rest_days()
    results = analyzer.analyze_win_rates()
    team_stats = analyzer.analyze_team_b2b_performance()
    
    # Get upcoming B2B games
    upcoming_b2b = calculate_upcoming_b2b(completed_df, upcoming_df, days_ahead=7)
    
    # Show dashboard
    show_dashboard(tracker)
    
    # Show upcoming bets
    show_upcoming_bets(upcoming_b2b, team_stats, tracker)
    
    # Show active bets
    show_active_bets(tracker)


def calculate_upcoming_b2b(completed_df, upcoming_df, days_ahead=7):
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


def show_dashboard(tracker):
    print("\n" + "="*70)
    print("💰 BANKROLL SUMMARY")
    print("="*70)
    
    pl = tracker.current_bankroll - tracker.initial_bankroll
    roi = (pl / tracker.initial_bankroll * 100)
    
    print(f"Starting Bankroll: ${tracker.initial_bankroll:.2f}")
    print(f"Current Bankroll:  ${tracker.current_bankroll:.2f}")
    print(f"Profit/Loss:       ${pl:+.2f} ({roi:+.1f}% ROI)")
    
    completed = [b for b in tracker.bets if b['result'] != 'pending']
    if len(completed) > 0:
        wins = len([b for b in completed if b['result'] == 'won'])
        losses = len([b for b in completed if b['result'] == 'lost'])
        win_rate = (wins / len(completed) * 100)
        print(f"Record:            {wins}-{losses} ({win_rate:.1f}% win rate)")


def show_upcoming_bets(upcoming_b2b, team_stats, tracker):
    print("\n" + "="*70)
    print("🎯 UPCOMING BETTING OPPORTUNITIES (Next 7 Days)")
    print("="*70)
    
    if len(upcoming_b2b) == 0:
        print("\n   No B2B opportunities in the next 7 days.")
        return
    
    count = 0
    for _, game in upcoming_b2b.iterrows():
        # Skip if already bet on this game
        already_bet = any(
            bet['date'] == str(game['date']) and 
            bet['home'] == game['home']
            for bet in tracker.bets
        )
        
        if already_bet:
            continue
        
        pick = None
        edge = 0
        reason = ""
        strong = False
        
        if game['home_b2b'] and not game['away_b2b']:
            pick = game['away']
            edge = 61.1
            reason = f"Rested away vs B2B home"
            
            if game['home'] in team_stats:
                home_pct = team_stats[game['home']]['home_b2b_pct']
                if home_pct < 40:
                    edge = 70
                    strong = True
                    reason += f" (Home {home_pct:.0f}% B2B)"
                    
        elif game['away_b2b'] and not game['home_b2b']:
            pick = game['home']
            edge = 70.2
            reason = f"Rested home vs B2B away"
            
            if game['away'] in team_stats:
                away_pct = team_stats[game['away']]['away_b2b_pct']
                if away_pct < 40:
                    edge = 75
                    strong = True
                    reason += f" (Away {away_pct:.0f}% B2B)"
        
        if pick:
            kelly_fraction = (edge / 100) * 0.25
            kelly_fraction = min(kelly_fraction, 0.05)
            bet_amount = tracker.current_bankroll * kelly_fraction
            
            count += 1
            print(f"\n{count}. {game['date']}")
            print(f"   {game['away']} @ {game['home']}")
            print(f"   {'🔥 STRONG' if strong else '✅'} BET ON: {pick}")
            print(f"   Bet Size: ${bet_amount:.2f} ({edge:.1f}% edge)")
            print(f"   Reason: {reason}")
    
    if count == 0:
        print("\n   No new opportunities (already bet on all B2B games)")


def show_active_bets(tracker):
    active = [b for b in tracker.bets if b['result'] == 'pending']
    
    if len(active) == 0:
        return
    
    print("\n" + "="*70)
    print("⏳ ACTIVE BETS (Waiting for Results)")
    print("="*70)
    
    for i, bet in enumerate(active, 1):
        print(f"\n{i}. {bet['date']}")
        print(f"   {bet['away']} @ {bet['home']}")
        print(f"   Pick: {bet['pick']} | Bet: ${bet['bet_amount']:.2f}")


if __name__ == "__main__":
    main()
