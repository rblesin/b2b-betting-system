from scraper import HockeyReferenceScraper
from analyzer import B2BAnalyzer

def main():
    """Main execution function"""
    
    print("="*60)
    print("NHL BACK-TO-BACK BETTING ANALYSIS")
    print("="*60)
    
    # Use 2025 for 2024-25 season (current season)
    scraper = HockeyReferenceScraper(season="2025")
    
    try:
        games_df = scraper.scrape_schedule()
    except Exception as e:
        print(f"Error scraping data: {e}")
        return
    
    analyzer = B2BAnalyzer(games_df)
    analyzer.calculate_rest_days()
    
    # Overall B2B win rates
    results = analyzer.analyze_win_rates()
    
    # Team-specific B2B performance
    team_stats = analyzer.analyze_team_b2b_performance()
    
    print("\n" + "="*60)
    print("SAMPLE B2B GAMES (Rested Home vs B2B Away)")
    print("="*60)
    
    sample = results['rested_home_b2b_away'].head(10)
    for _, game in sample.iterrows():
        winner = game['home'] if game['home_win'] else game['away']
        print(f"{game['date']} | {game['home']} (Rested) vs {game['away']} (B2B)")
        print(f"  Score: {game['home_goals']}-{game['away_goals']} | Winner: {winner}")
    
    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)

if __name__ == "__main__":
    main()
