# B2B Betting System - NHL Configuration

CURRENT_SEASON = "2026"  # NHL 2025-26

# THREE-TIER SYSTEM (Based on 10-year validation)
TIERS = {
    'S': {
        'name': 'Elite',
        'criteria': 'Rested 4-5 wins in L5 AND 2+ win advantage',
        'historical_wr': 69.2,
        'sample_size': 224
    },
    'A': {
        'name': 'Good',
        'criteria': 'Rested 4-5 wins in L5 AND 1+ win advantage',
        'historical_wr': 68.4,
        'sample_size': 326
    },
    'B': {
        'name': 'Decent',
        'criteria': 'Form advantage ≥2 (any form level)',
        'historical_wr': 66.0,
        'sample_size': 494
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

# NHL settings
ALLOW_AWAY_BETS = True  # NHL works for both home and away
BASELINE_WR = 58.4  # Rested vs B2B baseline
