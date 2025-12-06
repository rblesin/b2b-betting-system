from scraper import HockeyReferenceScraper
from analyzer import B2BAnalyzer
import pandas as pd
from datetime import datetime, timedelta

def main():
    """Analyze current 2025-26 season with upcoming B2B opportunities"""
    
    print("="*70)
    print("NHL 2025-26 SEASON - B2B BETTING ANALYSIS")
    print("="*70)
    
    print("\n[1/4] Fetching games from Hockey-Reference...")
    scraper = HockeyReferenceScraper(season="2026")
    completed_df, upcoming_df = scraper.scrape_all_games()
    
    print("\n[2/4] Fetching current standings...")
    standings = scraper.scrape_standings()
    
    # Show top 10 teams to verify standings
    print("\n📊 TOP 10 TEAMS BY POINTS:")
    sorted_teams = sorted(standings.items(), key=lambda x: x[1]['points'], reverse=True)[:10]
    for team, data in sorted_teams:
        print(f"   #{data['rank']} {team}: {data['points']} pts")
    
    if len(completed_df) == 0:
        print("\n❌ No completed games found.")
        return
    
    print("\n[3/4] Analyzing completed games for B2B performance...")
    analyzer = B2BAnalyzer(completed_df)
    games_with_rest = analyzer.calculate_rest_days()
    results = analyzer.analyze_win_rates()
    team_stats = analyzer.analyze_team_b2b_performance()
    
    # Analyze OT/SO in B2B games
    analyze_b2b_ot_so(games_with_rest, completed_df)
    
    print("\n[4/4] Identifying upcoming B2B betting opportunities...")
    upcoming_b2b = calculate_upcoming_b2b(completed_df, upcoming_df, days_ahead=7)
    
    if len(upcoming_b2b) == 0:
        print("\n❌ No B2B situations in next 7 days.")
    else:
        print_betting_opportunities(upcoming_b2b, team_stats, standings)


def analyze_b2b_ot_so(games_with_rest, completed_df):
    """Analyze OT/SO in B2B games - who wins?"""
    
    # Merge rest info with game results (including home_win and ot_so)
    merged = games_with_rest.merge(
        completed_df[['date', 'home', 'away', 'ot_so', 'home_win', 'home_goals', 'away_goals']], 
        on=['date', 'home', 'away'], 
        how='left',
        suffixes=('', '_result')
    )
    
    # Use home_win from completed_df (the _result suffix one if there's a conflict)
    if 'home_win_result' in merged.columns:
        merged['home_win'] = merged['home_win_result']
        merged = merged.drop(columns=['home_win_result'])
    
    # Filter for B2B games only
    b2b_games = merged[(merged['home_b2b']) | (merged['away_b2b'])].copy()
    
    total_b2b = len(b2b_games)
    ot_b2b = len(b2b_games[b2b_games['ot_so'] == 'OT'])
    so_b2b = len(b2b_games[b2b_games['ot_so'] == 'SO'])
    reg_b2b = len(b2b_games[b2b_games['ot_so'] == ''])
    
    # Overall games
    total_games = len(completed_df)
    ot_games = len(completed_df[completed_df['ot_so'] == 'OT'])
    so_games = len(completed_df[completed_df['ot_so'] == 'SO'])
    reg_games = len(completed_df[completed_df['ot_so'] == ''])
    
    print("\n" + "="*70)
    print("📊 OT/SO ANALYSIS")
    print("="*70)
    
    print(f"\nALL GAMES:")
    print(f"   Regulation: {reg_games}/{total_games} ({reg_games/total_games*100:.1f}%)")
    print(f"   Overtime: {ot_games}/{total_games} ({ot_games/total_games*100:.1f}%)")
    print(f"   Shootout: {so_games}/{total_games} ({so_games/total_games*100:.1f}%)")
    
    print(f"\nB2B GAMES:")
    print(f"   Regulation: {reg_b2b}/{total_b2b} ({reg_b2b/total_b2b*100:.1f}%)")
    print(f"   Overtime: {ot_b2b}/{total_b2b} ({ot_b2b/total_b2b*100:.1f}%)")
    print(f"   Shootout: {so_b2b}/{total_b2b} ({so_b2b/total_b2b*100:.1f}%)")
    
    ot_so_rate_all = (ot_games + so_games) / total_games * 100
    ot_so_rate_b2b = (ot_b2b + so_b2b) / total_b2b * 100
    
    print(f"\n💡 B2B games go to OT/SO {ot_so_rate_b2b:.1f}% vs {ot_so_rate_all:.1f}% overall")
    
    # Analyze WHO WINS in OT/SO for B2B games
    ot_so_b2b = b2b_games[(b2b_games['ot_so'] == 'OT') | (b2b_games['ot_so'] == 'SO')]
    
    if len(ot_so_b2b) > 0:
        print(f"\n🎯 WHO WINS OT/SO IN B2B GAMES? ({len(ot_so_b2b)} games)")
        print("="*70)
        
        # Home vs Away
        home_wins_ot_so = ot_so_b2b['home_win'].sum()
        away_wins_ot_so = len(ot_so_b2b) - home_wins_ot_so
        print(f"\n1. HOME vs AWAY in OT/SO:")
        print(f"   Home wins: {home_wins_ot_so}/{len(ot_so_b2b)} ({home_wins_ot_so/len(ot_so_b2b)*100:.1f}%)")
        print(f"   Away wins: {away_wins_ot_so}/{len(ot_so_b2b)} ({away_wins_ot_so/len(ot_so_b2b)*100:.1f}%)")
        
        # Rested vs B2B
        rested_wins = 0
        b2b_wins = 0
        
        for _, game in ot_so_b2b.iterrows():
            home_rested = not game['home_b2b']
            away_rested = not game['away_b2b']
            home_won = game['home_win']
            
            if home_rested and not away_rested:
                # Home rested, away B2B
                if home_won:
                    rested_wins += 1
                else:
                    b2b_wins += 1
            elif away_rested and not home_rested:
                # Away rested, home B2B
                if not home_won:
                    rested_wins += 1
                else:
                    b2b_wins += 1
            # Skip if both B2B
        
        total_rested_vs_b2b = rested_wins + b2b_wins
        if total_rested_vs_b2b > 0:
            print(f"\n2. RESTED vs B2B TEAM in OT/SO:")
            print(f"   Rested team wins: {rested_wins}/{total_rested_vs_b2b} ({rested_wins/total_rested_vs_b2b*100:.1f}%)")
            print(f"   B2B team wins: {b2b_wins}/{total_rested_vs_b2b} ({b2b_wins/total_rested_vs_b2b*100:.1f}%)")
            
            if rested_wins/total_rested_vs_b2b > 0.6:
                print(f"\n   🔥 INSIGHT: Rested teams dominate OT/SO vs B2B!")
            elif b2b_wins/total_rested_vs_b2b > 0.6:
                print(f"\n   ⚠️  SURPRISING: B2B teams actually win more OT/SO!")


