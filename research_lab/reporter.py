"""
Reporter Module

Handles batch processing of stocks, runs the Walk-Forward Optimization,
and saves the "Golden Parameters" and performance reports.
"""

import pandas as pd
import json
import os
from typing import List, Dict
from .backtest_pipeline import WalkForwardOptimizer
from .data_loader import DataLoader

class Reporter:
    def __init__(self, output_dir: str = "research_lab/results"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.loader = DataLoader()

    def get_nifty50_stocks(self) -> List[str]:
        """
        Returns a list of Nifty 50 stocks.
        For now, we'll return a subset or filter from master_mapping.
        """
        # Filter master mapping for Large Cap or Nifty 50 sector
        # This is a heuristic. Ideally we have a specific list.
        # Let's pick top 5 liquid stocks for the demo run to be quick.
        return ["RELIANCE", "HDFCBANK", "INFY", "TCS", "ICICIBANK"]

    def run_batch(self, symbols: List[str] = None):
        """
        Run optimization for a list of symbols.
        """
        if symbols is None:
            symbols = self.get_nifty50_stocks()
            
        all_results = []
        all_params = {}
        
        print(f"Starting Batch Run for {len(symbols)} stocks...")
        
        for symbol in symbols:
            print(f"\nProcessing {symbol}...")
            try:
                optimizer = WalkForwardOptimizer(symbol)
                stats, best_params = optimizer.run_pipeline()
                
                # Store Stats
                # Convert Series to dict for easier handling
                stats_dict = stats.to_dict()
                stats_dict['Symbol'] = symbol
                all_results.append(stats_dict)
                
                # Store Params
                # Convert numpy types to python types for JSON serialization
                serializable_params = {}
                for regime, params in best_params.items():
                    # Regime is now a string (e.g., "M0_S1_I2")
                    serializable_params[str(regime)] = [float(p) if isinstance(p, (float, int)) else p for p in params]
                    
                all_params[symbol] = serializable_params
                
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                import traceback
                traceback.print_exc()
                
        # Save Results
        self.save_results(all_results, all_params)
        
    def save_results(self, results: List[Dict], params: Dict):
        """Save results to CSV and JSON"""
        # 1. Performance Report
        if results:
            df = pd.DataFrame(results)
            # Reorder columns to put Symbol first
            cols = ['Symbol'] + [c for c in df.columns if c != 'Symbol']
            df = df[cols]
            
            csv_path = os.path.join(self.output_dir, "performance_report.csv")
            df.to_csv(csv_path, index=False)
            print(f"\nPerformance Report saved to: {csv_path}")
            
        # 2. Best Params (The "Golden Rules")
        json_path = os.path.join(self.output_dir, "best_params.json")
        
        # We need to ensure all data is JSON serializable
        # (Already handled in the loop, but double check)
        
        with open(json_path, 'w') as f:
            json.dump(params, f, indent=4)
            
        print(f"Best Parameters saved to: {json_path}")

if __name__ == "__main__":
    reporter = Reporter()
    reporter.run_batch()
