from typing import Optional
import pandas as pd
from indicators.trend import EMA
from indicators.volume import VWAP

class IndicatorExitMixin:
    """
    Indicator Reversal (The "Signal Flip")
    
    Rules:
    - Trend Trades: Exit if the 9 EMA crosses back below the 21 EMA.
    - Reversion Trades: Exit if price returns to the VWAP line.
    """
    
    def check_ema_exit(self, df: pd.DataFrame, idx: int, side: int) -> bool:
        """
        Check for EMA crossover exit.
        """
        ema_9 = EMA(df['close'], 9)
        ema_21 = EMA(df['close'], 21)
        
        curr_9 = ema_9.iloc[idx]
        curr_21 = ema_21.iloc[idx]
        prev_9 = ema_9.iloc[idx-1]
        prev_21 = ema_21.iloc[idx-1]
        
        if side == 1: # Long
            # Exit if 9 crosses below 21
            if curr_9 < curr_21 and prev_9 >= prev_21:
                return True
        elif side == -1: # Short
            # Exit if 9 crosses above 21
            if curr_9 > curr_21 and prev_9 <= prev_21:
                return True
                
        return False
        
    def check_vwap_exit(self, df: pd.DataFrame, idx: int, side: int) -> bool:
        """
        Check for VWAP return exit.
        """
        vwap = VWAP(df['high'], df['low'], df['close'], df['volume'])
        curr_vwap = vwap.iloc[idx]
        curr_close = df['close'].iloc[idx]
        prev_close = df['close'].iloc[idx-1]
        
        if side == 1: # Long (Reversion from below)
            # Exit if price touches/crosses VWAP from below
            # Assuming we entered below VWAP
            if curr_close >= curr_vwap:
                return True
        elif side == -1: # Short (Reversion from above)
            if curr_close <= curr_vwap:
                return True
                
        return False
