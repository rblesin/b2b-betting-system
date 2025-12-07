import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="B2B Betting System", page_icon="🎯", layout="wide")

# Auto-download NBA data if missing (before other imports)
if not os.path.exists('nba_completed_games_2025.csv'):
    with st.spinner("Downloading current NBA season data..."):
        import scrape_current_nba
        scrape_current_nba.scrape_and_save()

from scraper import HockeyReferenceScraper
from nba_scraper import NBAESPNScraper
from analyzer import B2BAnalyzer
from enhanced_analyzer import EnhancedB2BAnalyzer
from nba_analyzer import NBAB2BAnalyzer
from betting_tracker import BettingTracker
from config import *

# Initialize
@st.cache_data(ttl=CACHE_TTL)
def load_nhl_data():
    scraper = HockeyReferenceScraper(season=CURRENT_SEASON)
    completed_df, upcoming_df = scraper.scrape_all_games()
    standings = scraper.scrape_standings()
    return completed_df, upcoming_df, standings

@st.cache_data(ttl=CACHE_TTL)
def load_nba_data():
    nba_df = pd.read_csv('nba_completed_games_2025.csv')
    nba_df['date'] = pd.to_datetime(nba_df['date']).dt.date
    
    # Load upcoming games
    scraper = NBAESPNScraper()
    nba_upcoming = scraper.scrape_upcoming_games(days=30)
    nba_standings = scraper.scrape_standings()
    
    return nba_df, nba_upcoming, nba_standings

# Load data
with st.spinner("Loading data..."):
    nhl_completed, nhl_upcoming, nhl_standings = load_nhl_data()
    nba_completed, nba_upcoming, nba_standings = load_nba_data()

# Initialize
tracker = BettingTracker()
nhl_analyzer = B2BAnalyzer(nhl_completed)
nhl_enhanced = EnhancedB2BAnalyzer(nhl_completed)
nba_enhanced = NBAB2BAnalyzer(nba_completed)
nhl_team_stats = nhl_analyzer.analyze_team_b2b_performance()

# Sidebar
with st.sidebar:
    st.header("⚙️ B2B Betting System")
    
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    
    st.subheader("💰 Bankroll")
    st.metric("Current", f"${tracker.current_bankroll:,.2f}")
    st.metric("Starting", f"${tracker.initial_bankroll:,.2f}")
    
    profit = tracker.current_bankroll - tracker.initial_bankroll
    roi = (profit / tracker.initial_bankroll * 100) if tracker.initial_bankroll > 0 else 0
    st.metric("Profit", f"${profit:+,.2f}", f"{roi:+.1f}% ROI")
    
    st.divider()
    
    summary = tracker.get_summary()
    st.subheader("📊 Overall Record")
    if summary['total_bets'] > 0:
        st.metric("Record", f"{summary['wins']}-{summary['losses']}", f"{summary['win_rate']:.1f}% WR")
    else:
        st.info("No bets placed yet")
    
    # Sport breakdown
    sport_perf = tracker.get_sport_performance()
    
    if 'NHL' in sport_perf:
        st.subheader("🏒 NHL")
        nhl = sport_perf['NHL']
        st.metric("Record", f"{nhl['wins']}-{nhl['losses']}", f"{(nhl['wins']/(nhl['wins']+nhl['losses'])*100):.1f}% WR")
    
    if 'NBA' in sport_perf:
        st.subheader("🏀 NBA")
        nba = sport_perf['NBA']
        st.metric("Record", f"{nba['wins']}-{nba['losses']}", f"{(nba['wins']/(nba['wins']+nba['losses'])*100):.1f}% WR")

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard", 
    "🎯 Upcoming Bets",
    "📅 All B2B Games",
    "📜 Bet History"
])

