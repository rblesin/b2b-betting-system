import pandas as pd

def last_game_date(history_df, team):
    games = history_df[(history_df["home"] == team) | (history_df["away"] == team)]
    if games.empty:
        return None
    return games.sort_values("date").iloc[-1]["date"]


def compute_rest_metrics(history_df, upcoming_df):
    rows = []
    
    # CRITICAL: Sort upcoming games by date first!
    upcoming_df = upcoming_df.sort_values("date").reset_index(drop=True)
    
    # Create a working history that we'll update as we process games
    working_history = history_df.copy()

    print("\n=== PROCESSING GAMES ===")
    for idx, g in upcoming_df.iterrows():
        game_date = g["date"]
        
        # Convert to date-only for comparison
        game_date_only = game_date.date()

        # home
        home_last = last_game_date(working_history, g["home"])
        if home_last is not None:
            home_last_date_only = home_last.date()
            home_rest = (game_date_only - home_last_date_only).days
        else:
            home_rest = None

        # away
        away_last = last_game_date(working_history, g["away"])
        if away_last is not None:
            away_last_date_only = away_last.date()
            away_rest = (game_date_only - away_last_date_only).days
        else:
            away_rest = None

        # DEBUG: Print first 5 games with rest=0
        if home_rest == 0 or away_rest == 0:
            print(f"B2B FOUND: {game_date_only} | {g['home']} (rest={home_rest}) vs {g['away']} (rest={away_rest})")

        rows.append({
            "date": game_date,
            "home": g["home"],
            "away": g["away"],
            "home_rest_days": home_rest,
            "away_rest_days": away_rest,
            "home_rest_status": "B2B" if home_rest == 0 else "Rested",
            "away_rest_status": "B2B" if away_rest == 0 else "Rested"
        })
        
        # ADD THIS GAME TO WORKING HISTORY so next games see it
        new_row = pd.DataFrame([{
            'date': g['date'],
            'home': g['home'],
            'away': g['away']
        }])
        working_history = pd.concat([working_history, new_row], ignore_index=True)

    print("========================\n")

    df = pd.DataFrame(rows)

    # rest advantage
    df["rest_advantage"] = df.apply(
        lambda r: r["home"] if r["home_rest_days"] > r["away_rest_days"]
        else (r["away"] if r["away_rest_days"] > r["home_rest_days"] else None),
        axis=1
    )

    return df