# Installation Instructions

## Phase 1 Updates - Immediate Fixes ✅

### Step 1: Backup Your Current Files
```bash
cd nhl_rest_project
mkdir backup_old_files
cp *.py requirements.txt backup_old_files/
```

### Step 2: Replace Files
Download these updated files and replace your current ones:
- ✅ `streamlit_app.py` (updated)
- ✅ `analyzer.py` (cleaned)
- ✅ `enhanced_analyzer.py` (refactored)
- ✅ `betting_tracker.py` (cleaned)
- ✅ `requirements.txt` (updated)
- ✅ `scraper.py` (no changes, but included)
- ⭐ `config.py` (NEW FILE - add this)

### Step 3: Update Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Test the App
```bash
streamlit run streamlit_app.py
```

### Step 5: Clean Up Old Files (Optional)
After confirming everything works, you can delete:
```bash
rm analyze_with_tracking.py
rm analyze_current_season.py
rm analyze_upcoming.py
rm show_bets.py
rm main.py
rm flask_server.py
rm dashboard.html
rm upcoming_b2b_analysis.py
# Only if redundant:
# rm full_schedule_scraper.py
```

---

## What Changed?

### Fixed Issues:
1. ✅ Removed print statements causing emoji encoding issues
2. ✅ Refactored 200+ line `should_bet()` function into smaller, manageable pieces
3. ✅ Extracted all magic numbers to `config.py`
4. ✅ Fixed season year (2026 → 2025)
5. ✅ Fixed inconsistent Kelly sizing
6. ✅ Added streamlit to requirements.txt

### New File: `config.py`
This is where you can now easily tune your betting strategy:
- Base edge percentages
- Edge adjustments
- Betting thresholds
- Kelly Criterion settings
- Season year
- And more!

---

## Configuration

Edit `config.py` to tune your strategy:

```python
# Example: Make betting more conservative
MIN_EDGE_HOME_SCENARIO = 65  # Increase from 60
MIN_EDGE_AWAY_SCENARIO = 60  # Increase from 55

# Example: Change Kelly sizing
KELLY_FRACTIONAL = 0.20  # More conservative (was 0.25)
MAX_BET_PCT = 0.03       # Lower max bet (was 0.05)
```

---

## Troubleshooting

### Import Error: No module named 'config'
Make sure `config.py` is in the same directory as the other files.

### Season Data Not Loading
Check that `CURRENT_SEASON = "2025"` in `config.py` matches the current NHL season.

### Betting Tracker JSON Error
Your existing `betting_tracker.json` will work fine - no changes needed to data format.

---

## Next Steps

After confirming Phase 1 works:
1. **Phase 2: Layout Improvements** - Better UI, charts, visualizations
2. **Phase 3: Strategy Improvements** - Tune parameters, add features
3. **Phase 4: Code Cleanup** - Final polish

---

## Questions?
Check `CHANGES.md` for detailed explanations of all changes.
