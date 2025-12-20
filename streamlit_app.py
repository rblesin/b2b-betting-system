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
    return completed, upcoming, standings, scraper

@st.cache_data(ttl=86400)
def get_baseline():
    if os.path.exists('nhl_b2b_games_2015_2025.csv'):
        df = pd.read_csv('nhl_b2b_games_2015_2025.csv')
        total = len(df)
        wins = sum((df['rest_advantage'] == 'home') & df['home_win']) + sum((df['rest_advantage'] == 'away') & ~df['home_win'])
        return (wins / total * 100) if total > 0 else 58.4
    return 58.4

completed, upcoming, standings, scraper = load_data()
tracker = BettingTracker()
analyzer = EnhancedB2BAnalyzer(completed, scraper)

st.title("🏒 NHL Back-to-Back System")

# Win Rates
st.header("Win Rates")
col1, col2, col3, col4 = st.columns(4)

baseline = get_baseline()

# Calculate S+A only
nhl_bets = [b for b in tracker.bets if b.get('sport') == 'NHL' and b['result'] != 'pending']
sa_bets = [b for b in nhl_bets if b.get('tier') in ['S', 'A']]
if sa_bets:
    sa_wins = sum(1 for b in sa_bets if b['result'] == 'won')
    current_wr = sa_wins / len(sa_bets) * 100
    record = f"{sa_wins}-{len(sa_bets)-sa_wins}"
else:
    current_wr = 0
    record = "No bets yet"

historical_wr = 67.9

with col1:
    st.metric("Baseline", f"{baseline:.1f}%")
    st.caption("Any rested vs B2B")
with col2:
    st.metric("Historical", f"{historical_wr:.1f}%")
    st.caption("2-tier (10yr)")
with col3:
    st.metric("This Season", f"{current_wr:.1f}%" if current_wr > 0 else "0.0%")
    st.caption(record)
with col4:
    display_wr = current_wr if current_wr > 0 else historical_wr
    st.metric("Edge", f"+{display_wr - baseline:.1f}%")
    st.caption("vs Baseline")

with st.expander("📖 Strategy"):
    st.markdown("""
    **Tier S** (68.2%): Rested 4-5 wins + 3+ advantage
    **Tier A** (67.5%): Rested 4-5 wins + 2+ advantage
    
    **Pro Enhancements:**
    - 🥅 B2B backup goalie → Upgrades A → S
    - 🏥 Rested 2+ injuries → SKIP
    """)

st.divider()
st.header("All Back-to-Back Games")

all_b2b = []
for _, game in upcoming.iterrows():
    home_b2b = game.get('home_rest', 999) == 1
    away_b2b = game.get('away_rest', 999) == 1
    
    if home_b2b or away_b2b:
        rested = game['home'] if not home_b2b else game['away']
        b2b = game['away'] if not home_b2b else game['home']
        
        rec = analyzer.should_bet(
            {'home': game['home'], 'away': game['away'], 'home_b2b': home_b2b, 'away_b2b': away_b2b, 'date': game.get('date')},
            {}, standings
        )
        
        rested_form = analyzer.team_streaks.get(rested, {}).get('last_5', '?')
        b2b_form = analyzer.team_streaks.get(b2b, {}).get('last_5', '?')
        
        if rec['should_bet']:
            status = f"✅ BET ({rec['tier']})"
            reason = TIERS[rec['tier']]['criteria']
            if rec.get('enhancements'):
                for e in rec['enhancements']:
                    reason += f" • {e}"
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
    st.dataframe(pd.DataFrame(all_b2b), use_container_width=True, hide_index=True)
    bet_count = len([x for x in all_b2b if 'BET' in x['Status']])
    st.caption(f"{len(all_b2b)} B2B games ({bet_count} qualify)")
else:
    st.info("No B2B games found")

st.divider()
st.header("Betting History (2025-26)")

if sa_bets:
    st.metric("Record", f"{record} ({current_wr:.1f}%)")
    rows = []
    for bet in reversed(sa_bets):
        rows.append({
            'Date': bet['date'],
            '': '✅' if bet['result'] == 'won' else '❌',
            'Game': f"{bet['away']} @ {bet['home']}",
            'Pick': bet['pick'],
            'Tier': bet.get('tier', '?')
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("No S or A tier bets this season")
