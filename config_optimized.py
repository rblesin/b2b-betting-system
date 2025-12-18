# B2B Betting System - NHL Configuration (OPTIMIZED VERSION)
# This version uses stricter criteria found through 10-year optimization
# Trade-off: Fewer bets (~50% less volume) but higher win rates (66-68%)

CURRENT_SEASON = "2026"  # NHL 2025-26

# THREE-TIER SYSTEM (Optimized through 10-year backtest)
# These criteria produce 66.1% average WR vs 64.5% with looser criteria
TIERS = {
    'S': {
        'name': 'Elite',
        'criteria': 'Rested 4-5 wins in L5 AND 3+ win advantage',  # Was 2+
        'historical_wr': 68.2,  # Optimized from 68.1%
        'sample_size': 129  # Reduced from 282 (more selective)
    },
    'A': {
        'name': 'Good',
        'criteria': 'Rested 4-5 wins in L5 AND 2+ win advantage',  # Was 1+
        'historical_wr': 68.0,  # Improved from 61.1%
        'sample_size': 153  # Reduced from 126 (slightly more)
    },
    'B': {
        'name': 'Decent',
        'criteria': 'Form advantage ≥3 (any form level)',  # Was ≥2
        'historical_wr': 62.1,  # Similar to 61.6%
        'sample_size': 29  # Greatly reduced from 198 (very selective)
    }
}

# Betting thresholds
MIN_WIN_RATE = 65.0

# Kelly Criterion
KELLY_FRACTIONAL = 0.25
MAX_BET_AMOUNT = 1000  # Cap at $1,000 per bet
DEFAULT_ODDS = 2.00

# Form thresholds (OPTIMIZED)
GOOD_FORM_WINS = 4  # Keep at 4 (4-5 wins in L5)
RECENT_FORM_GAMES = 5

# OPTIMIZED TIER CRITERIA (use these in enhanced_analyzer.py)
TIER_S_FORM_ADV = 3  # Increased from 2
TIER_A_FORM_ADV = 2  # Increased from 1
TIER_B_FORM_ADV = 3  # Increased from 2

# Data settings
CACHE_TTL = 3600
UPCOMING_GAMES_DAYS = 30

# Files
INITIAL_BANKROLL = 1000
TRACKER_FILE = 'betting_tracker.json'

# NHL settings
ALLOW_AWAY_BETS = True  # NHL works for both home and away
BASELINE_WR = 58.4  # Rested vs B2B baseline

# OPTIMIZATION NOTES:
# - This config trades volume for quality
# - Expect ~50% fewer bets but 1.5-2% higher win rate
# - Better for conservative bankroll management
# - All three tiers now have 62%+ win rates
# - Tier S and A are now virtually identical in performance (68%)
