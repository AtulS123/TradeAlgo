import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from strategies import *
from utils.logger import logger

def generate_synthetic_data(n=200):
    """Generate synthetic OHLCV data"""
    dates = pd.date_range(start=datetime.now() - timedelta(days=1), periods=n, freq='5min')
    
    # Random walk
    close = 100 + np.cumsum(np.random.randn(n))
    high = close + np.abs(np.random.randn(n))
    low = close - np.abs(np.random.randn(n))
    open_p = close + np.random.randn(n) * 0.5
    volume = np.abs(np.random.randn(n) * 10000) + 1000
    
    df = pd.DataFrame({
        'open': open_p,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)
    
    return df

def test_strategies():
    print("Testing Strategies...")
    
    symbol = "TEST_SYM"
    data = generate_synthetic_data(200)
    
    strategies = [
        VWAPTrendStrategy("VWAP Trend", [symbol]),
        MultiTimeframeEMAStrategy("EMA Alignment", [symbol]),
        ORBStrategy("ORB", [symbol]),
        StructureShiftStrategy("Structure Shift", [symbol]),
        RSIBollingerStrategy("Mean Reversion", [symbol])
    ]
    
    for strategy in strategies:
        print(f"\nTesting {strategy.name}...")
        try:
            strategy.set_data(symbol, data)
            
            # Simulate a few bars
            for i in range(150, 200):
                strategy.current_bar[symbol] = i
                signals = strategy.generate_signals()
                if signals:
                    print(f"  Signal generated at bar {i}: {signals}")
            
            print(f"  {strategy.name} OK")
        except Exception as e:
            print(f"  ERROR in {strategy.name}: {e}")
            import traceback
            traceback.print_exc()

def test_exits():
    print("\nTesting Exits...")
    
    class TestExitStrategy(ATRTrailingStopMixin, TimeStopMixin, FixedRiskRewardTargetMixin, BreakEvenStopMixin):
        def __init__(self):
            self.data = {}
            self.current_bar = {}
            self.init_trailing_stop()
            self.init_time_stop()
            self.init_profit_target()
            
    exit_strat = TestExitStrategy()
    symbol = "TEST_EXIT"
    data = generate_synthetic_data(50)
    exit_strat.data[symbol] = data
    exit_strat.current_bar[symbol] = 40
    
    # Test Trailing Stop
    ts = exit_strat.update_trailing_stop(symbol, 105, 100, 1)
    print(f"  Trailing Stop: {ts}")
    
    # Test Time Stop
    should_exit = exit_strat.check_time_stop(symbol, 40, 100, 99, 1) # Just entered
    print(f"  Time Stop (Just Entered): {should_exit}")
    
    exit_strat.entry_bars[symbol] = 30 # Entered 10 bars ago
    should_exit = exit_strat.check_time_stop(symbol, 40, 100, 99, 1) # Loss
    print(f"  Time Stop (10 bars later, Loss): {should_exit}")
    
    # Test Profit Target
    target = exit_strat.get_target_price(100, 98, 1)
    print(f"  Profit Target (Entry 100, Stop 98): {target}")
    
    # Test Break Even
    new_stop = exit_strat.check_breakeven(103, 100, 98, 1) # Profit 3, Risk 2 -> >1R
    print(f"  Break Even (Profit 3, Risk 2): {new_stop}")

if __name__ == "__main__":
    test_strategies()
    test_exits()