def calculate_upcoming_b2b(completed_df, upcoming_df, days_ahead=7):
    """Calculate which upcoming games involve B2B situations"""
    
    today = datetime.now().date()
    cutoff_date = today + timedelta(days=days_ahead)
    
    upcoming_next_week = upcoming_df[
        (upcoming_df['date'] >= today) & 
        (upcoming_df['date'] <= cutoff_date)
    ].copy()
    
    if len(upcoming_next_week) == 0:
        return pd.DataFrame()
    
    print(f"   Analyzing {len(upcoming_next_week)} games...")
    
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


def print_betting_opportunities(upcoming_b2b, team_stats, standings):
    """Print betting opportunities with standings"""
    
    print("\n" + "="*70)
    print("🎯 UPCOMING B2B BETTING OPPORTUNITIES")
    print("="*70)
    print(f"\n✅ Found {len(upcoming_b2b)} games with B2B situations\n")
    
    for i, (_, game) in enumerate(upcoming_b2b.iterrows(), 1):
        print("="*70)
        print(f"OPPORTUNITY #{i}")
        print("="*70)
        print(f"📅 {game['date'].strftime('%A, %B %d, %Y')}")
        print(f"🏒 {game['away']} @ {game['home']}")
        
        # Show standings
        home_rank = standings.get(game['home'], {}).get('rank', '?')
        home_pts = standings.get(game['home'], {}).get('points', '?')
        away_rank = standings.get(game['away'], {}).get('rank', '?')
        away_pts = standings.get(game['away'], {}).get('points', '?')
        
        print(f"📊 Standings: {game['home']} (#{home_rank}, {home_pts}pts) vs {game['away']} (#{away_rank}, {away_pts}pts)")
        print(f"😴 Rest: {game['home']} = {game['home_rest']}d | {game['away']} = {game['away_rest']}d")
        
        print("\n📈 B2B PERFORMANCE:")
        
        if game['home_b2b']:
            print(f"   ⚠️  {game['home']} on B2B at home")
            if game['home'] in team_stats:
                stats = team_stats[game['home']]
                print(f"      Home B2B: {stats['home_b2b_wins']}-{stats['home_b2b']-stats['home_b2b_wins']} ({stats['home_b2b_pct']:.0f}%)")
        else:
            print(f"   ✅ {game['home']} RESTED at home")
        
        if game['away_b2b']:
            print(f"   ⚠️  {game['away']} on B2B away")
            if game['away'] in team_stats:
                stats = team_stats[game['away']]
                print(f"      Away B2B: {stats['away_b2b_wins']}-{stats['away_b2b']-stats['away_b2b_wins']} ({stats['away_b2b_pct']:.0f}%)")
        else:
            print(f"   ✅ {game['away']} RESTED away")
        
        print(f"\n💡 BET:")
        if game['home_b2b'] and not game['away_b2b']:
            print(f"   ✅ {game['away']} (61% historical edge)")
            if game['home'] in team_stats and team_stats[game['home']]['home_b2b_pct'] < 40:
                print(f"   🔥 STRONG: {game['home']} wins only {team_stats[game['home']]['home_b2b_pct']:.0f}% home B2B")
        elif game['away_b2b'] and not game['home_b2b']:
            print(f"   ✅ {game['home']} (70% historical edge)")
            if game['away'] in team_stats and team_stats[game['away']]['away_b2b_pct'] < 40:
                print(f"   🔥 STRONG: {game['away']} wins only {team_stats[game['away']]['away_b2b_pct']:.0f}% away B2B")
        else:
            print(f"   ⏭️  SKIP")
        
        print()
    
    print("="*70)


if __name__ == "__main__":
    main()
