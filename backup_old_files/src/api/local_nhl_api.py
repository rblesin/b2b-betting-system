import pandas as pd
import os

DATA_FILE = "data/raw/nhl_schedule_2025_26.json"

def load_full_schedule():
    df = pd.read_json(DATA_FILE)
    df["date"] = pd.to_datetime(df["DateUtc"], utc=True)
    return df.rename(columns={"HomeTeam": "home", "AwayTeam": "away"})[["date", "home", "away"]]


def get_history(start_date):
    df = load_full_schedule()
    return df[df["date"] < start_date].copy()


def get_upcoming(start_date, days_forward):
    df = load_full_schedule()
    end_date = start_date + pd.Timedelta(days=days_forward)
    return df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()
