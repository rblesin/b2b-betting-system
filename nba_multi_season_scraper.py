import requests
import pandas as pd
from datetime import datetime, timedelta
import time

print("="*80)
print("NBA MULTI-SEASON SCRAPER (2015-2025)")
print("="*80)

base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"

all_games = []

# Scrape 10 seasons: 2015-16 through 2024-25
seasons = [
    (2015, datetime(2015, 10, 1), datetime(2016, 6, 30)),
    (2016, datetime(2016, 10, 1), datetime(2017, 6, 30)),
    (2017, datetime(2017, 10, 1), datetime(2018, 6, 30)),
    (2018, datetime(2018, 10, 1), datetime(2019, 6, 30)),
    (2019, datetime(2019, 10, 1), datetime(2020, 10, 30)),  # COVID season
    (2020, datetime(2020, 12, 1), datetime(2021, 7, 31)),   # COVID delayed
    (2021, datetime(2021, 10, 1), datetime(2022, 6, 30)),
    (2022, datetime(2022, 10, 1), datetime(2023, 6, 30)),
    (2023, datetime(2023, 10, 1), datetime(2024, 6, 30)),
    (2024, datetime(2024, 10, 1), datetime(2024, 12, 4)),   # Current season
]

for season_year, start_date, end_date in seasons:
    print(f"\n{'='*80}")
    print(f"SEASON {season_year}-{season_year+1}")
    print(f"{'='*80}")
    
    current_date = start_date
    season_games = 0
    
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
                    competitors = competition['competitors']
                    
                    home_team = next((c for c in competitors if c['homeAway'] == 'home'), None)
                    away_team = next((c for c in competitors if c['homeAway'] == 'away'), None)
                    
                    if not home_team or not away_team:
                        continue
                    
                    # Only completed games
                    if not competition['status']['type']['completed']:
                        continue
                    
                    game_date = datetime.strptime(event['date'], '%Y-%m-%dT%H:%M%SZ').date()
                    
                    game = {
                        'season': f"{season_year}-{str(season_year+1)[-2:]}",
                        'date': game_date,
                        'away': away_team['team']['displayName'],
                        'home': home_team['team']['displayName'],
                        'away_points': int(away_team['score']),
                        'home_points': int(home_team['score']),
                        'home_win': int(home_team['score']) > int(away_team['score'])
                    }
                    
                    all_games.append(game)
                    season_games += 1
        
        except Exception as e:
            pass
        
        current_date += timedelta(days=1)
        
        # Progress update every 30 days
        if current_date.day == 1:
            print(f"  {current_date.strftime('%B %Y')}: {season_games} games")
        
        # Be polite to ESPN
        if current_date.day % 7 == 0:
            time.sleep(0.5)
    
    print(f"  ✅ Season complete: {season_games} games")
    time.sleep(2)  # Longer pause between seasons

print(f"\n{'='*80}")
print(f"SCRAPING COMPLETE")
print(f"{'='*80}")
print(f"Total games scraped: {len(all_games)}")

# Convert to DataFrame
df = pd.DataFrame(all_games)

# Calculate rest days
print("\n🔄 Calculating rest days...")
df = df.sort_values('date').reset_index(drop=True)
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
df.to_csv('nba_completed_games_2015_2025.csv', index=False)

print(f"\n✅ Saved to: nba_completed_games_2015_2025.csv")

# Summary
print(f"\n{'='*80}")
print("SUMMARY BY SEASON")
print(f"{'='*80}")

for season in df['season'].unique():
    season_df = df[df['season'] == season]
    b2b_count = len(season_df[
        ((season_df['home_b2b'] == True) & (season_df['away_b2b'] == False)) |
        ((season_df['home_b2b'] == False) & (season_df['away_b2b'] == True))
    ])
    print(f"{season}: {len(season_df)} games, {b2b_count} B2B situations ({b2b_count/len(season_df)*100:.1f}%)")

print("\n🏀 Ready for 10-year analysis!")
