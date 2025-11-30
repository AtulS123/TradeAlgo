"""
Trend following indicators
"""

import pandas as pd
import numpy as np
from typing import Union, Optional


def SMA(data: Union[pd.Series, np.ndarray], period: int = 20) -> pd.Series:
    """
    Simple Moving Average
    
    Args:
        data: Price data
        period: Period for SMA
        
    Returns:
        SMA values
    """
    return pd.Series(data).rolling(window=period).mean()


def EMA(data: Union[pd.Series, np.ndarray], period: int = 20) -> pd.Series:
    """
    Exponential Moving Average
    
    Args:
        data: Price data
        period: Period for EMA
        
    Returns:
        EMA values
    """
    return pd.Series(data).ewm(span=period, adjust=False).mean()


def DEMA(data: Union[pd.Series, np.ndarray], period: int = 20) -> pd.Series:
    """
    Double Exponential Moving Average
    
    Args:
        data: Price data
        period: Period for DEMA
        
    Returns:
        DEMA values
    """
    ema1 = EMA(data, period)
    ema2 = EMA(ema1, period)
    return 2 * ema1 - ema2


def HMA(data: Union[pd.Series, np.ndarray], period: int = 20) -> pd.Series:
    """
    Hull Moving Average
    
    Args:
        data: Price data
        period: Period for HMA
        
    Returns:
        HMA values
    """
    half_period = int(period / 2)
    sqrt_period = int(np.sqrt(period))
    
    wma_half = pd.Series(data).rolling(window=half_period).mean()
    wma_full = pd.Series(data).rolling(window=period).mean()
    
    raw_hma = 2 * wma_half - wma_full
    return raw_hma.rolling(window=sqrt_period).mean()


