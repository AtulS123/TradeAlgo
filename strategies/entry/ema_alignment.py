from typing import Dict, List, Optional
import pandas as pd
from core.strategy import Strategy
from indicators.trend import EMA
from utils.logger import logger

class MultiTimeframeEMAStrategy(Strategy):
    """
    Multi-Timeframe EMA Alignment (The "Royal Flush")
    
    Rules:
    - Filter (1-Hour Chart): Price must be above the 20 EMA.
    - Trigger (5-Minute Chart): Enter Long when the 9 EMA crosses above the 21 EMA.
    - Constraint: If the 1-Hour is bearish, ignore all 5-minute buy signals.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ema_fast = 9
        self.ema_slow = 21
        self.htf_ema_period = 20
        # In a real system, we'd need a way to access HTF data.
        # For this implementation, we will assume self.data contains 5-min data
        # and we will resample it to 1-hour to check the filter.
        
    def generate_signals(self) -> Dict[str, int]:
        signals = {}
        
        for symbol in self.symbols:
            if symbol not in self.data:
                continue
                
            df = self.data[symbol]
            if len(df) < 100: # Need enough data for resampling
                continue
                
            curr_idx = self.current_bar[symbol]
            
            # 1. HTF Filter (1-Hour)
            # Resample to 1H. Assuming data is 5min.
            # We need to be careful about lookahead bias. We should only use data up to current time.
            current_time = df.index[curr_idx]
            
            # Slice data up to current time
            history = df.iloc[:curr_idx+1].copy()
            
            # Resample to 1H
            # Note: This can be expensive to do every bar. Optimized systems maintain separate HTF series.
            htf_df = history.resample('1h').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            if len(htf_df) < self.htf_ema_period:
                continue
                
            htf_ema = EMA(htf_df['close'], self.htf_ema_period)
            
            # Check if latest HTF close is above HTF EMA
            # We use the last completed hour or the current forming hour?
            # Usually "Price must be above" implies the current state.
            if htf_df['close'].iloc[-1] <= htf_ema.iloc[-1]:
                # HTF is bearish or neutral, ignore signals
                continue
                
            # 2. LTF Trigger (5-Minute)
            ema_9 = EMA(df['close'], self.ema_fast)
            ema_21 = EMA(df['close'], self.ema_slow)
            
            # Check for crossover
            # Current 9 > 21 AND Previous 9 <= 21
            curr_9 = ema_9.iloc[curr_idx]
            curr_21 = ema_21.iloc[curr_idx]
            prev_9 = ema_9.iloc[curr_idx-1]
            prev_21 = ema_21.iloc[curr_idx-1]
            
            if curr_9 > curr_21 and prev_9 <= prev_21:
                signals[symbol] = 1
                logger.info(f"{symbol}: EMA Alignment Triggered. HTF Bullish & LTF Crossover.")
                
        return signals
