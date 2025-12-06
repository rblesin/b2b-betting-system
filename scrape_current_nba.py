import requests
import pandas as pd
from datetime import datetime, timedelta

print("="*80)
print("SCRAPING CURRENT NBA SEASON 2025-26")
print("="*80)

base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"

all_games = []

# CORRECT: Current season started Oct 2025
start_date = datetime(2025, 10, 21)  # First game Oct 21, 2025
end_date = datetime.now()

print(f"Scraping from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

current_date = start_date
day_count = 0

while current_date <= end_date:
    date_str = current_date.strftime('%Y%m%d')
    url = f"{base_url}/scoreboard?dates={date_str}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            
            for event in events:
                competition = event['competitions'][0]
                
                # Only completed games
                if not competition['status']['type']['completed']:
                    continue
                
                competitors = competition['competitors']
                home_team = next((c for c in competitors if c['homeAway'] == 'home'), None)
                away_team = next((c for c in competitors if c['homeAway'] == 'away'), None)
                
                if not home_team or not away_team:
                    continue
                
                game_date = datetime.strptime(event['date'], '%Y-%m-%dT%H:%M%SZ').date()
                
                game = {
                    'date': game_date,
                    'away': away_team['team']['displayName'],
                    'home': home_team['team']['displayName'],
                    'away_points': int(away_team['score']),
                    'home_points': int(home_team['score']),
                    'home_win': int(home_team['score']) > int(away_team['score'])
                }
                
                all_games.append(game)
        
        day_count += 1
        if day_count % 10 == 0:
            print(f"  Progress: {current_date.strftime('%Y-%m-%d')} ({len(all_games)} games)")
    
    except:
        pass
    
    current_date += timedelta(days=1)

print(f"\n✅ Scraped {len(all_games)} games")

if len(all_games) == 0:
    print("\n❌ No games found! Check if season has started.")
else:
    # Create DataFrame
    df = pd.DataFrame(all_games)
    df = df.sort_values('date').reset_index(drop=True)
    
    # Calculate rest days
    last_game = {}
    
    for idx in df.index:
        home = df.at[idx, 'home']
        away = df.at[idx, 'away']
        game_date = df.at[idx, 'date']
        
        home_rest = (game_date - last_game[home]).days if home in last_game else 999
        away_rest = (game_date - last_game[away]).days if away in last_game else 999
        
        df.at[idx, 'home_rest'] = home_rest
        df.at[idx, 'away_rest'] = away_rest
        df.at[idx, 'home_b2b'] = home_rest == 1
        df.at[idx, 'away_b2b'] = away_rest == 1
        
        last_game[home] = game_date
        last_game[away] = game_date
    
    # Save
    df.to_csv('nba_completed_games_2025.csv', index=False)
    
    print(f"💾 Saved to: nba_completed_games_2025.csv")
    print(f"\nDate range: {df['date'].min()} to {df['date'].max()}")
    
    # B2B Analysis
    b2b_games = df[
        ((df['home_b2b'] == True) & (df['away_b2b'] == False)) |
        ((df['home_b2b'] == False) & (df['away_b2b'] == True))
    ]
    
    print(f"\nB2B situations: {len(b2b_games)} ({len(b2b_games)/len(df)*100:.1f}%)")
    
    print("\n✅ Current NBA season data ready!")
