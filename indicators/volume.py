"""
Volume indicators
"""

import pandas as pd
import numpy as np
from typing import Union


def VolumeMA(volume: pd.Series, period: int = 20) -> pd.Series:
    """
    Volume Moving Average
    
    Args:
        volume: Volume data
        period: Period for moving average
        
    Returns:
        Volume MA values
    """
    return volume.rolling(window=period).mean()


def OBV(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    On-Balance Volume
    
    Args:
        close: Close prices
        volume: Volume
        
    Returns:
        OBV values
    """
    obv = pd.Series(index=close.index, dtype=float)
    obv.iloc[0] = volume.iloc[0]
    
    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
        elif close.iloc[i] < close.iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
        else:
            obv.iloc[i] = obv.iloc[i-1]
    
    return obv


def VWAP(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    Volume Weighted Average Price
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume
        
    Returns:
        VWAP values
    """
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    
    return vwap


def VolumeProfile(close: pd.Series, volume: pd.Series, bins: int = 20) -> dict:
    """
    Volume Profile
    
    Args:
        close: Close prices
        volume: Volume
        bins: Number of price bins
        
    Returns:
        Dictionary with price levels and volume
    """
    # Create price bins
    price_min = close.min()
    price_max = close.max()
    price_range = np.linspace(price_min, price_max, bins + 1)
    
    # Calculate volume at each price level
    volume_profile = {}
    
    for i in range(len(price_range) - 1):
        mask = (close >= price_range[i]) & (close < price_range[i + 1])
        volume_profile[f"{price_range[i]:.2f}-{price_range[i+1]:.2f}"] = volume[mask].sum()
    
    return volume_profile


def AccumulationDistribution(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    Accumulation/Distribution Line
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume
        
    Returns:
        A/D Line values
    """
    clv = ((close - low) - (high - close)) / (high - low)
    clv = clv.fillna(0)  # Handle division by zero
    
    ad = (clv * volume).cumsum()
    
    return ad


def ChaikinMoneyFlow(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
    """
    Chaikin Money Flow
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume
        period: Period for CMF
        
    Returns:
        CMF values
    """
    mfm = ((close - low) - (high - close)) / (high - low)
    mfm = mfm.fillna(0)
    
    mfv = mfm * volume
    
    cmf = mfv.rolling(window=period).sum() / volume.rolling(window=period).sum()
    
    return cmf


def EaseOfMovement(high: pd.Series, low: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
    """
    Ease of Movement
    
    Args:
        high: High prices
        low: Low prices
        volume: Volume
        period: Period for EOM
        
    Returns:
        EOM values
    """
    distance = ((high + low) / 2) - ((high.shift(1) + low.shift(1)) / 2)
    box_ratio = (volume / 100000000) / (high - low)
    
    eom = distance / box_ratio
    eom_ma = eom.rolling(window=period).mean()
    
    return eom_ma


def ForceIndex(close: pd.Series, volume: pd.Series, period: int = 13) -> pd.Series:
    """
    Force Index
    
    Args:
        close: Close prices
        volume: Volume
        period: Period for Force Index
        
    Returns:
        Force Index values
    """
    fi = (close - close.shift(1)) * volume
    fi_ema = fi.ewm(span=period, adjust=False).mean()
    
    return fi_ema


def KlingerOscillator(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    fast: int = 34,
    slow: int = 55
) -> pd.Series:
    """
    Klinger Oscillator
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume
        fast: Fast period
        slow: Slow period
        
    Returns:
        Klinger Oscillator values
    """
    dm = high - low
    cm = close - close.shift(1)
    
    trend = pd.Series(index=close.index, dtype=int)
    trend.iloc[0] = 1
    
    for i in range(1, len(close)):
        if cm.iloc[i] + dm.iloc[i] > cm.iloc[i-1] + dm.iloc[i-1]:
            trend.iloc[i] = 1
        else:
            trend.iloc[i] = -1
    
    vf = volume * trend * abs(2 * (dm / cm) - 1) * 100
    
    kvo = vf.ewm(span=fast, adjust=False).mean() - vf.ewm(span=slow, adjust=False).mean()
    
    return kvo


def NegativeVolumeIndex(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    Negative Volume Index
    
    Args:
        close: Close prices
        volume: Volume
        
    Returns:
        NVI values
    """
    nvi = pd.Series(index=close.index, dtype=float)
    nvi.iloc[0] = 1000
    
    for i in range(1, len(close)):
        if volume.iloc[i] < volume.iloc[i-1]:
            nvi.iloc[i] = nvi.iloc[i-1] + ((close.iloc[i] - close.iloc[i-1]) / close.iloc[i-1]) * nvi.iloc[i-1]
        else:
            nvi.iloc[i] = nvi.iloc[i-1]
    
    return nvi


def PositiveVolumeIndex(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    Positive Volume Index
    
    Args:
        close: Close prices
        volume: Volume
        
    Returns:
        PVI values
    """
    pvi = pd.Series(index=close.index, dtype=float)
    pvi.iloc[0] = 1000
    
    for i in range(1, len(close)):
        if volume.iloc[i] > volume.iloc[i-1]:
            pvi.iloc[i] = pvi.iloc[i-1] + ((close.iloc[i] - close.iloc[i-1]) / close.iloc[i-1]) * pvi.iloc[i-1]
        else:
            pvi.iloc[i] = pvi.iloc[i-1]
    
    return pvi
