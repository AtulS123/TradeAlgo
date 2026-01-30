"""
Walk-Forward Regime-Conditional Optimization (WFRCO) Pipeline

The "Rolling Time Machine" that:
1. Trains Regime Model on Rolling Window
2. Optimizes Strategies per Regime using GA
3. Tests on Out-of-Sample Window
"""

import vectorbt as vbt
import pandas as pd
import numpy as np
import pygad
from research_lab.data_loader import DataLoader
from research_lab.market_regime import RegimeEngine
from research_lab.vectorized_logic import *
from config.costs import CostModel, InstrumentType, MarketCap

class WalkForwardOptimizer:
    def __init__(self, symbol: str, train_window_months: int = 12, test_window_months: int = 1):
        self.symbol = symbol
        self.train_window = train_window_months
        self.test_window = test_window_months
        self.loader = DataLoader()
        self.regime_engine = RegimeEngine()
        
        # Load Data
        self.data = self.loader.load_stock_data(symbol, timeframe='15m') # Default 15m
        self.macro_data = self.loader.load_macro_data("NIFTY 50") # Placeholder
        
        # Get Cap Category for Costs
        self.cap_map = self.loader.get_stock_cap_map()
        cap_str = self.cap_map.get(symbol, "Small Cap").replace(" ", "").upper()
        if cap_str == "LARGECAP":
            self.cap_category = MarketCap.NIFTY50
        elif cap_str == "MIDCAP":
            self.cap_category = MarketCap.MIDCAP
        else:
            self.cap_category = MarketCap.SMALLCAP

    def fitness_func(self, ga_instance, solution, solution_idx):
        """
        GA Fitness Function: Maximize Net Sortino Ratio
        Params: [StrategyType, Param1, Param2, SL, TP]
        """
        # Decode Genes
        strat_type = int(solution[0]) # 0-4 mapping to strategies
        p1, p2 = solution[1], solution[2]
        sl, tp = solution[3], solution[4]
        
        # Run Strategy
        entries, exits = self._run_strategy_logic(strat_type, p1, p2)
        
        # Simulate Portfolio with Costs
        pf = vbt.Portfolio.from_signals(
            self.current_close,
            entries,
            exits,
            sl_stop=sl,
            tp_stop=tp,
            freq='15T',
            fees=0.0, # We calculate net pnl manually or use slippage approx
            slippage=CostModel.SLIPPAGE_RATES[self.cap_category] # Use vbt slippage for approx
        )
        
        # Calculate Sortino
        return pf.sortino_ratio()

    def _run_strategy_logic(self, strat_type, p1, p2):
        """Helper to run specific strategy based on ID"""
        c = self.current_close
        h = self.current_high
        l = self.current_low
        v = self.current_volume
        
        if strat_type == 0: # VWAP
            return vwap_trend_signals(c, h, l, v)
        elif strat_type == 1: # EMA
            return ema_alignment_signals(c, fast_period=int(p1), slow_period=int(p2))
        elif strat_type == 2: # ORB
            return orb_signals(h, l, c, self.current_time, orb_minutes=int(p1))
        elif strat_type == 3: # Structure
            return structure_shift_signals(h, l, c, lookback=int(p1))
        elif strat_type == 4: # Mean Rev
            return mean_reversion_signals(c, rsi_period=int(p1), bb_std=p2)
        else:
            return pd.Series(False, index=c.index), pd.Series(False, index=c.index)

    def run_pipeline(self):
        """Execute the Rolling Walk-Forward Optimization with Multi-Factor Regimes"""
        print(f"Starting Multi-Factor WFRCO for {self.symbol}...")
        
        # 1. Load Data Sources
        # A. Stock Data
        stock_data = self.data
        
        # B. Sector Data
        sector_map = self.loader.get_stock_sector_map()
        sector = sector_map.get(self.symbol, "NIFTY 50")
        print(f"Sector: {sector}")
        try:
            sector_data = self.loader.load_macro_data(sector)
        except:
            sector_data = self.loader.load_macro_data("NIFTY 50")
            
        # C. Market Data (Nifty 50)
        try:
            market_data = self.loader.load_macro_data("NIFTY 50")
        except:
            market_data = sector_data # Fallback
            
        # 2. Align Data (Intersection of all 3)
        common_start = max(stock_data.index.min(), sector_data.index.min(), market_data.index.min())
        common_end = min(stock_data.index.max(), sector_data.index.max(), market_data.index.max())
        
        stock_data = stock_data.loc[common_start:common_end]
        sector_data = sector_data.loc[common_start:common_end]
        market_data = market_data.loc[common_start:common_end]
        
        # Reindex to match stock timestamps exactly (ffill macro data)
        sector_data = sector_data.reindex(stock_data.index, method='ffill').dropna()
        market_data = market_data.reindex(stock_data.index, method='ffill').dropna()
        stock_data = stock_data.loc[market_data.index] # Align back
        
        self.data = stock_data # Update self.data
        
        # 3. Train 3 Separate HMMs (3 States each: Bull, Bear, Sideways)
        # Split Train/Test
        split_idx = int(len(stock_data) * 0.8)
        
        train_stock = stock_data.iloc[:split_idx]
        train_sector = sector_data.iloc[:split_idx]
        train_market = market_data.iloc[:split_idx]
        
        test_stock = stock_data.iloc[split_idx:]
        test_sector = sector_data.iloc[split_idx:]
        test_market = market_data.iloc[split_idx:]
        
        print("Training Market HMM...")
        hmm_market = RegimeEngine(n_states=3)
        hmm_market.train(train_market)
        
        print("Training Sector HMM...")
        hmm_sector = RegimeEngine(n_states=3)
        hmm_sector.train(train_sector)
        
        print("Training Stock HMM...")
        hmm_stock = RegimeEngine(n_states=3)
        hmm_stock.train(train_stock)
        
        # 4. Predict Regimes & Create Composite State
        # Train Regimes
        r_market = hmm_market.predict(train_market)
        r_sector = hmm_sector.predict(train_sector)
        r_stock = hmm_stock.predict(train_stock)
        
        # Create Composite Key: "M{}_S{}_I{}" (Market, Sector, Individual)
        train_regimes = "M" + r_market.astype(str) + "_S" + r_sector.astype(str) + "_I" + r_stock.astype(str)
        
        # 5. Optimize per Composite Regime
        best_params_per_regime = {}
        unique_regimes = train_regimes.unique()
        
        print(f"Found {len(unique_regimes)} unique composite regimes in training data.")
        
        for regime in unique_regimes:
            # Filter data for this regime
            regime_mask = (train_regimes == regime)
            count = regime_mask.sum()
            
            if count < 50: # Minimum bars required to be significant
                # print(f"Skipping Regime {regime} (Only {count} bars)")
                continue
                
            print(f"Optimizing for Regime {regime} ({count} bars)...")
            
            self.current_regime_mask = regime_mask
            self.current_close = train_stock['close']
            self.current_high = train_stock['high']
            self.current_low = train_stock['low']
            self.current_volume = train_stock['volume']
            self.current_time = train_stock.index
            
            # GA Setup (Same as before)
            ga_instance = pygad.GA(
                num_generations=5, 
                num_parents_mating=2,
                fitness_func=self.fitness_func,
                sol_per_pop=5,
                num_genes=5,
                gene_space=[
                    range(0, 5), # Strategy Type
                    range(5, 50), # Period
                    {'low': 1.0, 'high': 4.0}, # Multiplier
                    {'low': 0.005, 'high': 0.05}, # SL
                    {'low': 0.01, 'high': 0.10}   # TP
                ],
                suppress_warnings=True
            )
            
            ga_instance.run()
            best_solution, best_fitness, _ = ga_instance.best_solution()
            best_params_per_regime[regime] = best_solution
            
        # 6. Forward Test with Composite Regimes
        print("\nRunning Forward Test...")
        
        # Predict Test Regimes
        tr_market = hmm_market.predict(test_market)
        tr_sector = hmm_sector.predict(test_sector)
        tr_stock = hmm_stock.predict(test_stock)
        
        test_regimes = "M" + tr_market.astype(str) + "_S" + tr_sector.astype(str) + "_I" + tr_stock.astype(str)
        
        final_entries = pd.Series(False, index=test_stock.index)
        final_exits = pd.Series(False, index=test_stock.index)
        
        # Apply strategies for known regimes
        # For unknown regimes, we do nothing (Flat)
        
        for regime, params in best_params_per_regime.items():
            # Get mask for this regime in Test Data
            regime_mask = (test_regimes == regime)
            
            if regime_mask.sum() == 0:
                continue
                
            # Run strategy logic
            self.current_close = test_stock['close']
            self.current_high = test_stock['high']
            self.current_low = test_stock['low']
            self.current_volume = test_stock['volume']
            self.current_time = test_stock.index
            
            entries, exits = self._run_strategy_logic(int(params[0]), params[1], params[2])
            
            # Apply signals only where regime matches
            final_entries = final_entries | (entries & regime_mask)
            final_exits = final_exits | (exits & regime_mask)
            
        # Simulate Final Portfolio
        pf = vbt.Portfolio.from_signals(
            test_stock['close'],
            final_entries,
            final_exits,
            freq='15T',
            fees=0.0,
            slippage=CostModel.SLIPPAGE_RATES[self.cap_category]
        )
        
        print("\n--- Walk-Forward Results ---")
        print(f"Total Return: {pf.total_return():.2%}")
        print(f"Sharpe Ratio: {pf.sharpe_ratio():.2f}")
        print(f"Sortino Ratio: {pf.sortino_ratio():.2f}")
        print(f"Max Drawdown: {pf.max_drawdown():.2%}")
        
        return pf.stats(), best_params_per_regime

if __name__ == "__main__":
    # Test
    # optimizer = WalkForwardOptimizer("RELIANCE")
    pass
