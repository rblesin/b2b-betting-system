import requests
import pandas as pd
from datetime import datetime, timedelta

print("="*80)
print("NBA B2B ANALYSIS - Fast scraper (completed games only)")
print("="*80)

base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"

all_games = []

# Scrape Oct 1 to Dec 4 (today)
start = datetime(2024, 10, 1)
end = datetime(2024, 12, 4)

current = start
day_count = 0

while current <= end:
    date_str = current.strftime('%Y%m%d')
    url = f"{base_url}/scoreboard?dates={date_str}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            
            for event in events:
                comp = event['competitions'][0]
                competitors = comp['competitors']
                
                home = next((c for c in competitors if c['homeAway'] == 'home'), None)
                away = next((c for c in competitors if c['homeAway'] == 'away'), None)
                
                if not home or not away:
                    continue
                
                game_date = datetime.strptime(event['date'], '%Y-%m-%dT%H:%M%SZ').date()
                
                game = {
                    'date': game_date,
                    'away': away['team']['displayName'],
                    'home': home['team']['displayName'],
                }
                
                if comp['status']['type']['completed']:
                    game['away_points'] = int(away['score'])
                    game['home_points'] = int(home['score'])
                    game['home_win'] = int(home['score']) > int(away['score'])
                
                all_games.append(game)
            
            day_count += 1
            if day_count % 10 == 0:
                print(f"  Progress: {current.strftime('%Y-%m-%d')} ({len(all_games)} games so far)")
    
    except:
        pass
    
    current += timedelta(days=1)  # Fixed!

df = pd.DataFrame(all_games)
completed = df[df['home_win'].notna()].copy()

print(f"\n✅ Found {len(completed)} completed games")

# Calculate rest
completed = completed.sort_values('date').reset_index(drop=True)
last_game = {}

for idx in completed.index:
    home = completed.at[idx, 'home']
    away = completed.at[idx, 'away']
    game_date = completed.at[idx, 'date']
    
    home_rest = (game_date - last_game[home]).days if home in last_game else 999
    away_rest = (game_date - last_game[away]).days if away in last_game else 999
    
    completed.at[idx, 'home_rest'] = home_rest
    completed.at[idx, 'away_rest'] = away_rest
    completed.at[idx, 'home_b2b'] = home_rest == 1
    completed.at[idx, 'away_b2b'] = away_rest == 1
    
    last_game[home] = game_date
    last_game[away] = game_date

# B2B Analysis
print("\n" + "="*80)
print("B2B ANALYSIS")
print("="*80)

b2b_games = completed[
    ((completed['home_b2b'] == True) & (completed['away_b2b'] == False)) |
    ((completed['home_b2b'] == False) & (completed['away_b2b'] == True))
]

print(f"Total games: {len(completed)}")
print(f"B2B situations: {len(b2b_games)} ({len(b2b_games)/len(completed)*100:.1f}%)")

# Win rate
rested_wins = 0
for _, game in b2b_games.iterrows():
    if game['home_b2b'] and not game['away_b2b']:
        # Away rested
        if not game['home_win']:
            rested_wins += 1
    elif not game['home_b2b'] and game['away_b2b']:
        # Home rested
        if game['home_win']:
            rested_wins += 1

wr = (rested_wins / len(b2b_games) * 100) if len(b2b_games) > 0 else 0

print(f"Rested team: {rested_wins}-{len(b2b_games)-rested_wins} ({wr:.1f}%)")

print("\n" + "="*80)
print("COMPARISON TO NHL")
print("="*80)
print(f"NHL B2B baseline: 58.4%")
print(f"NBA B2B baseline: {wr:.1f}%")
print(f"Difference: {wr - 58.4:+.1f}%")

if wr > 55:
    print("\n✅ NBA has similar B2B advantage as NHL!")
    print("   Worth testing form-based strategy")
else:
    print("\n⚠️  NBA B2B advantage is weaker than NHL")
    print("   Strategy may not work as well")

# Save
completed.to_csv('nba_completed_games_2025.csv', index=False)
print(f"\n💾 Saved to nba_completed_games_2025.csv")
