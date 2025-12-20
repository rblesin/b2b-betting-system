# NHL B2B Betting System - Configuration
# TWO-TIER STRATEGY: 67.9% WR

CURRENT_SEASON = "2026"  # NHL 2025-26

# TWO-TIER SYSTEM (Tier B removed - only 57.7% WR)
TIERS = {
    'S': {
        'name': 'Elite',
        'criteria': 'Rested 4-5 wins + 3+ advantage',
        'historical_wr': 68.2,
        'sample_size': 129
    },
    'A': {
        'name': 'Good',
        'criteria': 'Rested 4-5 wins + 2+ advantage',
        'historical_wr': 67.5,
        'sample_size': 151
    }
}

# Form thresholds
GOOD_FORM_WINS = 4  # 4-5 wins in last 5 games
RECENT_FORM_GAMES = 5

# Data settings
CACHE_TTL = 3600
UPCOMING_GAMES_DAYS = 30

# Files
INITIAL_BANKROLL = 1000
TRACKER_FILE = 'betting_tracker.json'

# NHL settings
BASELINE_WR = 58.4  # Rested vs B2B baseline (no filters)
