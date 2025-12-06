from flask import Flask, jsonify, send_file
from scraper import HockeyReferenceScraper
from analyzer import B2BAnalyzer
from betting_tracker import BettingTracker
from datetime import datetime, timedelta
import pandas as pd
import os

app = Flask(__name__)

# Global data cache
data_cache = {
    'last_update': None,
    'data': None
}

def get_fresh_data():
    """Get fresh data from analysis"""
    
    print("🔄 Fetching fresh data...")
    
    # Initialize
    tracker = BettingTracker(tracker_file='betting_tracker.json', initial_bankroll=1000)
    scraper = HockeyReferenceScraper(season="2026")
    
    # Get games
    completed_df, upcoming_df = scraper.scrape_all_games()
    standings = scraper.scrape_standings()
    
    # Analyze
    analyzer = B2BAnalyzer(completed_df)
    games_with_rest = analyzer.calculate_rest_days()
    results = analyzer.analyze_win_rates()
    team_stats = analyzer.analyze_team_b2b_performance()
    
    # Update completed bets
    update_completed_bets(tracker, completed_df, games_with_rest)
    
    # Get upcoming B2B games
    upcoming_b2b = calculate_upcoming_b2b(completed_df, upcoming_df, days_ahead=7)
    
    # Build response
    data = {
        'bankroll': tracker.current_bankroll,
        'initial_bankroll': tracker.initial_bankroll,
        'total_bets': len([b for b in tracker.bets if b['result'] != 'pending']),
        'wins': len([b for b in tracker.bets if b['result'] == 'won']),
        'losses': len([b for b in tracker.bets if b['result'] == 'lost']),
        'upcoming_bets': format_upcoming_bets(upcoming_b2b, team_stats),
        'active_bets': [b for b in tracker.bets if b['result'] == 'pending'],
        'history': [b for b in tracker.bets if b['result'] != 'pending'][-20:],  # Last 20
        'stats': format_stats(results, team_stats)
    }
    
    print(f"✅ Data refreshed: {len(data['upcoming_bets'])} upcoming, {len(data['active_bets'])} active")
    
    return data


def update_completed_bets(tracker, completed_df, games_with_rest):
    """Update tracker with completed game results"""
    merged = games_with_rest.merge(
        completed_df[['date', 'home', 'away', 'home_win']], 
        on=['date', 'home', 'away'],
        how='left',
        suffixes=('', '_result')
    )
    
    if 'home_win_result' in merged.columns:
        merged['home_win'] = merged['home_win_result']
    
    for _, game in merged.iterrows():
        if pd.notna(game['home_win']):
            tracker.update_result(game['date'], game['home'], game['away'], game['home_win'])


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


def format_upcoming_bets(upcoming_b2b, team_stats):
    """Format upcoming bets for frontend"""
    bets = []
    
    for _, game in upcoming_b2b.iterrows():
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
                    reason += f" ({game['home']} only {home_pct:.0f}% at home B2B)"
                    
        elif game['away_b2b'] and not game['home_b2b']:
            pick = game['home']
            edge = 70.2
            reason = f"Rested home vs B2B away"
            
            if game['away'] in team_stats:
                away_pct = team_stats[game['away']]['away_b2b_pct']
                if away_pct < 40:
                    edge = 75
                    strong = True
                    reason += f" ({game['away']} only {away_pct:.0f}% away B2B)"
        
        if pick:
            # Calculate Kelly bet
            kelly_fraction = (edge / 100) * 0.25  # Fractional Kelly
            kelly_fraction = min(kelly_fraction, 0.05)  # Max 5%
            bet_amount = 1000 * kelly_fraction  # Using initial bankroll
            
            bets.append({
                'date': str(game['date']),
                'home': game['home'],
                'away': game['away'],
                'pick': pick,
                'edge': edge,
                'bet_amount': bet_amount,
                'reason': reason,
                'strong': strong
            })
    
    return bets


def format_stats(results, team_stats):
    """Format season stats for frontend"""
    
    # Get best and worst teams
    sorted_teams = sorted(team_stats.items(), key=lambda x: x[1]['win_pct'], reverse=True)
    
    best_teams = [
        {
            'name': team,
            'total_b2b': stats['total_b2b'],
            'wins': stats['total_wins'],
            'win_pct': stats['win_pct']
        }
        for team, stats in sorted_teams[:5]
    ]
    
    worst_teams = [
        {
            'name': team,
            'total_b2b': stats['total_b2b'],
            'wins': stats['total_wins'],
            'win_pct': stats['win_pct']
        }
        for team, stats in sorted_teams[-5:]
    ]
    
    return {
        'rested_home_vs_b2b_away': {
            'games': len(results['rested_home_b2b_away']),
            'win_pct': results['rested_home_b2b_away']['home_win'].mean() * 100 if len(results['rested_home_b2b_away']) > 0 else 0
        },
        'rested_away_vs_b2b_home': {
            'games': len(results['b2b_home_rested_away']),
            'win_pct': (1 - results['b2b_home_rested_away']['home_win'].mean()) * 100 if len(results['b2b_home_rested_away']) > 0 else 0
        },
        'overall_rest_advantage': {
            'games': len(results['rested_home_b2b_away']) + len(results['b2b_home_rested_away']),
            'win_pct': 67.7  # From your data
        },
        'best_teams': best_teams,
        'worst_teams': worst_teams
    }


@app.route('/')
def index():
    """Serve the dashboard HTML"""
    return send_file('dashboard.html')


@app.route('/api/data')
def get_data():
    """API endpoint for dashboard data"""
    global data_cache
    
    # Check if we need to refresh (every hour or if no data)
    now = datetime.now()
    if (data_cache['last_update'] is None or 
        (now - data_cache['last_update']).seconds > 3600):
        
        data_cache['data'] = get_fresh_data()
        data_cache['last_update'] = now
    
    return jsonify(data_cache['data'])


@app.route('/api/refresh')
def force_refresh():
    """Manually force a data refresh"""
    data_cache['data'] = get_fresh_data()
    data_cache['last_update'] = datetime.now()
    return jsonify({'status': 'refreshed'})


if __name__ == '__main__':
    print("="*60)
    print("🏒 NHL B2B BETTING DASHBOARD SERVER")
    print("="*60)
    print("\n✅ Starting server...")
    print("📊 Dashboard: http://localhost:5000")
    print("🔄 Auto-refresh: Every hour")
    print("💾 Data: betting_tracker.json")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
