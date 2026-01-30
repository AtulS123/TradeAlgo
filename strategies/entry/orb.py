from typing import Dict, List, Optional
import pandas as pd
from core.strategy import Strategy
from utils.logger import logger

class ORBStrategy(Strategy):
    """
    15-Minute Opening Range Breakout (ORB)
    
    Rules:
    - Setup: Mark the High and Low of the first 15 minutes (9:30–9:45 AM).
    - Trigger: Enter if a 5-minute candle closes outside this range with volume > 110% of average.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orb_start_time = "09:30"
        self.orb_end_time = "09:45"
        self.volume_avg_period = 20
        self.orb_levels = {} # Stores (high, low) for the current day per symbol
        self.current_day = {} # Tracks current day to reset levels
        
    def generate_signals(self) -> Dict[str, int]:
        signals = {}
        
        for symbol in self.symbols:
            if symbol not in self.data:
                continue
                
            df = self.data[symbol]
            curr_idx = self.current_bar[symbol]
            current_time = df.index[curr_idx]
            current_date = current_time.date()
            
            # Reset levels if new day
            if symbol not in self.current_day or self.current_day[symbol] != current_date:
                self.current_day[symbol] = current_date
                self.orb_levels[symbol] = None
            
            # Check if we are past the ORB period
            # We need to parse time. Assuming index is datetime.
            # In pandas, we can compare time objects.
            
            # Define time objects for comparison
            orb_start = pd.Timestamp(f"{current_date} {self.orb_start_time}").time()
            orb_end = pd.Timestamp(f"{current_date} {self.orb_end_time}").time()
            curr_time_val = current_time.time()
            
            # If we are IN the ORB period, we just wait (or accumulate data if we were streaming)
            # Since we have historical data, we can calculate the range once we pass 09:45
            
            if curr_time_val <= orb_end:
                continue
                
            # Calculate ORB levels if not set
            if self.orb_levels[symbol] is None:
                # Get data for the ORB period
                # Slice for today between start and end
                today_mask = (df.index.date == current_date)
                time_mask = (df.index.time >= orb_start) & (df.index.time <= orb_end)
                orb_data = df[today_mask & time_mask]
                
                if orb_data.empty:
                    continue
                    
                orb_high = orb_data['high'].max()
                orb_low = orb_data['low'].min()
                self.orb_levels[symbol] = (orb_high, orb_low)
                logger.info(f"{symbol}: ORB Levels Set. High: {orb_high}, Low: {orb_low}")
            
            # Check for Breakout
            orb_high, orb_low = self.orb_levels[symbol]
            close = df['close'].iloc[curr_idx]
            volume = df['volume'].iloc[curr_idx]
            
            # Volume Filter: > 110% of average
            # Calculate average volume of last N bars
            avg_volume = df['volume'].iloc[curr_idx-self.volume_avg_period:curr_idx].mean()
            
            if volume > (avg_volume * 1.10):
                if close > orb_high:
                    signals[symbol] = 1 # Long Breakout
                    logger.info(f"{symbol}: ORB Breakout LONG. Close {close} > {orb_high}, Vol {volume} > {avg_volume*1.1}")
                # Strategy description only mentioned "Enter" which usually implies Long in this context ("Enter Long when..."), 
                # but ORB can be bi-directional. The user prompt specifically said "Enter Long" for other strategies but just "Enter" here.
                # However, "Best For: Volatile stocks at the market open" usually implies following momentum.
                # I will implement Short as well for completeness, or stick to Long if the user context implies long-only.
                # Looking at other strategies, they are mostly Long. I'll add Short for robustness but comment it out or make it optional?
                # The prompt says "Enter if a 5-minute candle closes outside this range". Outside implies above or below.
                elif close < orb_low:
                    signals[symbol] = -1 # Short Breakout
                    logger.info(f"{symbol}: ORB Breakout SHORT. Close {close} < {orb_low}, Vol {volume} > {avg_volume*1.1}")

        return signals
