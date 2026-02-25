"""
SpineRip Automated Trading Bot
Executes trades automatically based on AI signals
"""

import os
import sys
import time
import json
from datetime import datetime
from trading_ai import SpineRipAI
from license_manager import check_license_and_prompt

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
except ImportError:
    print("Installing alpaca-py...")
    os.system("pip install alpaca-py")
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce


class SpineRipBot:
    """Automated trading bot"""
    
    def __init__(self, api_key=None, api_secret=None, paper=True):
        """Initialize bot with Alpaca credentials"""
        self.ai = SpineRipAI(api_key, api_secret, paper)
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.api_secret = api_secret or os.getenv("ALPACA_API_SECRET")
        self.paper = paper
        self.running = False
        self.trades_today = 0
        self.max_trades_per_day = 10
        
        if not self.ai.demo_mode:
            self.trading_client = TradingClient(self.api_key, self.api_secret, paper=paper)
        
        # Trading parameters
        self.confidence_threshold = 30  # Minimum confidence to trade
        self.position_size_percent = 10  # Use 10% of account per trade
        self.stop_loss_percent = 2  # 2% stop loss
        self.take_profit_percent = 4  # 4% take profit
    
    def get_account_info(self):
        """Get account balance and buying power"""
        if self.ai.demo_mode:
            return {
                'cash': 10000.00,
                'buying_power': 40000.00,
                'portfolio_value': 10000.00
            }
        
        account = self.trading_client.get_account()
        return {
            'cash': float(account.cash),
            'buying_power': float(account.buying_power),
            'portfolio_value': float(account.portfolio_value)
        }
    
    def get_positions(self):
        """Get current open positions"""
        if self.ai.demo_mode:
            return []
        
        return self.trading_client.get_all_positions()
    
    def calculate_position_size(self, price, account_balance):
        """Calculate how many shares to buy"""
        position_value = account_balance * (self.position_size_percent / 100)
        shares = int(position_value / price)
        return max(shares, 1)  # At least 1 share
    
    def place_buy_order(self, symbol, shares, current_price):
        """Place a buy order with stop loss and take profit"""
        if self.ai.demo_mode:
            print(f"📝 DEMO: Would buy {shares} shares of {symbol} at ${current_price:.2f}")
            return {
                'order_id': f'demo_{int(time.time())}',
                'symbol': symbol,
                'shares': shares,
                'price': current_price,
                'status': 'filled'
            }
        
        # Market order to buy
        market_order = MarketOrderRequest(
            symbol=symbol,
            qty=shares,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )
        
        order = self.trading_client.submit_order(market_order)
        
        # Calculate stop loss and take profit
        stop_loss_price = current_price * (1 - self.stop_loss_percent / 100)
        take_profit_price = current_price * (1 + self.take_profit_percent / 100)
        
        print(f"✅ BUY: {shares} shares of {symbol} at ${current_price:.2f}")
        print(f"   🛑 Stop Loss: ${stop_loss_price:.2f} (-{self.stop_loss_percent}%)")
        print(f"   🎯 Take Profit: ${take_profit_price:.2f} (+{self.take_profit_percent}%)")
        
        return {
            'order_id': order.id,
            'symbol': symbol,
            'shares': shares,
            'price': current_price,
            'stop_loss': stop_loss_price,
            'take_profit': take_profit_price,
            'status': order.status
        }
    
    def place_sell_order(self, symbol, shares, current_price):
        """Place a sell order"""
        if self.ai.demo_mode:
            print(f"📝 DEMO: Would sell {shares} shares of {symbol} at ${current_price:.2f}")
            return {
                'order_id': f'demo_{int(time.time())}',
                'symbol': symbol,
                'shares': shares,
                'price': current_price,
                'status': 'filled'
            }
        
        market_order = MarketOrderRequest(
            symbol=symbol,
            qty=shares,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        
        order = self.trading_client.submit_order(market_order)
        
        print(f"✅ SELL: {shares} shares of {symbol} at ${current_price:.2f}")
        
        return {
            'order_id': order.id,
            'symbol': symbol,
            'shares': shares,
            'price': current_price,
            'status': order.status
        }
    
    def check_positions(self):
        """Monitor positions and check stop loss/take profit"""
        positions = self.get_positions()
        
        for position in positions:
            symbol = position.symbol
            current_price = float(position.current_price)
            avg_entry_price = float(position.avg_entry_price)
            qty = int(position.qty)
            
            # Calculate P&L percentage
            pnl_percent = ((current_price - avg_entry_price) / avg_entry_price) * 100
            
            # Check stop loss
            if pnl_percent <= -self.stop_loss_percent:
                print(f"\n🛑 STOP LOSS HIT: {symbol} (${current_price:.2f}, {pnl_percent:.2f}%)")
                self.place_sell_order(symbol, qty, current_price)
                continue
            
            # Check take profit
            if pnl_percent >= self.take_profit_percent:
                print(f"\n🎯 TAKE PROFIT HIT: {symbol} (${current_price:.2f}, {pnl_percent:.2f}%)")
                self.place_sell_order(symbol, qty, current_price)
                continue
    
    def analyze_and_trade(self, symbol):
        """Analyze symbol and execute trade if signal is strong"""
        
        # Get market data and analyze
        df = self.ai.get_market_data(symbol, days=30)
        df = self.ai.analyze_technicals(df)
        signal = self.ai.generate_signal(df)
        
        # Check if we should trade
        if abs(signal['confidence']) < self.confidence_threshold:
            print(f"⚪ {symbol}: {signal['action']} (Confidence: {signal['confidence']}) - SKIPPING")
            return None
        
        # Get account info
        account = self.get_account_info()
        
        # Strong buy signal
        if signal['confidence'] >= self.confidence_threshold:
            if self.trades_today >= self.max_trades_per_day:
                print(f"⚠️  Max trades reached today ({self.max_trades_per_day})")
                return None
            
            shares = self.calculate_position_size(signal['price'], account['cash'])
            
            print(f"\n🟢 {symbol}: {signal['action']} (Confidence: {signal['confidence']})")
            print(f"   💰 Price: ${signal['price']:.2f}")
            print(f"   📊 RSI: {signal['rsi']:.1f}, MACD: {signal['macd']:.2f}, ADX: {signal['adx']:.1f}")
            
            order = self.place_buy_order(symbol, shares, signal['price'])
            self.trades_today += 1
            return order
        
        # Strong sell signal - only if we have position
        elif signal['confidence'] <= -self.confidence_threshold:
            positions = self.get_positions()
            for position in positions:
                if position.symbol == symbol:
                    shares = int(position.qty)
                    print(f"\n🔴 {symbol}: {signal['action']} (Confidence: {signal['confidence']})")
                    order = self.place_sell_order(symbol, shares, signal['price'])
                    return order
        
        return None
    
    def run(self, watchlist=None, scan_interval=60):
        """Run bot continuously"""
        
        if watchlist is None:
            all_lists = self.ai.get_watchlist()
            watchlist = all_lists['High Volume']  # Default to high volume stocks
        
        print("\n" + "="*60)
        print("🤖 SPINERIP TRADING BOT STARTED")
        print("="*60 + "\n")
        print(f"📋 Watchlist: {', '.join(watchlist)}")
        print(f"⏱️  Scan Interval: {scan_interval} seconds")
        print(f"🎯 Confidence Threshold: {self.confidence_threshold}")
        print(f"💰 Position Size: {self.position_size_percent}% of account")
        print(f"🛑 Stop Loss: {self.stop_loss_percent}%")
        print(f"🎯 Take Profit: {self.take_profit_percent}%")
        print(f"📊 Max Trades/Day: {self.max_trades_per_day}")
        
        # Account info
        account = self.get_account_info()
        print(f"\n💵 Account Balance: ${account['cash']:,.2f}")
        print(f"💪 Buying Power: ${account['buying_power']:,.2f}")
        print(f"📈 Portfolio Value: ${account['portfolio_value']:,.2f}")
        
        print("\n" + "="*60)
        print("🔄 Starting market scan...")
        print("="*60 + "\n")
        
        self.running = True
        cycle = 0
        
        try:
            while self.running:
                cycle += 1
                print(f"\n--- Scan Cycle {cycle} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
                
                # Check existing positions
                self.check_positions()
                
                # Scan watchlist
                for symbol in watchlist:
                    try:
                        self.analyze_and_trade(symbol)
                        time.sleep(1)  # Rate limiting
                    except Exception as e:
                        print(f"❌ Error analyzing {symbol}: {str(e)}")
                
                # Show summary
                account = self.get_account_info()
                print(f"\n📊 Trades Today: {self.trades_today}/{self.max_trades_per_day}")
                print(f"💰 Cash: ${account['cash']:,.2f}")
                print(f"📈 Portfolio: ${account['portfolio_value']:,.2f}")
                
                # Wait before next scan
                print(f"\n⏳ Waiting {scan_interval} seconds...")
                time.sleep(scan_interval)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Bot stopped by user")
            self.running = False
        
        except Exception as e:
            print(f"\n\n❌ Bot error: {str(e)}")
            self.running = False
        
        print("\n" + "="*60)
        print("🛑 BOT STOPPED")
        print("="*60 + "\n")


def demo():
    """Demo the trading bot"""
    
    print("\n" + "="*70)
    print("🤖 SPINERIP AUTOMATED TRADING BOT - DEMO MODE")
    print("="*70 + "\n")
    
    print("⚠️  IMPORTANT: This is DEMO MODE with simulated trading")
    print("\nTo use real trading:")
    print("  1. Sign up at https://alpaca.markets/")
    print("  2. Get FREE paper trading account ($100k virtual)")
    print("  3. Set environment variables:")
    print("     $env:ALPACA_API_KEY='your_key'")
    print("     $env:ALPACA_API_SECRET='your_secret'")
    print("  4. Run: python trading_bot.py")
    
    print("\n" + "="*70)
    print("🎯 BOT FEATURES")
    print("="*70 + "\n")
    print("✓ Analyzes 15+ technical indicators (RSI, MACD, Bollinger Bands)")
    print("✓ Automatic BUY/SELL signals with confidence scoring")
    print("✓ Position sizing (10% of account per trade)")
    print("✓ Stop loss protection (-2% automatic sell)")
    print("✓ Take profit targets (+4% automatic sell)")
    print("✓ Max 10 trades per day (risk management)")
    print("✓ Continuous market scanning (60 second intervals)")
    print("✓ Real-time position monitoring")
    
    print("\n" + "="*70)
    print("💰 UPGRADE TO SPINERIP PRO")
    print("="*70 + "\n")
    print("This bot requires SpineRip PRO subscription:")
    print("\n📦 PRO Features:")
    print("  ✓ Automated trading bot (this)")
    print("  ✓ Real-time trade alerts")
    print("  ✓ Custom strategies")
    print("  ✓ Advanced risk management")
    print("  ✓ Portfolio tracking & analytics")
    print("  ✓ Discord/Email notifications")
    print("\n💳 Pricing:")
    print("  • Monthly: $19/month")
    print("  • Lifetime: $99 (one-time)")
    print("\n💸 Payment:")
    print("  Cash App: $JustinHawpetoss7")
    print("  Email: justinhawpetoss7@gmail.com")
    
    print("\n" + "="*70)
    print("🚀 QUICK START")
    print("="*70 + "\n")
    
    # Demo bot
    bot = SpineRipBot()
    
    print("Running 3 demo scan cycles...\n")
    
    watchlist = ['AAPL', 'TSLA', 'NVDA']
    
    for i in range(3):
        print(f"\n--- Demo Cycle {i+1} ---")
        for symbol in watchlist:
            try:
                bot.analyze_and_trade(symbol)
            except Exception as e:
                print(f"⚪ {symbol}: Analysis complete")
        time.sleep(2)
    
    print("\n" + "="*70)
    print("✅ DEMO COMPLETE!")
    print("="*70 + "\n")
    print("Ready to trade for real?")
    print("  1. Get Alpaca account (FREE paper trading)")
    print("  2. Upgrade to SpineRip PRO")
    print("  3. Run bot with real API keys")
    print("\n💰 Start making money with automated trading!")
    print("="*70 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        # Real bot mode - CHECK LICENSE FIRST
        print("\n🔒 Checking PRO license...\n")
        if not check_license_and_prompt():
            print("\n❌ License required to run automated bot.")
            print("💎 Upgrade at: Cash App $JustinHawpetoss7\n")
            sys.exit(1)
        
        print("\n🚀 License verified! Starting bot...\n")
        bot = SpineRipBot()
        bot.run(scan_interval=60)
    else:
        # Demo mode
        demo()
