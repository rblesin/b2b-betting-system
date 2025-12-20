# NHL Back-to-Back Betting System

Exploit fatigue in NHL back-to-back games.

## Performance

**Two-Tier Strategy: 67.9% WR**
- Baseline: 58.4%
- Edge: +9.5%
- ~25 bets/year

## Strategy

**Tier S (Elite)** - 68.2% WR
- Rested: 4-5 wins in L5
- Advantage: +3 or more

**Tier A (Good)** - 67.5% WR
- Rested: 4-5 wins in L5
- Advantage: +2 or more

_(Tier B removed - only 57.7% barely above 58.4% baseline)_

## Files

- `streamlit_app.py` - Web interface
- `config.py` - 2-tier settings
- `enhanced_analyzer.py` - Logic
- `betting_tracker.py` - Tracking
- `scraper.py` - Data scraper
- `betting_tracker.json` - Current bets
- `*.csv` - Historical data (10 years)

## Deploy

```bash
git add .
git commit -m "Two-tier strategy: 67.9% WR (removed Tier B)"
git push origin main
```

Live: https://b2b-betting.streamlit.app

