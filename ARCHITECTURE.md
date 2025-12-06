# NHL B2B System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NHL B2B BETTING SYSTEM v2.0                         │
│                    Multi-Season Validation & Optimization                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA COLLECTION                                 │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
    │ Hockey Reference │      │ Hockey Reference │      │ Hockey Reference │
    │   2022-23 Games  │      │   2023-24 Games  │      │   2024-25 Games  │
    │   (~1,230 games) │      │   (~1,312 games) │      │   (~1,070 games) │
    └────────┬─────────┘      └────────┬─────────┘      └────────┬─────────┘
             │                         │                         │
             └─────────────────────────┴─────────────────────────┘
                                       │
                                       ▼
                          ┌────────────────────────┐
                          │ MultiSeasonScraper     │
                          │  - Fetch game data     │
                          │  - Calculate B2B       │
                          │  - Calculate form      │
                          │  - Cache results (1hr) │
                          └───────────┬────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │   multi_season_games   │
                          │         .csv           │
                          │    (~3,600 games)      │
                          └───────────┬────────────┘
                                      │
                                      │
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TIER VALIDATION                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │ MultiSeasonAnalyzer    │
                          │  - Define tiers        │
                          │  - Calculate win rates │
                          │  - Filter by criteria  │
                          │  - Compare home/away   │
                          └───────────┬────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
         ┌─────────────────────┐           ┌─────────────────────┐
         │   Tier Performance  │           │  Tier Definitions   │
         │   - Win rates       │           │  - S: Home/Good     │
         │   - Sample sizes    │           │  - A: Away/Good     │
         │   - Confidence      │           │  - B/C: Medium      │
         │   - Profitable?     │           │  - D/E: Hot Streak  │
         └──────────┬──────────┘           │  - F: Form Diff     │
                    │                      └─────────────────────┘
                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           KELLY OPTIMIZATION                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  For each viable    │
         │  tier (≥30 games,   │
         │  ≥52.5% win rate)   │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │   KellyValidator    │
         │  - Test fractions   │
         │    (10%, 25%, 50%)  │
         │  - Simulate bets    │
         │  - Calculate ROI    │
         │  - Max drawdown     │
         │  - Sharpe ratio     │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │ Optimal Kelly by    │
         │ Tier:               │
         │  - Tier S: 25%      │
         │  - Tier A: 15%      │
         │  - Tier D: 20%      │
         │  - etc...           │
         └──────────┬──────────┘
                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RESULTS & CONFIG                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┬───────────────┐
        │           │           │               │
        ▼           ▼           ▼               ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ analysis │ │recommend │ │  tier    │ │ comparison   │
│ summary  │ │  config  │ │ details  │ │   report     │
│  .json   │ │  .json   │ │  .json   │ │    .txt      │
└──────────┘ └──────────┘ └──────────┘ └──────────────┘
     │            │            │               │
     └────────────┴────────────┴───────────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │   Updated Betting       │
         │   Strategy              │
         │   - Validated tiers     │
         │   - Optimal Kelly       │
         │   - Confidence levels   │
         │   - Risk metrics        │
         └─────────────┬───────────┘
                       │
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INTEGRATION & DEPLOYMENT                              │
└─────────────────────────────────────────────────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │   Existing System       │
         │   - betting_tracker.py  │
         │   - streamlit_app.py    │
         │   - config.py (updated) │
         └─────────────┬───────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │   Live Betting with     │
         │   Multi-Season          │
         │   Validated Strategy    │
         └─────────────────────────┘
```

## Data Flow Summary

1. **Scrape** → Fetch 3+ seasons of NHL data (~3,600 games)
2. **Calculate** → Add B2B indicators and team form for each game
3. **Analyze** → Test 7 tier definitions across all historical games
4. **Validate** → Identify tiers with >30 games and >52.5% win rate
5. **Optimize** → Find optimal Kelly fraction for each viable tier
6. **Deploy** → Update config and integrate with existing system

## File Dependencies

```
run_analysis.py  (main orchestrator)
    ├── multi_season_scraper.py
    │   └── Outputs: multi_season_games.csv
    │
    ├── multi_season_analyzer.py
    │   ├── Inputs: multi_season_games.csv
    │   └── Outputs: analysis_summary.json
    │                recommended_config.json
    │                tier_details_*.json
    │
    └── kelly_validator.py
        ├── Inputs: tier game data from analyzer
        └── Outputs: Kelly recommendations (in config)

comparison_tool.py  (optional validation)
    ├── Inputs: Single season results
    │           Multi-season results
    └── Outputs: comparison_report.txt
```

## Module Interactions

```
┌──────────────────────────────────────────────────────────────┐
│                     run_analysis.py                          │
│                                                              │
│  1. Initialize scraper → get data                           │
│  2. Initialize analyzer → validate tiers                    │
│  3. For each profitable tier:                               │
│     - Initialize validator                                  │
│     - Test Kelly fractions                                  │
│     - Record recommendations                                │
│  4. Generate final config                                   │
│  5. Export all results                                      │
└──────────────────────────────────────────────────────────────┘
```

## Integration Points with Existing System

```
┌─────────────────────────────────────────────────────────────┐
│                    EXISTING SYSTEM                          │
├─────────────────────────────────────────────────────────────┤
│ scraper.py          → Keep for real-time upcoming games     │
│ analyzer.py         → Keep for single-season analysis       │
│ enhanced_analyzer.py → UPDATE tier definitions from config  │
│ betting_tracker.py  → UPDATE with new Kelly values          │
│ config.py           → UPDATE with multi-season findings     │
│ streamlit_app.py    → ADD multi-season validation tab       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    NEW COMPONENTS                           │
├─────────────────────────────────────────────────────────────┤
│ multi_season_scraper.py   → Historical data collection      │
│ multi_season_analyzer.py  → Tier validation                 │
│ kelly_validator.py        → Bet sizing optimization         │
│ run_analysis.py          → Orchestration                    │
│ comparison_tool.py        → Before/after analysis           │
└─────────────────────────────────────────────────────────────┘
```

## Workflow Timeline

```
Day 1: Setup & Initial Run
├─ Install dependencies (5 min)
├─ Run first analysis (10 min scraping + 5 min analysis)
└─ Review results (30-60 min)

Day 2: Integration
├─ Update config.py with findings (15 min)
├─ Add multi-season tab to Streamlit (30 min)
├─ Test with paper trades (ongoing)
└─ Compare with single-season results (15 min)

Week 1: Monitor
├─ Track new tier performance
├─ Verify Kelly sizing
└─ Build confidence in strategy

Month 1: Optimize
├─ Adjust tier definitions if needed
├─ Fine-tune Kelly fractions
└─ Expand to more tiers

Season End: Re-validate
└─ Re-run analysis with new season data
```

## Key Success Metrics

```
Input Metrics (Data Quality)
├─ Total games: ~3,600+
├─ Seasons analyzed: 3+
├─ B2B matchups: ~500+
└─ Games with form data: ~3,400+

Process Metrics (Analysis)
├─ Tiers evaluated: 7
├─ Tiers with ≥30 games: 3-5
├─ Profitable tiers found: 2-4
└─ Kelly fractions tested: 4-5 per tier

Output Metrics (Validation)
├─ Tier S win rate: 65-75% (vs 81.8% single season)
├─ Sample size: 150-200 games (vs 22 single season)
├─ Confidence: HIGH (vs LOW single season)
└─ Expected ROI: 100-200% (vs 255% single season)
```

---

**System Status:** ✓ Ready for Production

**Next Action:** `python run_analysis.py`
