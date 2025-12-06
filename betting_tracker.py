import json
import os
from datetime import datetime
from config import *

class BettingTracker:
    def __init__(self, tracker_file=TRACKER_FILE, initial_bankroll=INITIAL_BANKROLL):
        self.tracker_file = tracker_file
        self.initial_bankroll = initial_bankroll
        
        if os.path.exists(tracker_file):
            with open(tracker_file, 'r') as f:
                data = json.load(f)
                self.bets = data.get('bets', [])
                self.current_bankroll = data.get('current_bankroll', initial_bankroll)
        else:
            self.bets = []
            self.current_bankroll = initial_bankroll
            self._save()
    
    def _save(self):
        with open(self.tracker_file, 'w') as f:
            json.dump({
                'bets': self.bets,
                'current_bankroll': self.current_bankroll,
                'initial_bankroll': self.initial_bankroll
            }, f, indent=2, default=str)
    
    def calculate_kelly_bet(self, win_rate_pct, odds=DEFAULT_ODDS):
        """
        Calculate Kelly bet size with $1,000 cap
        
        IMPORTANT: Cap win rate at 85% to prevent over-betting during hot streaks
        """
        # Cap at 85% to be conservative during hot streaks
        win_rate_pct = min(win_rate_pct, 85.0)
        
        p = win_rate_pct / 100.0
        q = 1.0 - p
        b = odds - 1.0
        
        # Full Kelly
        kelly_full = (b * p - q) / b
        
        # Apply fractional Kelly (25% = conservative)
        kelly_fraction = kelly_full * 0.25
        
        # Calculate bet amount
        bet_amount = self.current_bankroll * kelly_fraction
        
        # Ensure non-negative
        bet_amount = max(0.0, bet_amount)
        
        # Cap at $1,000
        bet_amount = min(bet_amount, 1000.0)
        
        return round(bet_amount, 2)
    
    def add_bet(self, date, home, away, pick, edge_pct, reason, tier=None, odds=None, 
                form_advantage=None, rested_wins=None, b2b_wins=None, sport='NHL'):
        """Add bet with sport tracking"""
        if odds is None:
            odds = DEFAULT_ODDS
        
        bet_amount = self.calculate_kelly_bet(edge_pct, odds)
        
        if bet_amount == 0:
            return False
        
        bet = {
            'date': date.isoformat() if hasattr(date, 'isoformat') else str(date),
            'sport': sport,
            'home': home,
            'away': away,
            'pick': pick,
            'odds': odds,
            'bet_amount': bet_amount,
            'edge_pct': edge_pct,
            'reason': reason,
            'tier': tier,
            'form_advantage': form_advantage,
            'rested_wins': rested_wins,
            'b2b_wins': b2b_wins,
            'result': 'pending',
            'profit': 0,
            'bankroll_before': self.current_bankroll
        }
        
        self.bets.append(bet)
        self._save()
        return True
    
    def update_result(self, date, home, away, home_won, sport='NHL'):
        """Update bet result with sport filter"""
        date_str = date.isoformat() if hasattr(date, 'isoformat') else str(date)
        
        for bet in self.bets:
            if (bet['date'] == date_str and 
                bet['sport'] == sport and
                bet['home'] == home and 
                bet['away'] == away and 
                bet['result'] == 'pending'):
                
                pick_won = (bet['pick'] == home and home_won) or (bet['pick'] == away and not home_won)
                
                if pick_won:
                    bet['result'] = 'won'
                    bet['profit'] = bet['bet_amount'] * (bet['odds'] - 1)
                    self.current_bankroll += bet['profit']
                else:
                    bet['result'] = 'lost'
                    bet['profit'] = -bet['bet_amount']
                    self.current_bankroll += bet['profit']
                
                self._save()
                return True
        
        return False
    
    def get_tier_performance(self, sport=None):
        """Get performance by tier, optionally filtered by sport"""
        tier_stats = {}
        
        for bet in self.bets:
            if bet['result'] == 'pending':
                continue
            
            if sport and bet.get('sport') != sport:
                continue
            
            tier = bet.get('tier', 'Unknown')
            if tier not in tier_stats:
                tier_stats[tier] = {'wins': 0, 'losses': 0, 'profit': 0}
            
            if bet['result'] == 'won':
                tier_stats[tier]['wins'] += 1
            else:
                tier_stats[tier]['losses'] += 1
            
            tier_stats[tier]['profit'] += bet['profit']
        
        return tier_stats
    
    def get_sport_performance(self):
        """Get performance by sport"""
        sport_stats = {}
        
        for bet in self.bets:
            if bet['result'] == 'pending':
                continue
            
            sport = bet.get('sport', 'NHL')
            if sport not in sport_stats:
                sport_stats[sport] = {'wins': 0, 'losses': 0, 'profit': 0, 'bets': 0}
            
            sport_stats[sport]['bets'] += 1
            
            if bet['result'] == 'won':
                sport_stats[sport]['wins'] += 1
            else:
                sport_stats[sport]['losses'] += 1
            
            sport_stats[sport]['profit'] += bet['profit']
        
        return sport_stats
    
    def get_summary(self, sport=None):
        """Get overall summary stats, optionally filtered by sport"""
        completed = [b for b in self.bets if b['result'] != 'pending']
        
        if sport:
            completed = [b for b in completed if b.get('sport') == sport]
        
        if not completed:
            return {
                'total_bets': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'profit': 0,
                'roi': 0
            }
        
        wins = len([b for b in completed if b['result'] == 'won'])
        losses = len(completed) - wins
        profit = sum(b['profit'] for b in completed)
        total_wagered = sum(b['bet_amount'] for b in completed)
        roi = (profit / total_wagered * 100) if total_wagered > 0 else 0
        
        return {
            'total_bets': len(completed),
            'wins': wins,
            'losses': losses,
            'win_rate': (wins / len(completed) * 100) if completed else 0,
            'profit': profit,
            'roi': roi
        }
