"""
Simple backtest with RSI strategy on sample data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime

from core.backtest import BacktestEngine
from strategies.examples.rsi_strategy import RSIStrategy
from data.storage import init_db
from utils.logger import logger


def run_rsi_backtest():
    """
    Run RSI strategy backtest with sample data
    """
    print("\n" + "="*70)
    print("TradeAlgo - RSI Strategy Backtest")
    print("="*70 + "\n")
    
    # Initialize database
    init_db()
    
    # Define parameters
    symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK"]
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 11, 30)
    
    # Create RSI strategy
    strategy = RSIStrategy(
        symbols=symbols,
        rsi_period=14,
        oversold=30,
        overbought=70,
        capital=100000,
        position_size=10000
    )
    
    print("📊 Generating realistic sample data for Indian stocks...")
    print(f"   Period: {start_date.date()} to {end_date.date()}\n")
    
    # Generate realistic sample data for each symbol
    for symbol in symbols:
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Different characteristics for each stock
        np.random.seed(hash(symbol) % 2**32)
        
        # Base price varies by stock
        base_prices = {
            "RELIANCE": 2500,
            "TCS": 3500,
            "INFY": 1500,
            "HDFCBANK": 1600
        }
        base_price = base_prices.get(symbol, 1000)
        
        # Generate price series with trend and volatility
        trend = 0.0005  # Slight upward trend
        volatility = 0.015  # 1.5% daily volatility
        
        returns = np.random.normal(trend, volatility, len(dates))
        prices = base_price * (1 + returns).cumprod()
        
        # Add some mean reversion to create RSI signals
        prices = prices + 50 * np.sin(np.arange(len(dates)) / 20)
        
        # Create OHLCV data
        data = pd.DataFrame({
            'open': prices * (1 + np.random.uniform(-0.005, 0.005, len(dates))),
            'high': prices * (1 + np.random.uniform(0.005, 0.015, len(dates))),
            'low': prices * (1 + np.random.uniform(-0.015, -0.005, len(dates))),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
        
        strategy.set_data(symbol, data)
        print(f"   ✓ {symbol}: {len(data)} bars loaded (₹{prices[0]:.2f} → ₹{prices[-1]:.2f})")
    
    # Create and run backtest
    print("\n🔧 Initializing backtest engine...")
    backtest = BacktestEngine(
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        slippage_percent=0.1,
        brokerage_percent=0.03
    )
    
    print("🚀 Running backtest...")
    print("-" * 70)
    
    results = backtest.run()
    
    # Print detailed results
    print("\n" + "="*70)
    print("BACKTEST RESULTS - RSI STRATEGY")
    print("="*70)
    
    metrics = results['metrics']
    
    print(f"\n📊 Strategy Configuration:")
    print(f"   Name: {strategy.name}")
    print(f"   Symbols: {', '.join(symbols)}")
    print(f"   RSI Period: 14")
    print(f"   Oversold: 30 | Overbought: 70")
    
    print(f"\n💰 Performance Summary:")
    print(f"   Initial Capital:  ₹{strategy.initial_capital:>12,.2f}")
    print(f"   Final Value:      ₹{metrics.get('final_value', 0):>12,.2f}")
    print(f"   Total Return:     {metrics.get('total_return_percent', 0):>12.2f}%")
    print(f"   CAGR:             {metrics.get('cagr', 0):>12.2f}%")
    
    print(f"\n⚠️  Risk Metrics:")
    print(f"   Volatility:       {metrics.get('volatility', 0):>12.2f}%")
    print(f"   Sharpe Ratio:     {metrics.get('sharpe_ratio', 0):>12.2f}")
    print(f"   Sortino Ratio:    {metrics.get('sortino_ratio', 0):>12.2f}")
    print(f"   Max Drawdown:     {metrics.get('max_drawdown', 0):>12.2f}%")
    print(f"   Recovery Factor:  {metrics.get('recovery_factor', 0):>12.2f}")
    
    print(f"\n📈 Trade Statistics:")
    print(f"   Total Trades:     {metrics.get('total_trades', 0):>12}")
    print(f"   Win Rate:         {metrics.get('win_rate', 0):>12.2f}%")
    print(f"   Profit Factor:    {metrics.get('profit_factor', 0):>12.2f}")
    
    print(f"\n🎯 Advanced Metrics:")
    print(f"   Calmar Ratio:     {metrics.get('calmar_ratio', 0):>12.2f}")
    
    print("\n" + "="*70)
    
    # Generate visualizations
    print("\n📊 Generating interactive charts...")
    from utils.visualization import BacktestVisualizer
    
    viz = BacktestVisualizer(
        equity_curve=results['equity_curve'],
        trades=results['trades'],
        initial_capital=strategy.initial_capital
    )
    
    viz.save_all_charts("backtest_results")
    print("   ✓ Equity curve saved to: backtest_results/equity_curve.html")
    print("   ✓ Returns distribution saved to: backtest_results/returns_distribution.html")
    print("   ✓ Trade analysis saved to: backtest_results/trade_analysis.html")
    
    print("\n✅ Backtest completed successfully!")
    print(f"   Open the HTML files in backtest_results/ to view interactive charts\n")
    
    return results


if __name__ == "__main__":
    run_rsi_backtest()
