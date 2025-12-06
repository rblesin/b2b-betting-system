with open('streamlit_app.py', 'r') as f:
    content = f.read()

# Find and replace the history building section
old_section = """        # Build history (sort by date first)
        completed_bets_sorted = sorted(completed_bets, key=lambda x: x['date'], reverse=True)
        
        history_data = []
        for bet in completed_bets_sorted:
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
                })"""

new_section = """        # Build history
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
                })"""

content = content.replace(old_section, new_section)

# Add sorting AFTER building the dataframe
old_df_display = """        if history_data:
            history_df = pd.DataFrame(history_data)
            st.dataframe(history_df, width=1200, height=600)"""

new_df_display = """        if history_data:
            history_df = pd.DataFrame(history_data)
            # Sort by date (newest first)
            history_df['Date'] = pd.to_datetime(history_df['Date'])
            history_df = history_df.sort_values('Date', ascending=False)
            history_df['Date'] = history_df['Date'].dt.strftime('%Y-%m-%d')
            st.dataframe(history_df, width=1200, height=600)"""

content = content.replace(old_df_display, new_df_display)

with open('streamlit_app.py', 'w') as f:
    f.write(content)

print("✅ Fixed bet history sorting")
