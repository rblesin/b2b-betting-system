from src.api.local_nhl_api import get_history, get_upcoming
from src.features.rest_metrics import compute_rest_metrics
import pandas as pd

def evaluate_upcoming_games(start_date, days_forward):
    # The JSON is UTC, so normalize everything to UTC midnight
    start_date = pd.Timestamp(start_date).tz_convert("UTC").normalize()

    # end-date = start_date + days
    end_date = start_date + pd.Timedelta(days=days_forward)

    print(f"Loading upcoming games from {start_date.date()} to {end_date.date()} ...")

    # load historical games before start_date
    history = get_history(start_date)
    print(f"Loaded {len(history)} historical games")

    # load all games in the window
    upcoming = get_upcoming(start_date, days_forward)
    print(f"Loaded {len(upcoming)} upcoming games")
    print(f"Upcoming games date range: {upcoming['date'].min()} to {upcoming['date'].max()}")

    df = compute_rest_metrics(history, upcoming)
    print(f"Computed rest metrics for {len(df)} games")

    # Filter ONLY TRUE B2B games (rest = 0)
    df_b2b = df[(df["home_rest_days"] == 0) | (df["away_rest_days"] == 0)].copy()
    print(f"Found {len(df_b2b)} B2B games")

    # Sort by date for clarity
    df_b2b = df_b2b.sort_values("date")

    return df_b2b