# TAB 1: Dashboard
with tab1:
    st.header("🎯 B2B Betting System - Multi-Sport")
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Bankroll", f"${tracker.current_bankroll:,.2f}")
    
    with col2:
        if summary['total_bets'] > 0:
            st.metric("📊 Win Rate", f"{summary['win_rate']:.1f}%", f"{summary['wins']}-{summary['losses']}")
        else:
            st.metric("📊 Win Rate", "0%", "0-0")
    
    with col3:
        st.metric("💵 Profit", f"${profit:+,.2f}")
    
    with col4:
        st.metric("📈 ROI", f"{roi:+.1f}%")
    
    st.divider()
    
    # Sport Performance
    st.subheader("🏆 Performance by Sport")
    
    if sport_perf:
        cols = st.columns(2)
        
        for idx, (sport, stats) in enumerate(sport_perf.items()):
            with cols[idx]:
                total = stats['wins'] + stats['losses']
                wr = (stats['wins'] / total * 100) if total > 0 else 0
                
                icon = "🏒" if sport == "NHL" else "🏀"
                st.markdown(f"### {icon} {sport}")
                st.metric("Record", f"{stats['wins']}-{stats['losses']}")
                st.metric("Win Rate", f"{wr:.1f}%")
                st.metric("Profit", f"${stats['profit']:+,.2f}")
                st.metric("Bets", stats['bets'])
    
    st.divider()
    
    # Tier Performance
    st.subheader("🎯 Performance by Tier")
    
    tier_perf = tracker.get_tier_performance()
    
    if tier_perf:
        cols = st.columns(3)
        
        for idx, tier in enumerate(['S', 'A', 'B']):
            with cols[idx]:
                if tier in tier_perf:
                    stats = tier_perf[tier]
                    total = stats['wins'] + stats['losses']
                    wr = (stats['wins'] / total * 100) if total > 0 else 0
                    
                    st.markdown(f"### Tier {tier} - {TIERS[tier]['name']}")
                    st.metric("Record", f"{stats['wins']}-{stats['losses']}")
                    st.metric("Win Rate", f"{wr:.1f}%")
                    st.metric("Profit", f"${stats['profit']:+,.2f}")
                else:
                    st.markdown(f"### Tier {tier} - {TIERS[tier]['name']}")
                    st.info("No bets yet")
    
    st.divider()
    
    # Strategy explanation
    with st.expander("📖 How the System Works"):
        st.markdown("""
        ### Multi-Sport B2B Betting System
        
        **The Edge:** Teams on back-to-back games are fatigued. Rested opponents have a measurable advantage.
        
        **Sports Covered:**
        - 🏒 **NHL** - Works for home AND away rested teams
        - 🏀 **NBA** - Works ONLY for home rested teams
        
        **3-Tier Strategy:**
        
        | Tier | NHL Criteria | NBA Criteria | NHL WR | NBA WR |
        |------|-------------|--------------|--------|--------|
        | **S** | 4-5 wins + 2+ adv | HOME, 4-5 wins + 2+ adv | 69.2% | 76.0% |
        | **A** | 4-5 wins + 1+ adv | HOME, 4-5 wins + 1+ adv | 68.4% | 67.9% |
        | **B** | 2+ advantage | HOME, 2+ advantage | 66.0% | 76.0% |
        
        **10-Year Validation:**
        - 🏒 NHL: 12,620 games analyzed, 58.4% baseline
        - 🏀 NBA: 12,623 games analyzed, 56.8% baseline
        
        **Expected Annual Performance:**
        - ~150 bets per year (100 NHL + 50 NBA)
        - ~70% overall win rate
        - Kelly 25% with $1,000 cap
        """)

