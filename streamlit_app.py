import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="NHL B2B System", page_icon="🏒", layout="wide")

from scraper import HockeyReferenceScraper
from enhanced_analyzer import EnhancedB2BAnalyzer
from betting_tracker import BettingTracker
from config import CURRENT_SEASON, CACHE_TTL, TIERS

# Load data
@st.cache_data(ttl=CACHE_TTL)
def load_data():
    scraper = HockeyReferenceScraper(season=CURRENT_SEASON)
    completed, upcoming = scraper.scrape_all_games()
    standings = scraper.scrape_standings()
    return completed, upcoming, standings

@st.cache_data(ttl=86400)
def get_baseline():
    if os.path.exists('nhl_b2b_games_2015_2025.csv'):
        df = pd.read_csv('nhl_b2b_games_2015_2025.csv')
        total = len(df)
        wins = sum((df['rest_advantage'] == 'home') & df['home_win']) + sum((df['rest_advantage'] == 'away') & ~df['home_win'])
        return (wins / total * 100) if total > 0 else 58.4
    return 58.4

nhl_completed, nhl_upcoming, nhl_standings = load_data()
tracker = BettingTracker()
analyzer = EnhancedB2BAnalyzer(nhl_completed)

# Title
st.title("🏒 NHL Back-to-Back System")

# Win Rates
st.header("Win Rates")
col1, col2, col3 = st.columns(3)

baseline = get_baseline()
summary = tracker.get_summary(sport='NHL')
our_wr = summary['win_rate'] if summary['total_bets'] > 0 else 64.5

with col1:
    st.metric("Baseline (Rested vs B2B)", f"{baseline:.1f}%")
with col2:
    st.metric("Our Strategy", f"{our_wr:.1f}%")
with col3:
    st.metric("Edge", f"+{our_wr - baseline:.1f}%")

# Historical Performance
st.subheader("Strategy Details (10-Year Average)")
st.markdown(f"""
- **Tier S**: 68.1% WR - Rested 4-5 wins + 2+ advantage
- **Tier A**: 61.1% WR - Rested 4-5 wins + 1+ advantage
- **Tier B**: 61.6% WR - Rested any form + 2+ advantage
- **Overall**: 64.5% WR across 606 games
""")

st.divider()

# Tabs
tab1, tab2 = st.tabs(["🎯 Games to Bet", "📜 History"])

with tab1:
    st.subheader("Upcoming Games That Meet Criteria")
    
    bets = []
    for _, game in nhl_upcoming.iterrows():
        home_b2b = game.get('home_rest', 999) == 1
        away_b2b = game.get('away_rest', 999) == 1
        
        if home_b2b or away_b2b:
            rec = analyzer.should_bet(
                {'home': game['home'], 'away': game['away'], 'home_b2b': home_b2b, 'away_b2b': away_b2b},
                {}, nhl_standings
            )
            
            if rec['should_bet']:
                pick = rec['pick']
                b2b = game['away'] if pick == game['home'] else game['home']
                rested_form = analyzer.team_streaks.get(pick, {}).get('last_5', '?')
                b2b_form = analyzer.team_streaks.get(b2b, {}).get('last_5', '?')
                
                bets.append({
                    'Date': game['date'],
                    'Game': f"{game['away']} @ {game['home']}",
                    'Pick': pick,
                    'Tier': rec['tier'],
                    'Pick Form': rested_form,
                    'B2B Form': b2b_form,
                    'Advantage': f"+{rec.get('form_advantage', 0)}"
                })
    
    if bets:
        st.success(f"✅ {len(bets)} game(s) meet criteria")
        st.dataframe(pd.DataFrame(bets), use_container_width=True, hide_index=True)
    else:
        st.info("No games meet criteria right now")

with tab2:
    st.subheader("2025-26 Season Bets")
    
    nhl_bets = [b for b in tracker.bets if b.get('sport') == 'NHL']
    completed = [b for b in nhl_bets if b['result'] != 'pending']
    
    if completed:
        wins = sum(1 for b in completed if b['result'] == 'won')
        st.metric("Record", f"{wins}-{len(completed)-wins} ({wins/len(completed)*100:.1f}%)")
        
        rows = []
        for bet in reversed(completed):
            rows.append({
                'Date': bet['date'],
                '': '✅' if bet['result'] == 'won' else '❌',
                'Game': f"{bet['away']} @ {bet['home']}",
                'Pick': bet['pick'],
                'Tier': bet.get('tier', '?')
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No bets this season yet")

st.divider()
st.caption("🏒 Simple B2B System")
