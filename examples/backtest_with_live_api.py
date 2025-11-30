"""
Example: Backtest RSI strategy using live Kite API data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from strategies.examples.rsi_strategy import RSIStrategy
from core.live_api_backtest import LiveAPIBacktest, create_authenticated_kite


def main():
    """Run RSI backtest with live API data"""
    
    print("\n" + "="*70)
    print("RSI Strategy - Live API Backtest")
    print("="*70 + "\n")
    
    # Get request token
    if len(sys.argv) > 1:
        request_token = sys.argv[1]
    else:
        print("📋 Enter your Kite request token:")
        print("   (Get it from: https://kite.zerodha.com/connect/login?api_key=5f814cggb2e7m8z9)\n")
        request_token = input("Request Token: ").strip()
    
    if not request_token:
        print("\n❌ No token provided. Exiting...")
        return
    
    # Authenticate
    print("\n🔐 Authenticating with Kite API...")
    kite = create_authenticated_kite(request_token)
    
    if not kite:
        print("\n❌ Authentication failed. Exiting...")
        return
    
    # Create strategy
    strategy = RSIStrategy(
        symbols=["RELIANCE", "TCS", "INFY"],
        rsi_period=14,
        oversold=30,
        overbought=70,
        capital=100000,
        position_size=10000
    )
    
    # Set backtest period
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # Last 30 days
    
    # Create live API backtest
    backtest = LiveAPIBacktest(
        strategy=strategy,
        kite=kite,
        start_date=start_date,
        end_date=end_date,
        interval="5minute",  # 5-minute candles
        slippage_percent=0.1,
        brokerage_percent=0.03
    )
    
    # Run backtest
    results = backtest.run()
    
    print("✅ Backtest complete!")
    print(f"\nYou can now test ANY strategy with fresh API data!")
    print(f"No storage limits - fetch data on-demand for any period.\n")


if __name__ == "__main__":
    main()
