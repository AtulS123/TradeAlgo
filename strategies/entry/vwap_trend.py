from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from core.strategy import Strategy
from indicators.volume import VWAP
from utils.logger import logger

class VWAPTrendStrategy(Strategy):
    """
    The VWAP "Check-Back" (Trend Continuation) Strategy
    
    Rules:
    - Trend Filter: Price must be above VWAP for > 15 minutes (3 bars on 5-min chart).
    - Trigger: Price touches the VWAP line but does not close below it. 
      Enter Long when the next candle closes higher than the "touch" candle's high.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vwap_period = 20 # Not strictly used for standard VWAP but kept for consistency if needed
        self.trend_bars = 3
        self.touch_candle = {} # Store the candle that touched VWAP
        
    def on_data(self, symbol: str, bar: pd.Series):
        # Calculate indicators if not already done for this bar
        # In a real system, this might be handled by an event loop or data processor
        # Here we assume we have access to the full history up to this bar
        pass

    def generate_signals(self) -> Dict[str, int]:
        signals = {}
        
        for symbol in self.symbols:
            if symbol not in self.data:
                continue
                
            df = self.data[symbol]
            if len(df) < 20:
                continue
                
            # Calculate VWAP
            # Note: Standard VWAP resets daily. 
            # For simplicity here, we'll use the VWAP function which accumulates.
            # In a production intraday system, ensure VWAP resets at market open.
            vwap = VWAP(df['high'], df['low'], df['close'], df['volume'])
            
            curr_idx = self.current_bar[symbol]
            if curr_idx < self.trend_bars + 1:
                continue
                
            # Get recent data
            current_close = df['close'].iloc[curr_idx]
            current_high = df['high'].iloc[curr_idx]
            current_low = df['low'].iloc[curr_idx]
            current_vwap = vwap.iloc[curr_idx]
            
            prev_close = df['close'].iloc[curr_idx-1]
            prev_high = df['high'].iloc[curr_idx-1]
            prev_low = df['low'].iloc[curr_idx-1]
            prev_vwap = vwap.iloc[curr_idx-1]
            
            # Check for existing position to manage exits (if integrated) or ignore
            if self.get_position(symbol) > 0:
                signals[symbol] = 0
                continue

            # Logic
            # 1. Trend Filter: Price above VWAP for previous N bars (excluding the touch bar)
            # We need to look back a bit.
            # Let's say we are looking for the trigger NOW.
            # The trigger is: Next candle closes higher than "touch" candle's high.
            # So we need to identify if we had a "touch" candle recently.
            
            # Let's simplify state management:
            # We check if the PREVIOUS candle was a "touch" candle.
            # And if the bars BEFORE that were above VWAP.
            
            is_touch = (prev_low <= prev_vwap) and (prev_close >= prev_vwap)
            
            if is_touch:
                # Check trend before the touch
                trend_confirmed = True
                for i in range(2, self.trend_bars + 2):
                    if df['close'].iloc[curr_idx-i] < vwap.iloc[curr_idx-i]:
                        trend_confirmed = False
                        break
                
                if trend_confirmed:
                    # We found a valid touch. Now check if CURRENT bar triggers entry.
                    # Trigger: Close higher than touch candle's high
                    if current_close > prev_high:
                        signals[symbol] = 1
                        logger.info(f"{symbol}: VWAP Check-Back Triggered. Close {current_close} > Prev High {prev_high}")
            
            # Note: This logic assumes the trigger happens immediately after the touch.
            # The requirement says "Enter Long when the next candle closes higher".
            # If it takes multiple candles, we'd need more complex state tracking.
            # For this implementation, we'll stick to the immediate next candle.

        return signals
