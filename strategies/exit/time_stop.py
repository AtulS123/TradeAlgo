from typing import Dict

class TimeStopMixin:
    """
    The "N-Bar" Time Stop (The Stale Exit)
    
    Rule: If the trade is not profitable after 6 bars, close it immediately.
    """
    
    def init_time_stop(self, bars_limit=6):
        self.time_stop_limit = bars_limit
        self.entry_bars = {} # Track bar index of entry
        
    def check_time_stop(self, symbol: str, current_bar_idx: int, entry_price: float, current_price: float, side: int) -> bool:
        """
        Check if time stop is triggered.
        Returns True if should exit.
        """
        if symbol not in self.entry_bars:
            self.entry_bars[symbol] = current_bar_idx
            return False
            
        bars_held = current_bar_idx - self.entry_bars[symbol]
        
        if bars_held >= self.time_stop_limit:
            # Check profitability
            is_profitable = False
            if side == 1: # Long
                is_profitable = current_price > entry_price
            elif side == -1: # Short
                is_profitable = current_price < entry_price
                
            if not is_profitable:
                return True
                
        return False
        
    def reset_time_stop(self, symbol: str):
        if symbol in self.entry_bars:
            del self.entry_bars[symbol]
