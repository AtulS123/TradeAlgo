from typing import Optional, Dict
import pandas as pd
from indicators.volatility import ATR

class ATRTrailingStopMixin:
    """
    ATR Trailing Stop (The "Chandelier")
    
    Rule: Set a trailing stop at Highest Price - (3.0 * ATR).
    """
    
    def init_trailing_stop(self, atr_period=14, atr_multiplier=3.0):
        self.ts_atr_period = atr_period
        self.ts_atr_multiplier = atr_multiplier
        self.highest_prices = {} # Track highest price since entry per symbol
        
    def update_trailing_stop(self, symbol: str, current_price: float, entry_price: float, side: int) -> Optional[float]:
        """
        Calculate the current trailing stop price.
        Returns None if not enough data.
        """
        if symbol not in self.data:
            return None
            
        df = self.data[symbol]
        if len(df) < self.ts_atr_period:
            return None
            
        # Calculate ATR
        # Note: In a real loop, we'd cache this or calculate incrementally
        atr_series = ATR(df['high'], df['low'], df['close'], self.ts_atr_period)
        current_atr = atr_series.iloc[self.current_bar[symbol]]
        
        # Update highest price for Longs (or lowest for Shorts)
        if symbol not in self.highest_prices:
            self.highest_prices[symbol] = entry_price
            
        if side == 1: # Long
            if current_price > self.highest_prices[symbol]:
                self.highest_prices[symbol] = current_price
            
            stop_price = self.highest_prices[symbol] - (self.ts_atr_multiplier * current_atr)
            return stop_price
            
        elif side == -1: # Short
            # For shorts, we track lowest price
            # Initialize if needed (reuse variable name for simplicity but logic differs)
            if self.highest_prices[symbol] == entry_price: # First run check
                 self.highest_prices[symbol] = entry_price # Reset to entry
            
            # Actually, let's use a separate tracker or rename for clarity if we support shorts
            # For now assuming 'highest_prices' stores the extreme favorable price
            if current_price < self.highest_prices[symbol]:
                self.highest_prices[symbol] = current_price
                
            stop_price = self.highest_prices[symbol] + (self.ts_atr_multiplier * current_atr)
            return stop_price
            
        return None
