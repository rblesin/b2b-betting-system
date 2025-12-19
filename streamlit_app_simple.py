import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="NHL B2B System", page_icon="🏒", layout="wide")

from scraper import HockeyReferenceScraper
from enhanced_analyzer import EnhancedB2BAnalyzer
from betting_tracker import BettingTracker
from config import *

# Load data
@st.cache_data(ttl=CACHE_TTL)
def load_nhl_data():
    scraper = HockeyReferenceScraper(season=CURRENT_SEASON)
    completed_df, upcoming_df = scraper.scrape_all_games()
    standings = scraper.scrape_standings()
    return completed_df, upcoming_df, standings

@st.cache_data(ttl=86400)
def load_historical_stats():
    """Load historical B2B statistics"""
    if os.path.exists('nhl_b2b_games_2015_2025.csv'):
        b2b_df = pd.read_csv('nhl_b2b_games_2015_2025.csv')
        
        # Calculate baseline (all B2B games - rested team wins)
        total_games = len(b2b_df)
        
        # Count wins for rested team
        rested_wins = 0
        for _, game in b2b_df.iterrows():
            if game['rest_advantage'] == 'home' and game['home_win']:
                rested_wins += 1
            elif game['rest_advantage'] == 'away' and not game['home_win']:
                rested_wins += 1
        
        baseline_wr = (rested_wins / total_games * 100) if total_games > 0 else 0
        
        return {
            'baseline_wr': baseline_wr,
            'total_games': total_games,
            'rested_wins': rested_wins
        }
    return None

# Load data
with st.spinner("Loading..."):
    nhl_completed, nhl_upcoming, nhl_standings = load_nhl_data()
    hist_stats = load_historical_stats()

# Initialize
tracker = BettingTracker()
nhl_enhanced = EnhancedB2BAnalyzer(nhl_completed)

# Header
st.title("🏒 NHL Back-to-Back Betting System")

# Main Performance Section
st.header("📊 Win Rate Comparison")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Historical Baseline")
    if hist_stats:
        st.metric("Rested vs B2B", f"{hist_stats['baseline_wr']:.1f}%")
        st.caption(f"{hist_stats['rested_wins']:,} wins in {hist_stats['total_games']:,} games")
    else:
        st.metric("Rested vs B2B", "58.4%")
        st.caption("10-year average")

with col2:
    st.subheader("Our Strategy")
    summary = tracker.get_summary(sport='NHL')
    if summary['total_bets'] > 0:
        st.metric("With Form Filters", f"{summary['win_rate']:.1f}%")
        st.caption(f"{summary['wins']}-{summary['losses']} this season")
    else:
        st.metric("With Form Filters", "64.5%")
        st.caption("10-year average")

with col3:
    st.subheader("Improvement")
    if summary['total_bets'] > 0 and hist_stats:
        improvement = summary['win_rate'] - hist_stats['baseline_wr']
        st.metric("Edge Over Baseline", f"+{improvement:.1f}%")
        st.caption("Current season")
    else:
        st.metric("Edge Over Baseline", "+6.1%")
        st.caption("Historical average")

st.divider()

# Strategy explanation
with st.expander("📖 How the Strategy Works"):
    st.markdown("""
    **The Edge**: Teams playing back-to-back games (2nd game in consecutive nights) are fatigued.
    
    **Our Filters**:
    - **Tier S (Elite)**: Rested team with 4-5 wins in last 5 games + 2+ win advantage
    - **Tier A (Good)**: Rested team with 4-5 wins in last 5 games + 1+ win advantage  
    - **Tier B (Decent)**: Any rested team with 2+ win advantage
    
    **Historical Performance (10 years)**:
    - Tier S: 68.1% win rate
    - Tier A: 61.1% win rate
    - Tier B: 61.6% win rate
    """)

st.divider()

# Tabs
tab1, tab2, tab3 = st.tabs([
    "🎯 Upcoming Games",
    "📜 Betting History", 
    "❓ Why Didn't We Bet?"
])

