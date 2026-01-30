from typing import Dict, List, Optional
import pandas as pd
from core.strategy import Strategy
from utils.logger import logger

class StructureShiftStrategy(Strategy):
    """
    Supply/Demand Structure Shift (The "Smart Money" Entry)
    
    Rules:
    - Setup: Identify a downtrend with Lower Highs and Lower Lows.
    - Trigger: Enter Long immediately after a candle closes above the most recent Lower High (breaking the structure).
    - Filter: The breakout candle must be a "marubozu" (full body, small wicks) indicating conviction.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookback = 20 # How far back to look for swing points
        
    def _is_marubozu(self, open_p, close_p, high_p, low_p, threshold=0.1):
        """Check if candle is a marubozu (body is > 90% of range)"""
        total_range = high_p - low_p
        if total_range == 0:
            return False
        body_size = abs(close_p - open_p)
        return (body_size / total_range) >= (1.0 - threshold)
        
    def _find_swing_highs(self, df, idx, n=3):
        """Simple pivot high detection"""
        # A high surrounded by n lower highs on both sides
        # This is expensive to run every bar.
        # Simplified: Find the highest high of the last downtrend leg.
        pass

    def generate_signals(self) -> Dict[str, int]:
        signals = {}
        
        for symbol in self.symbols:
            if symbol not in self.data:
                continue
                
            df = self.data[symbol]
            curr_idx = self.current_bar[symbol]
            if curr_idx < 10:
                continue
                
            # 1. Identify Downtrend (Lower Highs, Lower Lows)
            # We need to find the most recent significant Swing High.
            # Let's look back and find the highest point in the last N bars, 
            # but that's just a high. We need a "Lower High".
            
            # Simplified Logic for "Most Recent Lower High":
            # We look for a local maximum in the recent past that was part of a downtrend.
            # Let's say we look at the last 10 bars.
            # If we see a sequence where highs were generally decreasing, the last peak is our target.
            
            # For this implementation, let's use a rolling max to identify local peaks.
            # Then check if that peak is lower than the previous peak.
            
            # Actually, the rule is "Enter Long ... above the most recent Lower High".
            # This implies we track swing points.
            
            # Let's try a simpler approach for the "Setup":
            # Check if price has been making lower lows recently.
            # Find the max high of the last X bars (e.g., 5 bars) excluding the current breakout bar.
            # If that max high is lower than the max high of the X bars before IT, we have a lower high structure.
            
            # Current candidate for breakout
            close = df['close'].iloc[curr_idx]
            open_p = df['open'].iloc[curr_idx]
            high = df['high'].iloc[curr_idx]
            low = df['low'].iloc[curr_idx]
            
            # Check Marubozu Filter first (cheap check)
            if not self._is_marubozu(open_p, close, high, low):
                continue
                
            # Find recent swing high
            # Look back 3-10 bars
            recent_window = df['high'].iloc[curr_idx-10:curr_idx]
            recent_high = recent_window.max()
            recent_high_idx = recent_window.idxmax()
            
            # Was this a lower high?
            # Look at the window BEFORE that high
            # We need the index integer
            # recent_high_idx is a timestamp if index is datetime.
            # Let's use iloc based indexing for simplicity in logic
            
            # Find max of last 10 bars (excluding current)
            last_10_highs = df['high'].iloc[curr_idx-10:curr_idx].values
            if len(last_10_highs) == 0: continue
            local_high = max(last_10_highs)
            
            # Check if this local high was lower than the high before it (Downtrend structure)
            # Look at bars -20 to -10
            prev_10_highs = df['high'].iloc[curr_idx-20:curr_idx-10].values
            if len(prev_10_highs) == 0: continue
            prev_high = max(prev_10_highs)
            
            if local_high < prev_high:
                # We have a Lower High structure (roughly)
                
                # Trigger: Close above this Lower High
                if close > local_high:
                    signals[symbol] = 1
                    logger.info(f"{symbol}: Structure Shift (MSS). Close {close} > Lower High {local_high}. Marubozu confirmed.")

        return signals