# TAB 2: Upcoming Bets
with tab2:
    st.header(f"🎯 Upcoming Bets (Qualifying Games Only)")
    
    sport_tab1, sport_tab2 = st.tabs(["🏒 NHL", "🏀 NBA"])
    
    # NHL Upcoming
    with sport_tab1:
        st.subheader(f"NHL - Next {UPCOMING_GAMES_DAYS} Days")
        
        cutoff_date = (datetime.now() + timedelta(days=UPCOMING_GAMES_DAYS)).date()
        nhl_upcoming_filtered = nhl_upcoming[nhl_upcoming['date'] <= cutoff_date]
        
        if len(nhl_upcoming_filtered) == 0:
            st.info(f"No NHL games in next {UPCOMING_GAMES_DAYS} days")
        else:
            recommendations = []
            
            for _, game in nhl_upcoming_filtered.iterrows():
                home_rest = game.get('home_rest', 999)
                away_rest = game.get('away_rest', 999)
                home_b2b = home_rest == 1
                away_b2b = away_rest == 1
                
                if (home_b2b and not away_b2b) or (not home_b2b and away_b2b):
                    game_data = {
                        'date': game['date'],
                        'home': game['home'],
                        'away': game['away'],
                        'home_rest': home_rest,
                        'away_rest': away_rest,
                        'home_b2b': home_b2b,
                        'away_b2b': away_b2b
                    }
                    
                    rec = nhl_enhanced.should_bet(game_data, nhl_team_stats, nhl_standings)
                    
                    if rec['should_bet']:
                        tier_perf = tracker.get_tier_performance(sport='NHL')
                        if rec['tier'] in tier_perf:
                            stats = tier_perf[rec['tier']]
                            total = stats['wins'] + stats['losses']
                            actual_wr = (stats['wins'] / total * 100) if total > 0 else TIERS[rec['tier']]['nhl_historical_wr']
                        else:
                            actual_wr = TIERS[rec['tier']]['nhl_historical_wr']
                        
                        bet_size = tracker.calculate_kelly_bet(actual_wr)
                        
                        rested = rec['pick']
                        b2b_team = game['home'] if rested == game['away'] else game['away']
                        
                        rested_form = nhl_enhanced.team_streaks.get(rested, {})
                        b2b_form = nhl_enhanced.team_streaks.get(b2b_team, {})
                        
                        recommendations.append({
                            'Date': game['date'].strftime('%Y-%m-%d'),
                            'Matchup': f"{game['away']} @ {game['home']}",
                            'Pick': rec['pick'],
                            'Tier': rec['tier'],
                            'Rested L5': rested_form.get('last_5', '?'),
                            'B2B L5': b2b_form.get('last_5', '?'),
                            'Form Adv': f"+{rec.get('form_advantage', 0)}",
                            'Expected WR': f"{actual_wr:.1f}%",
                            'Bet Size': f"${bet_size:.2f}",
                            'Criteria': TIERS[rec['tier']]['nhl_criteria']
                        })
            
            if recommendations:
                rec_df = pd.DataFrame(recommendations)
                st.dataframe(rec_df, use_container_width=True, hide_index=True)
                st.success(f"✅ Found {len(recommendations)} NHL qualifying bet(s)!")
            else:
                st.info("No NHL games meet criteria in next 30 days")
    
    # NBA Upcoming
    with sport_tab2:
        st.subheader("NBA - Next 30 Days")
        
        if len(nba_upcoming) == 0:
            st.info("No NBA games in next 30 days")
        else:
            recommendations = []
            
            for _, game in nba_upcoming.iterrows():
                home_b2b = game.get('home_b2b', False)
                away_b2b = game.get('away_b2b', False)
                
                # NBA only: home rested vs away B2B
                if not home_b2b and away_b2b:
                    game_data = {
                        'date': game['date'],
                        'home': game['home'],
                        'away': game['away'],
                        'home_b2b': home_b2b,
                        'away_b2b': away_b2b
                    }
                    
                    rec = nba_enhanced.should_bet(game_data, {}, nba_standings)
                    
                    if rec['should_bet']:
                        tier_perf = tracker.get_tier_performance(sport='NBA')
                        if rec['tier'] in tier_perf:
                            stats = tier_perf[rec['tier']]
                            total = stats['wins'] + stats['losses']
                            actual_wr = (stats['wins'] / total * 100) if total > 0 else TIERS[rec['tier']]['nba_historical_wr']
                        else:
                            actual_wr = TIERS[rec['tier']]['nba_historical_wr']
                        
                        bet_size = tracker.calculate_kelly_bet(actual_wr)
                        
                        rested = rec['pick']
                        b2b_team = game['away']
                        
                        rested_form = nba_enhanced.team_streaks.get(rested, {})
                        b2b_form = nba_enhanced.team_streaks.get(b2b_team, {})
                        
                        recommendations.append({
                            'Date': game['date'].strftime('%Y-%m-%d'),
                            'Matchup': f"{game['away']} @ {game['home']}",
                            'Pick': rec['pick'],
                            'Tier': rec['tier'],
                            'Rested L5': rested_form.get('last_5', '?'),
                            'B2B L5': b2b_form.get('last_5', '?'),
                            'Form Adv': f"+{rec.get('form_advantage', 0)}",
                            'Expected WR': f"{actual_wr:.1f}%",
                            'Bet Size': f"${bet_size:.2f}",
                            'Criteria': TIERS[rec['tier']]['nba_criteria']
                        })
            
            if recommendations:
                rec_df = pd.DataFrame(recommendations)
                st.dataframe(rec_df, use_container_width=True, hide_index=True)
                st.success(f"✅ Found {len(recommendations)} NBA qualifying bet(s)!")
            else:
                st.info("No NBA games meet criteria in next 30 days")

