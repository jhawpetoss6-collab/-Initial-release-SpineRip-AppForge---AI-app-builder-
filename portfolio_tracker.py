"""
SpineRip Portfolio Tracker
Real-time portfolio tracking, P&L calculation, performance metrics
"""

import os
import json
from datetime import datetime, timedelta
from trading_ai import SpineRipAI

try:
    from alpaca.trading.client import TradingClient
except ImportError:
    print("Installing alpaca-py...")
    os.system("pip install alpaca-py")
    from alpaca.trading.client import TradingClient


class PortfolioTracker:
    """Track portfolio performance and metrics"""
    
    def __init__(self, api_key=None, api_secret=None, paper=True):
        """Initialize tracker"""
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.api_secret = api_secret or os.getenv("ALPACA_API_SECRET")
        self.paper = paper
        
        if not self.api_key or not self.api_secret:
            self.demo_mode = True
            print("⚠️  Demo mode - using simulated data")
        else:
            self.trading_client = TradingClient(self.api_key, self.api_secret, paper=paper)
            self.demo_mode = False
    
    def get_account_summary(self):
        """Get account balance and equity"""
        if self.demo_mode:
            return {
                'cash': 10000.00,
                'portfolio_value': 12500.00,
                'buying_power': 40000.00,
                'equity': 12500.00,
                'last_equity': 10000.00
            }
        
        account = self.trading_client.get_account()
        return {
            'cash': float(account.cash),
            'portfolio_value': float(account.portfolio_value),
            'buying_power': float(account.buying_power),
            'equity': float(account.equity),
            'last_equity': float(account.last_equity)
        }
    
    def get_positions(self):
        """Get all open positions"""
        if self.demo_mode:
            return [
                {
                    'symbol': 'AAPL',
                    'qty': 10,
                    'avg_entry_price': 150.00,
                    'current_price': 165.00,
                    'market_value': 1650.00,
                    'cost_basis': 1500.00,
                    'unrealized_pl': 150.00,
                    'unrealized_plpc': 10.0,
                    'side': 'long'
                },
                {
                    'symbol': 'TSLA',
                    'qty': 5,
                    'avg_entry_price': 200.00,
                    'current_price': 210.00,
                    'market_value': 1050.00,
                    'cost_basis': 1000.00,
                    'unrealized_pl': 50.00,
                    'unrealized_plpc': 5.0,
                    'side': 'long'
                }
            ]
        
        positions = self.trading_client.get_all_positions()
        
        position_list = []
        for pos in positions:
            position_list.append({
                'symbol': pos.symbol,
                'qty': int(pos.qty),
                'avg_entry_price': float(pos.avg_entry_price),
                'current_price': float(pos.current_price),
                'market_value': float(pos.market_value),
                'cost_basis': float(pos.cost_basis),
                'unrealized_pl': float(pos.unrealized_pl),
                'unrealized_plpc': float(pos.unrealized_plpc) * 100,
                'side': pos.side
            })
        
        return position_list
    
    def get_portfolio_history(self, days=30):
        """Get portfolio performance history"""
        if self.demo_mode:
            # Generate demo history
            import pandas as pd
            dates = pd.date_range(end=datetime.now(), periods=days, freq='1D')
            values = [10000 + (i * 50) + ((i % 5) * 100 - 250) for i in range(days)]
            
            return {
                'dates': [d.strftime('%Y-%m-%d') for d in dates],
                'equity': values,
                'profit_loss': [v - 10000 for v in values],
                'profit_loss_pct': [((v - 10000) / 10000) * 100 for v in values]
            }
        
        # Get from Alpaca
        history = self.trading_client.get_portfolio_history(
            period=f"{days}D",
            timeframe="1D"
        )
        
        dates = [datetime.fromtimestamp(ts).strftime('%Y-%m-%d') for ts in history.timestamp]
        
        return {
            'dates': dates,
            'equity': history.equity,
            'profit_loss': history.profit_loss,
            'profit_loss_pct': history.profit_loss_pct
        }
    
    def calculate_metrics(self):
        """Calculate performance metrics"""
        
        account = self.get_account_summary()
        positions = self.get_positions()
        
        # Total P&L
        total_pl = account['equity'] - account['last_equity']
        total_pl_pct = (total_pl / account['last_equity']) * 100 if account['last_equity'] > 0 else 0
        
        # Position stats
        total_positions = len(positions)
        winning_positions = sum(1 for p in positions if p['unrealized_pl'] > 0)
        losing_positions = sum(1 for p in positions if p['unrealized_pl'] < 0)
        
        win_rate = (winning_positions / total_positions * 100) if total_positions > 0 else 0
        
        # Largest winner/loser
        if positions:
            largest_winner = max(positions, key=lambda x: x['unrealized_plpc'])
            largest_loser = min(positions, key=lambda x: x['unrealized_plpc'])
        else:
            largest_winner = None
            largest_loser = None
        
        return {
            'total_pl': total_pl,
            'total_pl_pct': total_pl_pct,
            'total_positions': total_positions,
            'winning_positions': winning_positions,
            'losing_positions': losing_positions,
            'win_rate': win_rate,
            'largest_winner': largest_winner,
            'largest_loser': largest_loser
        }
    
    def display_dashboard(self):
        """Display portfolio dashboard"""
        
        print("\n" + "="*70)
        print("📊 SPINERIP PORTFOLIO DASHBOARD")
        print("="*70 + "\n")
        
        # Account summary
        account = self.get_account_summary()
        
        print("💰 ACCOUNT SUMMARY")
        print("-" * 70)
        print(f"Portfolio Value:  ${account['portfolio_value']:,.2f}")
        print(f"Cash Available:   ${account['cash']:,.2f}")
        print(f"Buying Power:     ${account['buying_power']:,.2f}")
        
        # Calculate day change
        day_pl = account['equity'] - account['last_equity']
        day_pl_pct = (day_pl / account['last_equity']) * 100 if account['last_equity'] > 0 else 0
        
        pl_emoji = "📈" if day_pl >= 0 else "📉"
        print(f"\nToday's Change:   {pl_emoji} ${day_pl:+,.2f} ({day_pl_pct:+.2f}%)")
        
        # Performance metrics
        print("\n📊 PERFORMANCE METRICS")
        print("-" * 70)
        
        metrics = self.calculate_metrics()
        
        print(f"Total Positions:  {metrics['total_positions']}")
        print(f"Winning:          {metrics['winning_positions']} 🟢")
        print(f"Losing:           {metrics['losing_positions']} 🔴")
        print(f"Win Rate:         {metrics['win_rate']:.1f}%")
        
        # Positions
        print("\n📋 OPEN POSITIONS")
        print("-" * 70)
        
        positions = self.get_positions()
        
        if not positions:
            print("No open positions")
        else:
            for pos in positions:
                pl_emoji = "🟢" if pos['unrealized_pl'] >= 0 else "🔴"
                print(f"\n{pl_emoji} {pos['symbol']}")
                print(f"  Shares: {pos['qty']}")
                print(f"  Entry: ${pos['avg_entry_price']:.2f}")
                print(f"  Current: ${pos['current_price']:.2f}")
                print(f"  Value: ${pos['market_value']:,.2f}")
                print(f"  P&L: ${pos['unrealized_pl']:+,.2f} ({pos['unrealized_plpc']:+.2f}%)")
        
        # Best/Worst performers
        if metrics['largest_winner'] and metrics['largest_loser']:
            print("\n⭐ TOP PERFORMERS")
            print("-" * 70)
            
            winner = metrics['largest_winner']
            loser = metrics['largest_loser']
            
            print(f"\n🏆 Best: {winner['symbol']} (+{winner['unrealized_plpc']:.2f}%)")
            print(f"   ${winner['unrealized_pl']:+,.2f}")
            
            print(f"\n💔 Worst: {loser['symbol']} ({loser['unrealized_plpc']:.2f}%)")
            print(f"   ${loser['unrealized_pl']:+,.2f}")
        
        # Portfolio allocation
        print("\n📊 PORTFOLIO ALLOCATION")
        print("-" * 70)
        
        if positions:
            total_invested = sum(p['market_value'] for p in positions)
            
            for pos in sorted(positions, key=lambda x: x['market_value'], reverse=True):
                allocation = (pos['market_value'] / account['portfolio_value']) * 100
                bar_length = int(allocation / 2)
                bar = "█" * bar_length
                print(f"{pos['symbol']:6} {bar:20} {allocation:5.1f}%  ${pos['market_value']:>10,.2f}")
        
        print("\n" + "="*70 + "\n")
    
    def export_report(self, filename="portfolio_report.json"):
        """Export portfolio report to JSON"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'account': self.get_account_summary(),
            'positions': self.get_positions(),
            'metrics': self.calculate_metrics(),
            'history': self.get_portfolio_history(30)
        }
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Report exported to: {filepath}")
        return filepath


def demo():
    """Demo portfolio tracker"""
    
    print("\n" + "="*70)
    print("📊 SPINERIP PORTFOLIO TRACKER")
    print("="*70 + "\n")
    
    tracker = PortfolioTracker()
    
    # Display dashboard
    tracker.display_dashboard()
    
    # Performance history
    print("📈 PERFORMANCE HISTORY (30 DAYS)")
    print("-" * 70 + "\n")
    
    history = tracker.get_portfolio_history(30)
    
    # Show last 7 days
    print("Last 7 Days:")
    for i in range(-7, 0):
        date = history['dates'][i]
        equity = history['equity'][i]
        pl = history['profit_loss'][i]
        pl_pct = history['profit_loss_pct'][i]
        
        emoji = "📈" if pl >= 0 else "📉"
        print(f"{emoji} {date}: ${equity:>10,.2f}  ({pl:+8,.2f} | {pl_pct:+6.2f}%)")
    
    print("\n" + "="*70)
    print("💰 SPINERIP PRO FEATURES")
    print("="*70 + "\n")
    print("✓ Real-time portfolio tracking")
    print("✓ Detailed P&L analytics")
    print("✓ Win rate calculations")
    print("✓ Performance charts")
    print("✓ Position alerts")
    print("✓ Export reports (CSV/JSON)")
    print("✓ Tax reporting")
    print("✓ Historical backtesting")
    
    print("\n💳 Upgrade to PRO:")
    print("  Monthly: $19/month")
    print("  Lifetime: $99 one-time")
    print("\n💸 Cash App: $JustinHawpetoss7")
    print("\n" + "="*70 + "\n")
    
    # Export report
    tracker.export_report()


if __name__ == "__main__":
    demo()
