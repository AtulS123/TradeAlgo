"""
Example paper trading script
"""

import time
from datetime import datetime

from core.paper_trading import PaperTradingEngine
from strategies.examples.sma_crossover import SMACrossoverStrategy
from data.fetcher import KiteDataFetcher
from utils.config import config
from utils.logger import logger


def run_paper_trading():
    """
    Run paper trading with SMA Crossover strategy
    """
    print("\n" + "="*60)
    print("TradeAlgo - Paper Trading Demo")
    print("="*60 + "\n")
    
    # Create strategy
    strategy = SMACrossoverStrategy(
        symbols=["RELIANCE", "TCS"],
        fast_period=10,
        slow_period=20,
        capital=100000,
        position_size=10000
    )
    
    # Initialize data fetcher (requires Kite access token)
    # For demo, we'll run without live data
    data_fetcher = None
    
    # Uncomment below if you have Kite access token
    # data_fetcher = KiteDataFetcher()
    # data_fetcher.set_access_token_from_request_token(request_token, api_secret)
    
    # Create paper trading engine
    paper_engine = PaperTradingEngine(
        strategy=strategy,
        data_fetcher=data_fetcher,
        slippage_percent=0.1,
        brokerage_percent=0.03,
        update_interval=60  # Update every 60 seconds
    )
    
    # Start paper trading
    paper_engine.start()
    
    print("\n📊 Paper trading is now running...")
    print("Press Ctrl+C to stop\n")
    
    try:
        # Run for a specified duration or until interrupted
        while True:
            time.sleep(10)
            
            # Print status every 10 seconds
            status = paper_engine.get_status()
            print(f"\r⏱️  Running: {status['duration_minutes']:.1f} min | "
                  f"Portfolio: ₹{status['portfolio_value']:,.0f} | "
                  f"Trades: {status['total_trades']}", end='')
    
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping paper trading...")
        paper_engine.stop()
        
        # Get final performance
        performance = paper_engine.get_performance()
        
        print(f"\n📈 Final Performance:")
        print(f"  Total Return: {performance.get('total_return_percent', 0):.2f}%")
        print(f"  Total Trades: {performance.get('total_trades', 0)}")
        
        print("\n✅ Paper trading stopped successfully!\n")


if __name__ == "__main__":
    run_paper_trading()