# TAB 3: All B2B Games
with tab3:
    st.header("📅 All Back-to-Back Games (Next 7 Days)")
    st.caption("Shows ALL B2B situations where one team is rested and one is on B2B")
    
    sport_tab1, sport_tab2 = st.tabs(["🏒 NHL", "🏀 NBA"])
    
    # NHL All B2B
    with sport_tab1:
        st.subheader("NHL B2B Games")
        
        cutoff_date = (datetime.now() + timedelta(days=7)).date()
        nhl_filtered = nhl_upcoming[nhl_upcoming['date'] <= cutoff_date].sort_values('date')
        
        all_b2b = []
        
        for _, game in nhl_filtered.iterrows():
            home_rest = game.get('home_rest', 999)
            away_rest = game.get('away_rest', 999)
            home_b2b = home_rest == 1
            away_b2b = away_rest == 1
            
            # ANY B2B situation
            if (home_b2b and not away_b2b) or (not home_b2b and away_b2b):
                rested_team = game['home'] if not home_b2b else game['away']
                b2b_team = game['away'] if not home_b2b else game['home']
                
                rested_form = nhl_enhanced.team_streaks.get(rested_team, {})
                b2b_form = nhl_enhanced.team_streaks.get(b2b_team, {})
                
                rested_wins = rested_form.get('last_5_wins', 0)
                b2b_wins = b2b_form.get('last_5_wins', 0)
                form_adv = rested_wins - b2b_wins
                
                # Check if qualifies (optional)
                game_data = {
                    'date': game['date'],
                    'home': game['home'],
                    'away': game['away'],
                    'home_rest': home_rest,
                    'away_rest': away_rest,
                    'home_b2b': home_b2b,
                    'away_b2b': away_b2b
                }
                
                rec = nhl_enhanced.should_bet(game_data, nhl_team_stats, nhl_standings)
                
                all_b2b.append({
                    'Date': game['date'].strftime('%m/%d'),
                    'Matchup': f"{game['away']} @ {game['home']}",
                    'Rested': rested_team,
                    'Rested L5': rested_form.get('last_5', '0-5'),
                    'B2B': b2b_team,
                    'B2B L5': b2b_form.get('last_5', '0-5'),
                    'Form Adv': f"+{form_adv}" if form_adv >= 0 else str(form_adv),
                    'Bet?': '✅ Tier ' + rec['tier'] if rec['should_bet'] else '❌',
                    'Why': rec['reason'][:50] + '...' if len(rec['reason']) > 50 else rec['reason']
                })
        
        if all_b2b:
            b2b_df = pd.DataFrame(all_b2b)
            st.dataframe(b2b_df, use_container_width=True, hide_index=True, height=500)
            
            qualifying = len([x for x in all_b2b if x['Bet?'].startswith('✅')])
            st.info(f"📊 {len(all_b2b)} total B2B games | ✅ {qualifying} qualify for betting")
        else:
            st.warning("No B2B games in next 7 days")
    
    # NBA All B2B
    with sport_tab2:
        st.subheader("NBA B2B Games")
        st.caption("Showing ALL B2B games (not just home rested)")
        
        cutoff_date = (datetime.now() + timedelta(days=7)).date()
        nba_filtered = nba_upcoming[nba_upcoming['date'] <= cutoff_date].sort_values('date')
        
        all_b2b = []
        
        for _, game in nba_filtered.iterrows():
            home_b2b = game.get('home_b2b', False)
            away_b2b = game.get('away_b2b', False)
            
            # ANY B2B situation
            if (home_b2b and not away_b2b) or (not home_b2b and away_b2b):
                rested_team = game['home'] if not home_b2b else game['away']
                b2b_team = game['away'] if not home_b2b else game['home']
                is_home_rested = not home_b2b
                
                rested_form = nba_enhanced.team_streaks.get(rested_team, {})
                b2b_form = nba_enhanced.team_streaks.get(b2b_team, {})
                
                rested_wins = rested_form.get('last_5_wins', 0)
                b2b_wins = b2b_form.get('last_5_wins', 0)
                form_adv = rested_wins - b2b_wins
                
                # Check if qualifies
                if is_home_rested:
                    game_data = {
                        'date': game['date'],
                        'home': game['home'],
                        'away': game['away'],
                        'home_b2b': home_b2b,
                        'away_b2b': away_b2b
                    }
                    rec = nba_enhanced.should_bet(game_data, {}, nba_standings)
                    bet_status = '✅ Tier ' + rec['tier'] if rec['should_bet'] else '❌'
                    why = rec['reason'][:50] + '...' if len(rec['reason']) > 50 else rec['reason']
                else:
                    bet_status = '❌'
                    why = "NBA strategy only works for HOME rested"
                
                all_b2b.append({
                    'Date': game['date'].strftime('%m/%d'),
                    'Matchup': f"{game['away']} @ {game['home']}",
                    'Rested': rested_team + (' 🏠' if is_home_rested else ' ✈️'),
                    'Rested L5': rested_form.get('last_5', '0-5'),
                    'B2B': b2b_team,
                    'B2B L5': b2b_form.get('last_5', '0-5'),
                    'Form Adv': f"+{form_adv}" if form_adv >= 0 else str(form_adv),
                    'Bet?': bet_status,
                    'Why': why
                })
        
        if all_b2b:
            b2b_df = pd.DataFrame(all_b2b)
            st.dataframe(b2b_df, use_container_width=True, hide_index=True, height=500)
            
            qualifying = len([x for x in all_b2b if x['Bet?'].startswith('✅')])
            st.info(f"📊 {len(all_b2b)} total B2B games | ✅ {qualifying} qualify for betting | 🏠 = home rested, ✈️ = away rested")
        else:
            st.warning("No B2B games in next 7 days")

