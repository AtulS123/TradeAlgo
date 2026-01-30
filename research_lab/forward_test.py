"""
Forward Test Module

Simulates the "Golden Rules" (Best Parameters) on Out-of-Sample data.
"""

import pandas as pd
import numpy as np
import vectorbt as vbt
import json
import os
from research_lab.data_loader import DataLoader
from research_lab.market_regime import RegimeEngine
from research_lab.vectorized_logic import (
    vwap_trend_signals, ema_alignment_signals, orb_signals, 
    structure_shift_signals, mean_reversion_signals
)
from config.costs import CostModel

class ForwardTester:
    def __init__(self, symbol: str, params_file: str = "research_lab/results/best_params.json"):
        self.symbol = symbol
        self.loader = DataLoader()
        self.params_file = params_file
        self.load_params()
        
        # Get Cap Category for Costs
        self.cap_map = self.loader.get_stock_cap_map()
        cap_str = self.cap_map.get(symbol, "Small Cap").replace(" ", "").upper()
        if cap_str == "LARGECAP":
            self.cap_category = "NIFTY50" # String key for CostModel dict
        elif cap_str == "MIDCAP":
            self.cap_category = "MIDCAP"
        else:
            self.cap_category = "SMALLCAP"
            
        # Initialize HMMs
        self.hmm_market = RegimeEngine(n_states=3)
        self.hmm_sector = RegimeEngine(n_states=3)
        self.hmm_stock = RegimeEngine(n_states=3)

    def load_params(self):
        with open(self.params_file, 'r') as f:
            all_params = json.load(f)
        self.best_params = all_params.get(self.symbol, {})
        if not self.best_params:
            print(f"Warning: No parameters found for {self.symbol}")

    def _run_strategy_logic(self, strat_type, p1, p2, close, high, low, volume, time):
        """Helper to run specific strategy based on ID"""
        if strat_type == 0: # VWAP
            return vwap_trend_signals(close, high, low, volume)
        elif strat_type == 1: # EMA
            return ema_alignment_signals(close, fast_period=int(p1), slow_period=int(p2))
        elif strat_type == 2: # ORB
            return orb_signals(high, low, close, time, orb_minutes=int(p1))
        elif strat_type == 3: # Structure
            return structure_shift_signals(high, low, close, lookback=int(p1))
        elif strat_type == 4: # Mean Rev
            return mean_reversion_signals(close, rsi_period=int(p1), bb_std=p2)
        else:
            return pd.Series(False, index=close.index), pd.Series(False, index=close.index)

    def run_test(self):
        print(f"Running Forward Test for {self.symbol}...")
        
        # 1. Load & Align Data (Same logic as Pipeline)
        stock_data = self.loader.load_stock_data(self.symbol)
        sector_map = self.loader.get_stock_sector_map()
        sector = sector_map.get(self.symbol, "NIFTY 50")
        
        try: sector_data = self.loader.load_macro_data(sector)
        except: sector_data = self.loader.load_macro_data("NIFTY 50")
            
        try: market_data = self.loader.load_macro_data("NIFTY 50")
        except: market_data = sector_data

        common_start = max(stock_data.index.min(), sector_data.index.min(), market_data.index.min())
        common_end = min(stock_data.index.max(), sector_data.index.max(), market_data.index.max())
        
        stock_data = stock_data.loc[common_start:common_end]
        sector_data = sector_data.loc[common_start:common_end]
        market_data = market_data.loc[common_start:common_end]
        
        sector_data = sector_data.reindex(stock_data.index, method='ffill').dropna()
        market_data = market_data.reindex(stock_data.index, method='ffill').dropna()
        stock_data = stock_data.loc[market_data.index]
        
        # 2. Split Data (80/20)
        split_idx = int(len(stock_data) * 0.8)
        
        train_stock = stock_data.iloc[:split_idx]
        train_sector = sector_data.iloc[:split_idx]
        train_market = market_data.iloc[:split_idx]
        
        test_stock = stock_data.iloc[split_idx:]
        test_sector = sector_data.iloc[split_idx:]
        test_market = market_data.iloc[split_idx:]
        
        print(f"Training Period: {train_stock.index.min()} to {train_stock.index.max()}")
        print(f"Forward Test Period: {test_stock.index.min()} to {test_stock.index.max()}")
        
        # 3. Train HMMs on Training Data
        self.hmm_market.train(train_market)
        self.hmm_sector.train(train_sector)
        self.hmm_stock.train(train_stock)
        
        # 4. Predict Regimes on Test Data
        tr_market = self.hmm_market.predict(test_market)
        tr_sector = self.hmm_sector.predict(test_sector)
        tr_stock = self.hmm_stock.predict(test_stock)
        
        test_regimes = "M" + tr_market.astype(str) + "_S" + tr_sector.astype(str) + "_I" + tr_stock.astype(str)
        
        # 5. Simulate Trading
        final_entries = pd.Series(False, index=test_stock.index)
        final_exits = pd.Series(False, index=test_stock.index)
        
        for regime, params in self.best_params.items():
            # Get mask for this regime in Test Data
            regime_mask = (test_regimes == regime)
            
            if regime_mask.sum() == 0:
                continue
                
            # Run strategy logic
            entries, exits = self._run_strategy_logic(
                int(params[0]), params[1], params[2],
                test_stock['close'], test_stock['high'], test_stock['low'], test_stock['volume'], test_stock.index
            )
            
            # Apply signals only where regime matches
            final_entries = final_entries | (entries & regime_mask)
            final_exits = final_exits | (exits & regime_mask)
            
        # 6. Portfolio Stats
        # Map Cap Category string to Enum if needed, or just use the string key if CostModel supports it
        # CostModel.SLIPPAGE_RATES is keyed by Enum. We need to fix this.
        from research_lab.backtest_pipeline import MarketCap
        
        cap_enum = MarketCap.SMALLCAP
        if self.cap_category == "NIFTY50": cap_enum = MarketCap.NIFTY50
        elif self.cap_category == "MIDCAP": cap_enum = MarketCap.MIDCAP
            
        pf = vbt.Portfolio.from_signals(
            test_stock['close'],
            final_entries,
            final_exits,
            freq='15T',
            fees=0.0, # We use slippage to approximate costs + impact
            slippage=CostModel.SLIPPAGE_RATES[cap_enum]
        )
        
        return pf

if __name__ == "__main__":
    import sys
    
    # Default to RELIANCE if no arg
    symbol = sys.argv[1] if len(sys.argv) > 1 else "RELIANCE"
    
    tester = ForwardTester(symbol)
    pf = tester.run_test()
    
    print("\n" + "="*40)
    print(f"FORWARD TEST RESULTS: {symbol}")
    print("="*40)
    print(f"Start Date: {pf.wrapper.index[0]}")
    print(f"End Date:   {pf.wrapper.index[-1]}")
    print("-" * 40)
    print(f"Total Return:    {pf.total_return():.2%}")
    print(f"Annual Return:   {pf.annualized_return():.2%}")
    print(f"Sharpe Ratio:    {pf.sharpe_ratio():.2f}")
    print(f"Sortino Ratio:   {pf.sortino_ratio():.2f}")
    print(f"Max Drawdown:    {pf.max_drawdown():.2%}")
    print(f"Win Rate:        {pf.stats()['Win Rate [%]']:.2f}%")
    print(f"Profit Factor:   {pf.stats()['Profit Factor']:.2f}")
    print(f"Total Trades:    {pf.stats()['Total Trades']}")
    print("="*40)
