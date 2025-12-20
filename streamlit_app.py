import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="NHL B2B", page_icon="🏒", layout="wide")

from scraper import HockeyReferenceScraper
from enhanced_analyzer import EnhancedB2BAnalyzer
from betting_tracker import BettingTracker
from config import CURRENT_SEASON, CACHE_TTL, TIERS

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

completed, upcoming, standings = load_data()
tracker = BettingTracker()
analyzer = EnhancedB2BAnalyzer(completed)

# Title
st.title("🏒 NHL Back-to-Back System")

# Win Rates
st.header("Win Rates")
col1, col2, col3 = st.columns(3)

baseline = get_baseline()
summary = tracker.get_summary(sport='NHL')
our_wr = summary['win_rate'] if summary['total_bets'] > 0 else 67.9

with col1:
    st.metric("Baseline", f"{baseline:.1f}%")
    st.caption("Rested vs B2B (10yr)")
with col2:
    st.metric("Our Strategy", f"{our_wr:.1f}%")
    st.caption(f"{summary['wins']}-{summary['losses']}" if summary['total_bets'] > 0 else "67.9% (10yr avg)")
with col3:
    st.metric("Edge", f"+{our_wr - baseline:.1f}%")
    st.caption("Improvement")

# Strategy
with st.expander("📖 Strategy"):
    st.markdown("""
    **Tier S** (68.2%): Rested 4-5 wins + 3+ advantage
    **Tier A** (67.5%): Rested 4-5 wins + 2+ advantage
    
    _(Tier B removed - only 57.7% vs 58.4% baseline)_
    """)

st.divider()

# Main section - ALL B2B GAMES
st.header("All Back-to-Back Games")

all_b2b = []

for _, game in upcoming.iterrows():
    home_b2b = game.get('home_rest', 999) == 1
    away_b2b = game.get('away_rest', 999) == 1
    
    if home_b2b or away_b2b:
        rested = game['home'] if not home_b2b else game['away']
        b2b = game['away'] if not home_b2b else game['home']
        
        rec = analyzer.should_bet(
            {'home': game['home'], 'away': game['away'], 'home_b2b': home_b2b, 'away_b2b': away_b2b},
            {}, standings
        )
        
        rested_form = analyzer.team_streaks.get(rested, {}).get('last_5', '?')
        b2b_form = analyzer.team_streaks.get(b2b, {}).get('last_5', '?')
        
        if rec['should_bet']:
            status = f"✅ BET ({rec['tier']})"
            reason = TIERS[rec['tier']]['criteria']
        else:
            status = "⏭️ SKIP"
            reason = rec.get('reason', 'Does not meet criteria')
        
        all_b2b.append({
            'Date': game['date'],
            'Away': game['away'],
            'Home': game['home'],
            'B2B Team': b2b,
            'Rested': rested,
            'Rested Form': rested_form,
            'B2B Form': b2b_form,
            'Status': status,
            'Why': reason
        })

if all_b2b:
    df = pd.DataFrame(all_b2b)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    bet_count = len([x for x in all_b2b if 'BET' in x['Status']])
    st.caption(f"Showing {len(all_b2b)} B2B games ({bet_count} qualify for betting)")
else:
    st.info("No B2B games found")

st.divider()

# History
st.header("Betting History (2025-26)")

nhl_bets = [b for b in tracker.bets if b.get('sport') == 'NHL']
completed_bets = [b for b in nhl_bets if b['result'] != 'pending']

if completed_bets:
    wins = sum(1 for b in completed_bets if b['result'] == 'won')
    st.metric("Record", f"{wins}-{len(completed_bets)-wins} ({wins/len(completed_bets)*100:.1f}%)")
    
    rows = []
    for bet in reversed(completed_bets):
        rows.append({
            'Date': bet['date'],
            '': '✅' if bet['result'] == 'won' else '❌',
            'Game': f"{bet['away']} @ {bet['home']}",
            'Pick': bet['pick'],
            'Tier': bet.get('tier', '?')
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("No bets this season")