with tab1:
    st.subheader("Qualifying Bets - Next 30 Days")
    
    if len(nhl_upcoming) == 0:
        st.info("No games in next 30 days")
    else:
        recommendations = []
        
        for _, game in nhl_upcoming.iterrows():
            home_b2b = game.get('home_rest', 999) == 1
            away_b2b = game.get('away_rest', 999) == 1
            
            if home_b2b or away_b2b:
                game_data = {
                    'home': game['home'],
                    'away': game['away'],
                    'home_b2b': home_b2b,
                    'away_b2b': away_b2b
                }
                
                rec = nhl_enhanced.should_bet(game_data, {}, nhl_standings)
                
                if rec['should_bet']:
                    rested = rec['pick']
                    b2b_team = game['away'] if rested == game['home'] else game['home']
                    
                    rested_form = nhl_enhanced.team_streaks.get(rested, {})
                    b2b_form = nhl_enhanced.team_streaks.get(b2b_team, {})
                    
                    recommendations.append({
                        'Date': game['date'],
                        'Game': f"{game['away']} @ {game['home']}",
                        'Pick': f"✅ {rested}",
                        'Tier': rec['tier'],
                        'Rested Form': rested_form.get('last_5', '?'),
                        'B2B Form': b2b_form.get('last_5', '?'),
                        'Form Adv': f"+{rec.get('form_advantage', 0)}",
                        'Why': TIERS[rec['tier']]['criteria']
                    })
        
        if recommendations:
            st.success(f"✅ Found {len(recommendations)} qualifying bet(s)")
            rec_df = pd.DataFrame(recommendations)
            st.dataframe(rec_df, use_container_width=True, hide_index=True)
        else:
            st.info("No games meet criteria in next 30 days")

with tab2:
    st.subheader("2025-26 Season Betting History")
    
    # Get all NHL bets
    nhl_bets = [b for b in tracker.bets if b.get('sport') == 'NHL']
    
    if nhl_bets:
        # Summary
        completed = [b for b in nhl_bets if b['result'] != 'pending']
        if completed:
            wins = len([b for b in completed if b['result'] == 'won'])
            losses = len(completed) - wins
            win_rate = (wins / len(completed) * 100)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Record", f"{wins}-{losses}")
            with col2:
                st.metric("Win Rate", f"{win_rate:.1f}%")
            with col3:
                st.metric("Total Bets", len(completed))
        
        st.divider()
        
        # Bet list
        bet_rows = []
        for bet in reversed(nhl_bets):  # Most recent first
            result_emoji = "✅" if bet['result'] == 'won' else "❌" if bet['result'] == 'lost' else "⏳"
            
            bet_rows.append({
                'Date': bet['date'],
                '': result_emoji,
                'Matchup': f"{bet['away']} @ {bet['home']}",
                'Pick': bet['pick'],
                'Tier': bet.get('tier', '?'),
                'Form Adv': f"+{bet.get('form_advantage', '?')}"
            })
        
        st.dataframe(pd.DataFrame(bet_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No bets placed this season yet")

with tab3:
    st.subheader("All B2B Games - Why Did/Didn't We Bet?")
    
    st.markdown("""
    This shows **all** back-to-back situations and whether they met our criteria.
    """)
    
    cutoff_date = datetime.now().date() + timedelta(days=30)
    nhl_filtered = nhl_upcoming[nhl_upcoming['date'] <= cutoff_date].sort_values('date')
    
    game_rows = []
    
    for _, game in nhl_filtered.iterrows():
        home_b2b = game.get('home_rest', 999) == 1
        away_b2b = game.get('away_rest', 999) == 1
        
        if home_b2b or away_b2b:
            rested_team = game['home'] if not home_b2b else game['away']
            b2b_team = game['away'] if not home_b2b else game['home']
            
            rested_form = nhl_enhanced.team_streaks.get(rested_team, {})
            b2b_form = nhl_enhanced.team_streaks.get(b2b_team, {})
            
            game_data = {
                'home': game['home'],
                'away': game['away'],
                'home_b2b': home_b2b,
                'away_b2b': away_b2b
            }
            
            rec = nhl_enhanced.should_bet(game_data, {}, nhl_standings)
            
            if rec['should_bet']:
                verdict = f"✅ BET ({rec['tier']})"
                why = TIERS[rec['tier']]['criteria']
            else:
                verdict = "⏭️ Skip"
                why = rec.get('reason', 'Does not meet criteria')
            
            game_rows.append({
                'Date': game['date'],
                'Away': game['away'],
                'Home': game['home'],
                'B2B Team': b2b_team,
                'Rested Team': rested_team,
                'Rested Form': rested_form.get('last_5', '?'),
                'B2B Form': b2b_form.get('last_5', '?'),
                'Decision': verdict,
                'Reason': why
            })
    
    if game_rows:
        # Add search
        search = st.text_input("🔍 Search for a specific team", "")
        
        df = pd.DataFrame(game_rows)
        
        if search:
            mask = df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
            df = df[mask]
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.caption(f"Showing {len(df)} B2B games")
    else:
        st.info("No B2B games in next 30 days")

st.divider()
st.caption("🏒 NHL B2B System | Simple & Focused")