# TAB 4: Bet History
with tab4:
    st.header("📜 Bet History")
    
    completed_bets = [b for b in tracker.bets if b['result'] != 'pending']
    
    if not completed_bets:
        st.info("No completed bets yet.")
    else:
        # Filters
        col1, col2 = st.columns([1, 3])
        
        with col1:
            sport_filter = st.multiselect(
                "Filter by Sport",
                ['NHL', 'NBA'],
                default=['NHL', 'NBA']
            )
        
        # Build history
        history_data = []
        for bet in completed_bets:
            if bet.get('sport', 'NHL') in sport_filter:
                sport_icon = "🏒" if bet.get('sport') == 'NHL' else "🏀"
                history_data.append({
                    'Sport': sport_icon,
                    'Date': bet['date'],
                    'Matchup': f"{bet['away']} @ {bet['home']}",
                    'Pick': bet['pick'],
                    'Tier': bet.get('tier', 'S'),
                    'Form Adv': f"+{bet.get('form_advantage', 0)}" if bet.get('form_advantage') else 'N/A',
                    'Bet': f"${bet['bet_amount']:.2f}",
                    'Result': '✅ Won' if bet['result'] == 'won' else '❌ Lost',
                    'Profit': f"${bet['profit']:+.2f}"
                })
        
        if history_data:
            history_df = pd.DataFrame(history_data)
            # Sort by date (newest first)
            history_df['Date'] = pd.to_datetime(history_df['Date'])
            history_df = history_df.sort_values('Date', ascending=False)
            history_df['Date'] = history_df['Date'].dt.strftime('%Y-%m-%d')
            st.dataframe(history_df, use_container_width=True, hide_index=True, height=600)
            
            # Summary
            st.divider()
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Bets", len(completed_bets))
            with col2:
                st.metric("Record", f"{summary['wins']}-{summary['losses']}")
            with col3:
                st.metric("Win Rate", f"{summary['win_rate']:.1f}%")
            with col4:
                total_profit = sum(b['profit'] for b in completed_bets)
                st.metric("Total Profit", f"${total_profit:+,.2f}")
        else:
            st.info("No bets match filters")
