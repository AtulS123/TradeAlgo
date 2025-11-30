"""
Backtest with real Kite historical data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime, timedelta

from core.backtest import BacktestEngine
from strategies.examples.rsi_strategy import RSIStrategy
from data.fetcher import KiteDataFetcher
from data.storage import init_db
from utils.config import config
from utils.logger import logger


def fetch_kite_data():
    """
    Fetch historical data from Kite API
    
    Note: This requires a valid access token. For first-time use:
    1. Get the login URL
    2. Login and authorize
    3. Get the request token from redirect URL
    4. Generate access token
    """
    print("\n" + "="*60)
    print("Kite API Data Fetcher")
    print("="*60 + "\n")
    
    # Initialize Kite data fetcher
    fetcher = KiteDataFetcher(
        api_key=config.kite_api_key
    )
    
    print(f"API Key: {config.kite_api_key}")
    print(f"\nTo get access token:")
    print(f"1. Visit: {fetcher.get_login_url()}")
    print(f"2. Login and authorize")
    print(f"3. Copy the 'request_token' from the redirect URL")
    print(f"4. Enter it below\n")
    
    # For automation, you can set access token directly if you have it
    # For now, we'll use a simplified approach
    
    # Get request token from user
    request_token = input("Enter request token (or press Enter to skip): ").strip()
    
    if request_token:
        try:
            access_token = fetcher.set_access_token_from_request_token(
                request_token=request_token,
                api_secret=config.kite_api_secret
            )
            print(f"\n✅ Access token generated successfully!")
            print(f"Access Token: {access_token[:20]}...")
            
            return fetcher
        except Exception as e:
            print(f"\n❌ Error generating access token: {e}")
            print("Proceeding without Kite data...")
            return None
    else:
        print("\nSkipping Kite authentication. Using sample data instead.")
        return None


def run_real_backtest():
    """
    Run backtest with real Kite historical data
    """
    print("\n" + "="*60)
    print("TradeAlgo - Real Data Backtest with RSI Strategy")
    print("="*60 + "\n")
    
    # Initialize database
    init_db()
    
    # Define parameters
    symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK"]
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 11, 30)
    
    # Create strategy
    strategy = RSIStrategy(
        symbols=symbols,
        rsi_period=14,
        oversold=30,
        overbought=70,
        capital=100000,
        position_size=10000
    )
    
    # Try to fetch real data
    fetcher = fetch_kite_data()
    
    if fetcher:
        print("\n📊 Fetching historical data from Kite...")
        
        for symbol in symbols:
            try:
                print(f"  Fetching {symbol}...", end='')
                
                # Fetch historical data
                df = fetcher.get_historical_data(
                    symbol=symbol,
                    from_date=start_date,
                    to_date=end_date,
                    interval="day",
                    exchange="NSE"
                )
                
                if not df.empty:
                    df.set_index('timestamp', inplace=True)
                    strategy.set_data(symbol, df)
                    print(f" ✓ {len(df)} bars")
                else:
                    print(f" ⚠️  No data")
                    
            except Exception as e:
                print(f" ❌ Error: {e}")
    else:
        # Use sample data
        print("\n📊 Using sample data for demonstration...")
        
        for symbol in symbols:
            # Create sample data with realistic price movements
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Generate more realistic data with trends and volatility
            import numpy as np
            np.random.seed(hash(symbol) % 2**32)  # Different seed per symbol
            
            base_price = 100 + (hash(symbol) % 1000)
            returns = np.random.normal(0.001, 0.02, len(dates))  # Daily returns
            prices = base_price * (1 + returns).cumprod()
            
            data = pd.DataFrame({
                'open': prices * (1 + np.random.uniform(-0.01, 0.01, len(dates))),
                'high': prices * (1 + np.random.uniform(0, 0.02, len(dates))),
                'low': prices * (1 + np.random.uniform(-0.02, 0, len(dates))),
                'close': prices,
                'volume': np.random.randint(1000000, 10000000, len(dates))
            }, index=dates)
            
            strategy.set_data(symbol, data)
            print(f"  ✓ Loaded {len(data)} bars for {symbol}")
    
    # Create backtest engine
    print("\n🔧 Initializing backtest engine...")
    backtest = BacktestEngine(
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        slippage_percent=0.1,
        brokerage_percent=0.03
    )
    
    # Run backtest
    print("\n🚀 Running backtest...")
    print("-" * 60)
    results = backtest.run()
    
    # Print results
    print("\n" + "="*60)
    print("BACKTEST RESULTS - RSI STRATEGY")
    print("="*60)
    
    metrics = results['metrics']
    
    print(f"\n📊 Performance Summary:")
    print(f"  Strategy: {strategy.name}")
    print(f"  Period: {start_date.date()} to {end_date.date()}")
    print(f"  Symbols: {', '.join(symbols)}")
    print(f"  Initial Capital: ₹{strategy.initial_capital:,.2f}")
    print(f"  Final Value: ₹{metrics.get('final_value', 0):,.2f}")
    print(f"  Total Return: {metrics.get('total_return_percent', 0):.2f}%")
    print(f"  CAGR: {metrics.get('cagr', 0):.2f}%")
    
    print(f"\n⚠️  Risk Metrics:")
    print(f"  Volatility: {metrics.get('volatility', 0):.2f}%")
    print(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
    print(f"  Sortino Ratio: {metrics.get('sortino_ratio', 0):.2f}")
    print(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
    print(f"  Recovery Factor: {metrics.get('recovery_factor', 0):.2f}")
    
    print(f"\n📈 Trade Statistics:")
    print(f"  Total Trades: {metrics.get('total_trades', 0)}")
    print(f"  Win Rate: {metrics.get('win_rate', 0):.2f}%")
    print(f"  Profit Factor: {metrics.get('profit_factor', 0):.2f}")
    
    print(f"\n🎯 Advanced Metrics:")
    print(f"  Calmar Ratio: {metrics.get('calmar_ratio', 0):.2f}")
    
    print("\n" + "="*60)
    
    # Create visualizations
    print("\n📊 Generating charts...")
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
    run_real_backtest()
