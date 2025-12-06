# B2B Betting System - Multi-Sport Configuration

CURRENT_SEASON = "2026"  # NHL
CURRENT_NBA_SEASON = "2025"  # NBA

# THREE-TIER SYSTEM (Based on 10-year validation)
TIERS = {
    'S': {
        'name': 'Elite',
        'nhl_criteria': 'Rested 4-5 wins in L5 AND 2+ win advantage',
        'nba_criteria': 'HOME rested, 4-5 wins in L5 AND 2+ win advantage',
        'nhl_historical_wr': 69.2,
        'nba_historical_wr': 76.0,
        'nhl_sample_size': 224,
        'nba_sample_size': 263
    },
    'A': {
        'name': 'Good',
        'nhl_criteria': 'Rested 4-5 wins in L5 AND 1+ win advantage',
        'nba_criteria': 'HOME rested, 4-5 wins in L5 AND 1+ win advantage',
        'nhl_historical_wr': 68.4,
        'nba_historical_wr': 67.9,
        'nhl_sample_size': 326,
        'nba_sample_size': 109
    },
    'B': {
        'name': 'Decent',
        'nhl_criteria': 'Form advantage ≥2 (any form level)',
        'nba_criteria': 'HOME rested, form advantage ≥2 (any form level)',
        'nhl_historical_wr': 66.0,
        'nba_historical_wr': 76.0,
        'nhl_sample_size': 494,
        'nba_sample_size': 146
    }
}

# Betting thresholds
MIN_WIN_RATE = 65.0

# Kelly Criterion
KELLY_FRACTIONAL = 0.25
MAX_BET_AMOUNT = 1000  # Cap at $1,000 per bet
DEFAULT_ODDS = 2.00

# Form thresholds
GOOD_FORM_WINS = 4  # 4+ wins for Tier S/A
RECENT_FORM_GAMES = 5

# Data settings
CACHE_TTL = 3600
UPCOMING_GAMES_DAYS = 30

# Files
INITIAL_BANKROLL = 1000
TRACKER_FILE = 'betting_tracker.json'

# Sport-specific settings
SPORTS = {
    'NHL': {
        'enabled': True,
        'allow_away_bets': True,  # NHL works for both home and away
        'baseline_wr': 58.4
    },
    'NBA': {
        'enabled': True,
        'allow_away_bets': False,  # NBA only works for HOME rested
        'baseline_wr': 61.2  # Home rested only
    }
}
