# NHL B2B Multi-Season Analysis - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies
```bash
pip install pandas numpy requests beautifulsoup4 matplotlib streamlit
```

### Step 2: Run the Analysis
```bash
python run_analysis.py
```

This will:
- ✓ Scrape NHL data for seasons 2022-23, 2023-24, 2024-25
- ✓ Analyze all betting tiers across ~3,600 games
- ✓ Test optimal Kelly Criterion fractions
- ✓ Generate recommendations and config files

**Expected runtime:** 5-10 minutes (first run with scraping)

### Step 3: Review Results

The analysis creates these files:
- `multi_season_games.csv` - Complete dataset
- `recommended_config.json` - Updated tier configurations
- `analysis_summary.json` - Key findings
- `tier_details_*.json` - Detailed game-by-game results

### What You'll See

```
============================================================
STEP 2: TIER ANALYSIS
============================================================

Tier S - Elite Home
  Home rested vs B2B opponent, good form (3-5 wins in L5)
  Record: 145-32 (81.9%)
  Sample size: 177 games
  Status: ✓ PROFITABLE

Tier A - Good Away
  Away rested vs B2B opponent, good form (3-5 wins in L5)
  Record: 42-39 (51.9%)
  Sample size: 81 games
  Status: ≈ MARGINAL

...
```

## 🎯 Key Questions Answered

### Q: Is my 81.8% Tier S win rate real or lucky?
**A:** The multi-season analysis will show you the historical win rate across 150+ games. If it's 65-75%, you've been lucky. If it's 75-80%, it's validated.

### Q: Should I bet Tier A?
**A:** Your Kelly system correctly stopped at 50%. The multi-season analysis shows if this tier is viable long-term (needs 52.5%+ across 80+ games).

### Q: What Kelly fraction should I use?
**A:** The analysis tests 10%, 25%, 50%, and 100% Kelly for each tier and recommends the optimal fraction based on:
- Maximum ROI
- Acceptable drawdown risk
- Sharpe ratio (risk-adjusted return)

### Q: Are there other profitable tiers?
**A:** The analysis evaluates 7 different tier definitions:
- Tier B/C: Medium form (2 wins in L5)
- Tier D/E: Hot streaks (5 wins in L5)
- Tier F: Relative form advantage

## 📊 Understanding Your Results

### If Tier S shows 70%+ win rate across 150+ games:
✓ **VALIDATED** - Continue betting with confidence
- Use recommended Kelly fraction (likely 25%)
- Track results season-by-season
- Consider increasing bankroll allocation

### If Tier S shows 55-65% win rate:
⚠️ **PROFITABLE BUT MODERATE** - Adjust expectations
- Current season was lucky (81.8% unsustainable)
- Still profitable, just lower returns
- Use conservative Kelly (10-25%)

### If Tier S shows <55% win rate:
❌ **WARNING** - Reevaluate strategy
- Sample size may be too small
- Tier definition may need adjustment
- Current season might be anomaly

## 🔧 Customization Options

### Analyze Different Seasons
```python
from run_analysis import run_complete_analysis

results = run_complete_analysis(
    seasons=["2020", "2021", "2022", "2023", "2024"],  # 5 seasons
    force_refresh=False,
    initial_bankroll=5000.0
)
```

### Test Custom Kelly Fractions
```python
from kelly_validator import KellyValidator

validator = KellyValidator(initial_bankroll=1000.0)
results = validator.test_kelly_fractions(
    tier_games,
    win_rate=0.65,
    fractions=[0.05, 0.10, 0.15, 0.20, 0.25, 0.30]  # Fine-tuned
)
```

### Compare Single vs Multi-Season
```python
from comparison_tool import SeasonComparison

# After running analysis
comparison = SeasonComparison(single_season_data, multi_season_data)
comparison.generate_report()
```

## 🎮 Integration with Existing System

Your existing `streamlit_app.py` can load the multi-season results:

```python
import pandas as pd
import streamlit as st
from multi_season_analyzer import MultiSeasonAnalyzer

# Add a new tab
tab1, tab2, tab3, tab4, tab5, tab_multi = st.tabs([
    "Dashboard", "Strategy", "Upcoming", "Active", "History", 
    "Multi-Season"  # New tab
])

with tab_multi:
    st.header("Multi-Season Validation")
    
    # Load data
    df = pd.read_csv('multi_season_games.csv', parse_dates=['date'])
    analyzer = MultiSeasonAnalyzer(df)
    
    # Show tier performance
    results = analyzer.analyze_all_tiers()
    
    cols = st.columns(3)
    for i, (tier_key, perf) in enumerate(results.items()):
        if perf.games >= 30:
            with cols[i % 3]:
                st.metric(
                    label=perf.name,
                    value=f"{perf.win_rate:.1%}",
                    delta=f"{perf.wins}-{perf.losses}"
                )
```

## 📈 Expected Outcomes

### Conservative Estimate (Tier S at 65% win rate)
- Starting bankroll: $1,000
- Expected final: $2,500 - $3,500 (after 100 bets)
- ROI: +150% to +250%
- Time frame: 1-2 seasons

### Moderate Estimate (Tier S at 70% win rate)
- Starting bankroll: $1,000
- Expected final: $4,000 - $6,000 (after 100 bets)
- ROI: +300% to +500%
- Time frame: 1-2 seasons

### Aggressive Estimate (Tier S at 75% win rate)
- Starting bankroll: $1,000
- Expected final: $7,000 - $10,000 (after 100 bets)
- ROI: +600% to +900%
- Time frame: 1-2 seasons

**Note:** These assume 25% Kelly with max 10% bet size cap.

## 🚨 Important Reminders

1. **Past performance ≠ future results**
   - Multi-season data gives confidence, not guarantees
   - NHL changes: rule changes, team dynamics, etc.

2. **Sample size matters**
   - <30 games = ignore
   - 30-50 games = possible
   - 50-100 games = confident
   - 100+ games = robust

3. **Kelly protects you**
   - System won't bet without edge
   - Fractional Kelly reduces risk
   - Max bet cap prevents catastrophe

4. **Variance is real**
   - Even 70% win rate has losing streaks
   - Expect 3-5 game losing runs
   - Don't panic, trust the math

## 🎯 Next Actions

After reviewing your multi-season results:

**If Tier S validated (>65% win rate):**
1. Update `config.py` with historical win rate
2. Set Kelly fraction to recommended value
3. Continue current betting approach
4. Monitor season-by-season performance

**If new tiers discovered:**
1. Review tier definitions in analysis
2. Test with small bets first
3. Track separately from Tier S
4. Validate over 30+ games before full commitment

**If Tier A viable (>52.5% win rate):**
1. Add back to betting rotation
2. Use conservative Kelly (10-15%)
3. Track separately from Tier S
4. Reevaluate after 50 bets

## 📞 Troubleshooting

**"No data collected"**
- Check internet connection
- Try `force_refresh=True`
- Verify Hockey Reference is accessible

**"Tier X has 0 games"**
- Form calculation needs 5 games/team
- Early season games excluded
- Tier criteria may be too restrictive

**"Kelly recommendation is 0%"**
- Win rate <50% = no edge
- System correctly refuses to bet
- Consider revising tier definition

**Results differ from single season**
- Expected! Single season is small sample
- Multi-season is more reliable
- Adjust expectations accordingly

---

## 🎊 Ready to Run!

```bash
python run_analysis.py
```

Watch as your single-season findings get validated (or challenged) by 3+ years of data. The truth is in the numbers! 📊🏒
