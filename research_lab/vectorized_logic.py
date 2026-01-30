"""
Vectorized Strategy Logic

Implements the 5 core strategies using vectorbt for high-performance backtesting.
All functions accept pandas Series/DataFrames and return boolean signal Series.
"""

import vectorbt as vbt
import pandas as pd
import numpy as np

# 1. VWAP Trend
def vwap_trend_signals(close, high, low, volume, vwap_anchor='D'):
    """
    Signal: Close > VWAP AND Close > EMA(Close, 20) (Trend Filter)
    Note: Standard VWAP calculation requires intraday data.
    """
    # Calculate VWAP manually (Cumulative(Price * Vol) / Cumulative(Vol))
    # Resetting daily is complex in vectorized without time grouping
    # Approximation: Rolling VWAP or just typical price * vol / vol
    
    typical_price = (high + low + close) / 3
    tp_v = typical_price * volume
    cum_tp_v = tp_v.cumsum()
    cum_vol = volume.cumsum()
    vwap = cum_tp_v / cum_vol
    
    # Trend Filter
    ema_20 = vbt.MA.run(close, window=20, ewm=True).ma
    
    entries = (close > vwap) & (close > ema_20)
    exits = (close < vwap)
    return entries, exits

# 2. EMA Alignment (Royal Flush)
def ema_alignment_signals(close, fast_period=9, slow_period=21, trend_period=200):
    """
    Signal: Fast EMA > Slow EMA AND Close > 200 EMA
    """
    ema_fast = vbt.MA.run(close, window=fast_period, ewm=True).ma
    ema_slow = vbt.MA.run(close, window=slow_period, ewm=True).ma
    ema_trend = vbt.MA.run(close, window=trend_period, ewm=True).ma
    
    entries = (ema_fast > ema_slow) & (close > ema_trend) & (ema_fast.shift(1) <= ema_slow.shift(1)) # Crossover
    exits = (ema_fast < ema_slow)
    return entries, exits

# 3. ORB (Opening Range Breakout)
def orb_signals(high, low, close, time_index, orb_minutes=15):
    """
    Signal: Close > High of first 15 mins
    """
    # Identify session start (assuming 09:15)
    # This logic is complex in vectorized form without specific time index manipulation
    # Simplified: Get max high of first N bars of the day
    
    # Extract time
    times = time_index.time
    # Mask for ORB period (e.g., 09:15 to 09:30)
    # This requires the index to be DatetimeIndex
    
    # Placeholder for vectorized ORB - usually requires resampling or groupby
    # For now, using a simple breakout logic as proxy
    
    # Proxy: Donchian Channel Breakout of last N bars (where N ~ 15 mins)
    upper = high.rolling(int(orb_minutes)).max()
    lower = low.rolling(int(orb_minutes)).min()
    
    entries = (close > upper.shift(1))
    exits = (close < lower.shift(1))
    return entries, exits

# 4. Structure Shift (Approximation)
def structure_shift_signals(high, low, close, lookback=10):
    """
    Signal: Break of recent Swing High (Higher High)
    """
    # Vectorized Swing High: Max of last N bars
    recent_high = high.rolling(lookback).max()
    recent_low = low.rolling(lookback).min()
    
    entries = (close > recent_high.shift(1))
    exits = (close < recent_low.shift(1))
    return entries, exits

# 5. Mean Reversion (RSI + BB)
def mean_reversion_signals(close, rsi_period=14, rsi_lower=30, rsi_upper=70, bb_period=20, bb_std=2):
    """
    Signal: RSI < 30 AND Close < Lower BB (Oversold)
    """
    rsi = vbt.RSI.run(close, window=rsi_period).rsi
    bb = vbt.BBANDS.run(close, window=bb_period, alpha=bb_std)
    
    entries = (rsi < rsi_lower) & (close < bb.lower)
    exits = (rsi > rsi_upper) | (close > bb.middle) # Exit at overbought or mean
    return entries, exits

def get_exit_signals(entries, close, sl_pct=0.01, tp_pct=0.02):
    """
    Generate exit signals based on SL/TP.
    Note: vbt.Portfolio.from_signals handles SL/TP internally better than generating raw signals.
    This function is for custom logic if needed.
    """
    # vbt handles this, so we might not need explicit signal generation here
    pass
