"""
SpineRip Trading AI - Market Analysis & Trading Signals
Uses Alpaca API + pandas-ta for technical analysis
"""

import os
import json
import requests
from datetime import datetime, timedelta
import pandas as pd

# Install: pip install pandas-ta-classic alpaca-py
try:
    import pandas_ta_classic as ta
except ImportError:
    print("Installing pandas-ta-classic...")
    os.system("pip install pandas-ta-classic alpaca-py")
    import pandas_ta_classic as ta

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


class SpineRipAI:
    """AI-powered trading assistant for day trading"""
    
    def __init__(self, api_key=None, api_secret=None, paper=True):
        """Initialize with Alpaca API credentials"""
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.api_secret = api_secret or os.getenv("ALPACA_API_SECRET")
        self.paper = paper
        
        if not self.api_key or not self.api_secret:
            print("⚠️  No Alpaca API credentials found!")
            print("Sign up free at: https://alpaca.markets/")
            print("\nPaper Trading (Practice):")
            print("  - $100,000 virtual money")
            print("  - Test strategies risk-free")
            print("  - Real-time market data")
            self.demo_mode = True
        else:
            self.trading_client = TradingClient(self.api_key, self.api_secret, paper=paper)
            self.data_client = StockHistoricalDataClient(self.api_key, self.api_secret)
            self.demo_mode = False
    
    def get_market_data(self, symbol, days=30):
        """Get historical market data for analysis"""
        if self.demo_mode:
            # Generate demo data
            dates = pd.date_range(end=datetime.now(), periods=days*390, freq='1min')
            df = pd.DataFrame({
                'timestamp': dates,
                'open': 100 + pd.Series(range(len(dates))).apply(lambda x: x % 20 - 10),
                'high': 105 + pd.Series(range(len(dates))).apply(lambda x: x % 20 - 5),
                'low': 95 + pd.Series(range(len(dates))).apply(lambda x: x % 20 - 15),
                'close': 100 + pd.Series(range(len(dates))).apply(lambda x: x % 20 - 10),
                'volume': [1000000 + (i % 500000) for i in range(len(dates))]
            })
            return df
        
        # Real Alpaca data
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Minute,
            start=datetime.now() - timedelta(days=days)
        )
        
        bars = self.data_client.get_stock_bars(request)
        df = bars.df
        df.reset_index(inplace=True)
        return df
    
    def analyze_technicals(self, df):
        """Analyze with 15+ technical indicators"""
        
        # Trend Indicators
        df['sma_20'] = ta.sma(df['close'], length=20)
        df['sma_50'] = ta.sma(df['close'], length=50)
        df['ema_12'] = ta.ema(df['close'], length=12)
        df['ema_26'] = ta.ema(df['close'], length=26)
        
        # Momentum Indicators
        df['rsi'] = ta.rsi(df['close'], length=14)
        macd = ta.macd(df['close'])
        df['macd'] = macd['MACD_12_26_9']
        df['macd_signal'] = macd['MACDs_12_26_9']
        df['macd_hist'] = macd['MACDh_12_26_9']
        
        # Volatility Indicators
        bbands = ta.bbands(df['close'], length=20)
        df['bb_upper'] = bbands['BBU_20_2.0']
        df['bb_middle'] = bbands['BBM_20_2.0']
        df['bb_lower'] = bbands['BBL_20_2.0']
        
        # Volume Indicators
        df['obv'] = ta.obv(df['close'], df['volume'])
        
        # Stochastic
        stoch = ta.stoch(df['high'], df['low'], df['close'])
        df['stoch_k'] = stoch['STOCHk_14_3_3']
        df['stoch_d'] = stoch['STOCHd_14_3_3']
        
        # ADX (Trend Strength)
        adx = ta.adx(df['high'], df['low'], df['close'])
        df['adx'] = adx['ADX_14']
        
        return df
    
    def generate_signal(self, df):
        """Generate BUY/SELL/HOLD signal with confidence"""
        
        latest = df.iloc[-1]
        signals = []
        confidence = 0
        
        # RSI Signals
        if latest['rsi'] < 30:
            signals.append("🔵 RSI Oversold (Bullish)")
            confidence += 20
        elif latest['rsi'] > 70:
            signals.append("🔴 RSI Overbought (Bearish)")
            confidence -= 20
        
        # MACD Signals
        if latest['macd'] > latest['macd_signal']:
            signals.append("🔵 MACD Bullish Crossover")
            confidence += 15
        else:
            signals.append("🔴 MACD Bearish")
            confidence -= 15
        
        # Moving Average Signals
        if latest['close'] > latest['sma_20'] > latest['sma_50']:
            signals.append("🔵 Price Above MAs (Uptrend)")
            confidence += 15
        elif latest['close'] < latest['sma_20'] < latest['sma_50']:
            signals.append("🔴 Price Below MAs (Downtrend)")
            confidence -= 15
        
        # Bollinger Bands
        if latest['close'] < latest['bb_lower']:
            signals.append("🔵 Below Lower Band (Oversold)")
            confidence += 10
        elif latest['close'] > latest['bb_upper']:
            signals.append("🔴 Above Upper Band (Overbought)")
            confidence -= 10
        
        # Stochastic
        if latest['stoch_k'] < 20 and latest['stoch_d'] < 20:
            signals.append("🔵 Stochastic Oversold")
            confidence += 10
        elif latest['stoch_k'] > 80 and latest['stoch_d'] > 80:
            signals.append("🔴 Stochastic Overbought")
            confidence -= 10
        
        # ADX (Trend Strength)
        if latest['adx'] > 25:
            signals.append(f"💪 Strong Trend (ADX: {latest['adx']:.1f})")
        else:
            signals.append(f"📊 Weak Trend (ADX: {latest['adx']:.1f})")
        
        # Final Signal
        if confidence >= 30:
            action = "🟢 STRONG BUY"
        elif confidence >= 15:
            action = "🔵 BUY"
        elif confidence <= -30:
            action = "🔴 STRONG SELL"
        elif confidence <= -15:
            action = "🟠 SELL"
        else:
            action = "⚪ HOLD"
        
        return {
            'action': action,
            'confidence': confidence,
            'signals': signals,
            'price': latest['close'],
            'rsi': latest['rsi'],
            'macd': latest['macd'],
            'adx': latest['adx']
        }
    
    def explain_strategy(self, strategy_name):
        """Explain trading strategies in simple terms"""
        
        strategies = {
            'scalping': {
                'name': 'Scalping',
                'timeframe': '1-5 minutes',
                'description': 'Quick trades for small profits. Buy low, sell high within minutes.',
                'indicators': ['Level 2 data', 'Volume', 'Price action'],
                'risk': 'Medium - Many small trades',
                'profit_target': '0.1% - 0.5% per trade'
            },
            'momentum': {
                'name': 'Momentum Trading',
                'timeframe': '15-60 minutes',
                'description': 'Ride the wave! Buy stocks moving up strongly, sell when momentum slows.',
                'indicators': ['RSI', 'MACD', 'Volume'],
                'risk': 'Medium-High - Fast moving stocks',
                'profit_target': '1% - 3% per trade'
            },
            'breakout': {
                'name': 'Breakout Trading',
                'timeframe': '30 minutes - 2 hours',
                'description': 'Wait for stock to break resistance, then ride the move up.',
                'indicators': ['Support/Resistance', 'Volume', 'Bollinger Bands'],
                'risk': 'Medium - Wait for confirmation',
                'profit_target': '2% - 5% per trade'
            },
            'reversal': {
                'name': 'Reversal Trading',
                'timeframe': '1-4 hours',
                'description': 'Buy when downtrend ends, sell when uptrend ends. Catch the turn.',
                'indicators': ['RSI', 'Stochastic', 'Candlestick patterns'],
                'risk': 'High - Catching falling knives',
                'profit_target': '3% - 7% per trade'
            },
            'gap': {
                'name': 'Gap Trading',
                'timeframe': 'Market open (9:30-11:00 AM)',
                'description': 'Trade stocks that gap up/down at open due to news.',
                'indicators': ['Pre-market volume', 'News', 'Gap size'],
                'risk': 'High - Volatile opens',
                'profit_target': '2% - 10% per trade'
            }
        }
        
        return strategies.get(strategy_name.lower(), strategies['momentum'])
    
    def get_watchlist(self):
        """Get recommended stocks for day trading"""
        
        # Popular day trading stocks
        return {
            'High Volume': ['SPY', 'QQQ', 'AAPL', 'TSLA', 'NVDA'],
            'Volatile': ['GME', 'AMC', 'PLTR', 'NIO', 'COIN'],
            'Tech Giants': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'],
            'EV Sector': ['TSLA', 'RIVN', 'LCID', 'NIO', 'XPEV'],
            'Meme Stocks': ['GME', 'AMC', 'BBBY', 'CLOV', 'HOOD']
        }
    
    def risk_management(self, account_balance, risk_percent=1):
        """Calculate position size based on risk"""
        
        risk_amount = account_balance * (risk_percent / 100)
        
        return {
            'account_balance': account_balance,
            'risk_percent': risk_percent,
            'risk_per_trade': risk_amount,
            'max_loss': risk_amount,
            'recommendation': f"Risk ${risk_amount:.2f} per trade (stop loss)"
        }