def MACD(
    data: Union[pd.Series, np.ndarray],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> tuple:
    """
    Moving Average Convergence Divergence
    
    Args:
        data: Price data
        fast_period: Fast EMA period
        slow_period: Slow EMA period
        signal_period: Signal line period
        
    Returns:
        Tuple of (MACD line, Signal line, Histogram)
    """
    fast_ema = EMA(data, fast_period)
    slow_ema = EMA(data, slow_period)
    
    macd_line = fast_ema - slow_ema
    signal_line = EMA(macd_line, signal_period)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def ADX(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Average Directional Index
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Period for ADX
        
    Returns:
        ADX values
    """
    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    # Calculate Directional Movement
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    plus_dm = pd.Series(plus_dm, index=high.index).rolling(window=period).mean()
    minus_dm = pd.Series(minus_dm, index=high.index).rolling(window=period).mean()
    
    # Calculate Directional Indicators
    plus_di = 100 * (plus_dm / atr)
    minus_di = 100 * (minus_dm / atr)
    
    # Calculate ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    
    return adx


def Supertrend(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 10,
    multiplier: float = 3.0
) -> tuple:
    """
    Supertrend Indicator (popular in Indian markets)
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ATR period
        multiplier: ATR multiplier
        
    Returns:
        Tuple of (Supertrend, Direction)
    """
    # Calculate ATR
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    # Calculate basic bands
    hl_avg = (high + low) / 2
    upper_band = hl_avg + (multiplier * atr)
    lower_band = hl_avg - (multiplier * atr)
    
    # Initialize
    supertrend = pd.Series(index=close.index, dtype=float)
    direction = pd.Series(index=close.index, dtype=int)
    
    supertrend.iloc[0] = upper_band.iloc[0]
    direction.iloc[0] = 1
    
    # Calculate Supertrend
    for i in range(1, len(close)):
        if close.iloc[i] > supertrend.iloc[i-1]:
            supertrend.iloc[i] = lower_band.iloc[i]
            direction.iloc[i] = 1
        elif close.iloc[i] < supertrend.iloc[i-1]:
            supertrend.iloc[i] = upper_band.iloc[i]
            direction.iloc[i] = -1
        else:
            supertrend.iloc[i] = supertrend.iloc[i-1]
            direction.iloc[i] = direction.iloc[i-1]
    
    return supertrend, direction


def ParabolicSAR(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    af_start: float = 0.02,
    af_increment: float = 0.02,
    af_max: float = 0.2
) -> pd.Series:
    """
    Parabolic SAR
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        af_start: Starting acceleration factor
        af_increment: AF increment
        af_max: Maximum AF
        
    Returns:
        SAR values
    """
    sar = pd.Series(index=close.index, dtype=float)
    trend = pd.Series(index=close.index, dtype=int)
    af = af_start
    ep = high.iloc[0]
    
    sar.iloc[0] = low.iloc[0]
    trend.iloc[0] = 1
    
    for i in range(1, len(close)):
        if trend.iloc[i-1] == 1:  # Uptrend
            sar.iloc[i] = sar.iloc[i-1] + af * (ep - sar.iloc[i-1])
            
            if low.iloc[i] < sar.iloc[i]:
                trend.iloc[i] = -1
                sar.iloc[i] = ep
                ep = low.iloc[i]
                af = af_start
            else:
                trend.iloc[i] = 1
                if high.iloc[i] > ep:
                    ep = high.iloc[i]
                    af = min(af + af_increment, af_max)
        else:  # Downtrend
            sar.iloc[i] = sar.iloc[i-1] - af * (sar.iloc[i-1] - ep)
            
            if high.iloc[i] > sar.iloc[i]:
                trend.iloc[i] = 1
                sar.iloc[i] = ep
                ep = high.iloc[i]
                af = af_start
            else:
                trend.iloc[i] = -1
                if low.iloc[i] < ep:
                    ep = low.iloc[i]
                    af = min(af + af_increment, af_max)
    
    return sar


def Aroon(high: pd.Series, low: pd.Series, period: int = 25) -> tuple:
    """
    Aroon Indicator
    
    Args:
        high: High prices
        low: Low prices
        period: Period for Aroon
        
    Returns:
        Tuple of (Aroon Up, Aroon Down, Aroon Oscillator)
    """
    aroon_up = pd.Series(index=high.index, dtype=float)
    aroon_down = pd.Series(index=low.index, dtype=float)
    
    for i in range(period, len(high)):
        high_idx = high.iloc[i-period:i+1].idxmax()
        low_idx = low.iloc[i-period:i+1].idxmin()
        
        periods_since_high = i - high.index.get_loc(high_idx)
        periods_since_low = i - low.index.get_loc(low_idx)
        
        aroon_up.iloc[i] = ((period - periods_since_high) / period) * 100
        aroon_down.iloc[i] = ((period - periods_since_low) / period) * 100
    
    aroon_oscillator = aroon_up - aroon_down
    
    return aroon_up, aroon_down, aroon_oscillator


def IchimokuCloud(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    tenkan_period: int = 9,
    kijun_period: int = 26,
    senkou_b_period: int = 52
) -> dict:
    """
    Ichimoku Cloud
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        tenkan_period: Tenkan-sen period
        kijun_period: Kijun-sen period
        senkou_b_period: Senkou Span B period
        
    Returns:
        Dictionary with all Ichimoku components
    """
    # Tenkan-sen (Conversion Line)
    tenkan_high = high.rolling(window=tenkan_period).max()
    tenkan_low = low.rolling(window=tenkan_period).min()
    tenkan_sen = (tenkan_high + tenkan_low) / 2
    
    # Kijun-sen (Base Line)
    kijun_high = high.rolling(window=kijun_period).max()
    kijun_low = low.rolling(window=kijun_period).min()
    kijun_sen = (kijun_high + kijun_low) / 2
    
    # Senkou Span A (Leading Span A)
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun_period)
    
    # Senkou Span B (Leading Span B)
    senkou_high = high.rolling(window=senkou_b_period).max()
    senkou_low = low.rolling(window=senkou_b_period).min()
    senkou_span_b = ((senkou_high + senkou_low) / 2).shift(kijun_period)
    
    # Chikou Span (Lagging Span)
    chikou_span = close.shift(-kijun_period)
    
    return {
        'tenkan_sen': tenkan_sen,
        'kijun_sen': kijun_sen,
        'senkou_span_a': senkou_span_a,
        'senkou_span_b': senkou_span_b,
        'chikou_span': chikou_span
    }


def LinearRegression(data: Union[pd.Series, np.ndarray], period: int = 20) -> pd.Series:
    """
    Linear Regression
    
    Args:
        data: Price data
        period: Period for regression
        
    Returns:
        Linear regression values
    """
    result = pd.Series(index=pd.Series(data).index, dtype=float)
    
    for i in range(period - 1, len(data)):
        y = pd.Series(data).iloc[i-period+1:i+1].values
        x = np.arange(len(y))
        
        # Linear regression
        slope, intercept = np.polyfit(x, y, 1)
        result.iloc[i] = slope * (period - 1) + intercept
    
    return result
