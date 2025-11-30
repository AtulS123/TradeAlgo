"""
Example backtest script
"""

import sys
import os
# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime, timedelta

from core.backtest import BacktestEngine
from strategies.examples.sma_crossover import SMACrossoverStrategy
# from data.fetcher import KiteDataFetcher  # Not needed for demo
from data.storage import init_db
from utils.logger import logger


def run_example_backtest():
    """
    Run an example backtest with SMA Crossover strategy
    """
    print("\n" + "="*60)
    print("TradeAlgo - Example Backtest")
    print("="*60 + "\n")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Define parameters
    symbols = ["RELIANCE", "TCS", "INFY"]
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 1, 1)
    
    # Create strategy
    strategy = SMACrossoverStrategy(
        symbols=symbols,
        fast_period=10,
        slow_period=20,
        capital=100000,
        position_size=10000
    )
    
    # Load historical data (placeholder - in reality would fetch from Kite)
    # For demo purposes, creating sample data
    print("Loading historical data...")
    for symbol in symbols:
        # Create sample data
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        data = pd.DataFrame({
            'open': 100 + pd.Series(range(len(dates))).cumsum() * 0.1,
            'high': 102 + pd.Series(range(len(dates))).cumsum() * 0.1,
            'low': 98 + pd.Series(range(len(dates))).cumsum() * 0.1,
            'close': 100 + pd.Series(range(len(dates))).cumsum() * 0.1,
            'volume': 1000000
        }, index=dates)
        
        strategy.set_data(symbol, data)
        print(f"  ✓ Loaded {len(data)} bars for {symbol}")
    
    # Create backtest engine
    print("\nInitializing backtest engine...")
    backtest = BacktestEngine(
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        slippage_percent=0.1,
        brokerage_percent=0.03
    )
    
    # Run backtest
    print("\nRunning backtest...")
    print("-" * 60)
    results = backtest.run()
    
    # Print results
    print("\n" + "="*60)
    print("BACKTEST RESULTS")
    print("="*60)
    
    metrics = results['metrics']
    
    print(f"\n📊 Performance Summary:")
    print(f"  Initial Capital: ₹{strategy.initial_capital:,.2f}")
    print(f"  Final Value: ₹{metrics.get('final_value', 0):,.2f}")
    print(f"  Total Return: {metrics.get('total_return_percent', 0):.2f}%")
    print(f"  CAGR: {metrics.get('cagr', 0):.2f}%")
    
    print(f"\n⚠️  Risk Metrics:")
    print(f"  Volatility: {metrics.get('volatility', 0):.2f}%")
    print(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
    print(f"  Sortino Ratio: {metrics.get('sortino_ratio', 0):.2f}")
    print(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
    
    print(f"\n📈 Trade Statistics:")
    print(f"  Total Trades: {metrics.get('total_trades', 0)}")
    print(f"  Win Rate: {metrics.get('win_rate', 0):.2f}%")
    
    print("\n" + "="*60)
    
    # Create visualizations
    print("\nGenerating charts...")
    from utils.visualization import BacktestVisualizer
    
    viz = BacktestVisualizer(
        equity_curve=results['equity_curve'],
        trades=results['trades'],
        initial_capital=strategy.initial_capital
    )
    
    # Save charts
    viz.save_all_charts("backtest_results")
    print("  ✓ Charts saved to backtest_results/")
    
    print("\n✅ Backtest completed successfully!\n")
    
    return results


if __name__ == "__main__":
    run_example_backtest()
