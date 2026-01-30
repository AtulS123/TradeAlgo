from typing import Dict, List, Optional
import pandas as pd
from core.strategy import Strategy
from indicators.volatility import BollingerBands
from indicators.momentum import RSI
from utils.logger import logger

class RSIBollingerStrategy(Strategy):
    """
    RSI + Bollinger Band Extremes (Mean Reversion)
    
    Rules:
    - Setup: Bollinger Bands (Length 20, StdDev 2.5) and RSI (Length 14).
    - Trigger (Short): Price touches the Upper Band AND RSI > 75.
    - Trigger (Long): Price touches the Lower Band AND RSI < 25.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bb_period = 20
        self.bb_std = 2.5
        self.rsi_period = 14
        self.rsi_overbought = 75
        self.rsi_oversold = 25
        
    def generate_signals(self) -> Dict[str, int]:
        signals = {}
        
        for symbol in self.symbols:
            if symbol not in self.data:
                continue
                
            df = self.data[symbol]
            if len(df) < 20:
                continue
                
            curr_idx = self.current_bar[symbol]
            
            # Calculate Indicators
            upper, middle, lower = BollingerBands(df['close'], self.bb_period, self.bb_std)
            rsi = RSI(df['close'], self.rsi_period)
            
            curr_close = df['close'].iloc[curr_idx]
            curr_high = df['high'].iloc[curr_idx]
            curr_low = df['low'].iloc[curr_idx]
            curr_rsi = rsi.iloc[curr_idx]
            curr_upper = upper.iloc[curr_idx]
            curr_lower = lower.iloc[curr_idx]
            
            # Trigger (Short)
            # Price touches Upper Band (High >= Upper) AND RSI > 75
            if curr_high >= curr_upper and curr_rsi > self.rsi_overbought:
                signals[symbol] = -1
                logger.info(f"{symbol}: Mean Reversion SHORT. High {curr_high} >= BB Upper {curr_upper}, RSI {curr_rsi}")
                
            # Trigger (Long)
            # Price touches Lower Band (Low <= Lower) AND RSI < 25
            elif curr_low <= curr_lower and curr_rsi < self.rsi_oversold:
                signals[symbol] = 1
                logger.info(f"{symbol}: Mean Reversion LONG. Low {curr_low} <= BB Lower {curr_lower}, RSI {curr_rsi}")

        return signals