def demo():
    """Demo the AI trading assistant"""
    
    print("\n" + "="*60)
    print("🤖 SPINERIP AI TRADING ASSISTANT")
    print("="*60 + "\n")
    
    ai = SpineRipAI()
    
    # Analyze AAPL
    print("📊 Analyzing AAPL...\n")
    df = ai.get_market_data("AAPL", days=30)
    df = ai.analyze_technicals(df)
    signal = ai.generate_signal(df)
    
    print(f"💰 Current Price: ${signal['price']:.2f}")
    print(f"📈 Signal: {signal['action']}")
    print(f"🎯 Confidence: {signal['confidence']}/100\n")
    
    print("📊 Technical Indicators:")
    print(f"  RSI: {signal['rsi']:.1f} {'(Oversold)' if signal['rsi'] < 30 else '(Overbought)' if signal['rsi'] > 70 else '(Neutral)'}")
    print(f"  MACD: {signal['macd']:.2f}")
    print(f"  ADX: {signal['adx']:.1f} {'(Strong Trend)' if signal['adx'] > 25 else '(Weak Trend)'}\n")
    
    print("🎯 Signals:")
    for sig in signal['signals']:
        print(f"  {sig}")
    
    # Strategy explanation
    print("\n" + "="*60)
    print("📚 STRATEGY: MOMENTUM TRADING")
    print("="*60 + "\n")
    
    strategy = ai.explain_strategy('momentum')
    print(f"⏱️  Timeframe: {strategy['timeframe']}")
    print(f"📖 Description: {strategy['description']}")
    print(f"📊 Indicators: {', '.join(strategy['indicators'])}")
    print(f"⚠️  Risk Level: {strategy['risk']}")
    print(f"💰 Profit Target: {strategy['profit_target']}")
    
    # Risk management
    print("\n" + "="*60)
    print("🛡️ RISK MANAGEMENT")
    print("="*60 + "\n")
    
    risk = ai.risk_management(10000, risk_percent=1)
    print(f"💰 Account Balance: ${risk['account_balance']:,.2f}")
    print(f"📊 Risk Per Trade: {risk['risk_percent']}%")
    print(f"🛑 Max Loss: ${risk['risk_per_trade']:.2f}")
    print(f"💡 {risk['recommendation']}")
    
    # Watchlist
    print("\n" + "="*60)
    print("📋 WATCHLIST RECOMMENDATIONS")
    print("="*60 + "\n")
    
    watchlist = ai.get_watchlist()
    for category, tickers in watchlist.items():
        print(f"\n{category}:")
        print(f"  {', '.join(tickers)}")
    
    print("\n" + "="*60)
    print("🔗 GETTING STARTED")
    print("="*60 + "\n")
    print("1. Sign up for FREE Alpaca paper trading:")
    print("   https://alpaca.markets/")
    print("\n2. Get your API keys (FREE)")
    print("\n3. Set environment variables:")
    print("   $env:ALPACA_API_KEY='your_key'")
    print("   $env:ALPACA_API_SECRET='your_secret'")
    print("\n4. Start trading with $100,000 virtual money!")
    print("\n💰 Upgrade to SpineRip PRO for:")
    print("  ✓ Automated trading bot")
    print("  ✓ Real-time alerts")
    print("  ✓ Advanced strategies")
    print("  ✓ Portfolio tracking")
    print("\n💳 Pay $19/month or $99 lifetime:")
    print("   Cash App: $JustinHawpetoss7")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    demo()
