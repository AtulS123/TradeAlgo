"""
Momentum indicators
"""

import pandas as pd
import numpy as np
from typing import Union


def RSI(data: Union[pd.Series, np.ndarray], period: int = 14) -> pd.Series:
    """
    Relative Strength Index
    
    Args:
        data: Price data
        period: Period for RSI
        
    Returns:
        RSI values
    """
    delta = pd.Series(data).diff()
    
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def Stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3,
    smooth_k: int = 3
) -> tuple:
    """
    Stochastic Oscillator
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        k_period: %K period
        d_period: %D period
        smooth_k: Smoothing period for %K
        
    Returns:
        Tuple of (%K, %D)
    """
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    
    k_fast = 100 * (close - lowest_low) / (highest_high - lowest_low)
    k = k_fast.rolling(window=smooth_k).mean()
    d = k.rolling(window=d_period).mean()
    
    return k, d


def WilliamsR(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Williams %R
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Period for Williams %R
        
    Returns:
        Williams %R values
    """
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    
    wr = -100 * (highest_high - close) / (highest_high - lowest_low)
    
    return wr


def ROC(data: Union[pd.Series, np.ndarray], period: int = 12) -> pd.Series:
    """
    Rate of Change
    
    Args:
        data: Price data
        period: Period for ROC
        
    Returns:
        ROC values
    """
    roc = 100 * (pd.Series(data) - pd.Series(data).shift(period)) / pd.Series(data).shift(period)
    return roc


def CCI(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
    """
    Commodity Channel Index
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Period for CCI
        
    Returns:
        CCI values
    """
    tp = (high + low + close) / 3
    sma_tp = tp.rolling(window=period).mean()
    mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
    
    cci = (tp - sma_tp) / (0.015 * mad)
    
    return cci


def MFI(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
    """
    Money Flow Index
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume
        period: Period for MFI
        
    Returns:
        MFI values
    """
    tp = (high + low + close) / 3
    mf = tp * volume
    
    mf_pos = mf.where(tp > tp.shift(1), 0)
    mf_neg = mf.where(tp < tp.shift(1), 0)
    
    mf_pos_sum = mf_pos.rolling(window=period).sum()
    mf_neg_sum = mf_neg.rolling(window=period).sum()
    
    mfi = 100 - (100 / (1 + mf_pos_sum / mf_neg_sum))
    
    return mfi


def UltimateOscillator(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period1: int = 7,
    period2: int = 14,
    period3: int = 28
) -> pd.Series:
    """
    Ultimate Oscillator
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period1: First period
        period2: Second period
        period3: Third period
        
    Returns:
        Ultimate Oscillator values
    """
    bp = close - pd.concat([low, close.shift(1)], axis=1).min(axis=1)
    tr = pd.concat([
        high - low,
        abs(high - close.shift(1)),
        abs(low - close.shift(1))
    ], axis=1).max(axis=1)
    
    avg1 = bp.rolling(window=period1).sum() / tr.rolling(window=period1).sum()
    avg2 = bp.rolling(window=period2).sum() / tr.rolling(window=period2).sum()
    avg3 = bp.rolling(window=period3).sum() / tr.rolling(window=period3).sum()
    
    uo = 100 * ((4 * avg1) + (2 * avg2) + avg3) / 7
    
    return uo


def TSI(data: Union[pd.Series, np.ndarray], long_period: int = 25, short_period: int = 13) -> pd.Series:
    """
    True Strength Index
    
    Args:
        data: Price data
        long_period: Long period
        short_period: Short period
        
    Returns:
        TSI values
    """
    momentum = pd.Series(data).diff()
    
    ema_long = momentum.ewm(span=long_period, adjust=False).mean()
    ema_short = ema_long.ewm(span=short_period, adjust=False).mean()
    
    abs_momentum = abs(momentum)
    abs_ema_long = abs_momentum.ewm(span=long_period, adjust=False).mean()
    abs_ema_short = abs_ema_long.ewm(span=short_period, adjust=False).mean()
    
    tsi = 100 * (ema_short / abs_ema_short)
    
    return tsi


def KST(
    data: Union[pd.Series, np.ndarray],
    roc1: int = 10,
    roc2: int = 15,
    roc3: int = 20,
    roc4: int = 30,
    sma1: int = 10,
    sma2: int = 10,
    sma3: int = 10,
    sma4: int = 15
) -> pd.Series:
    """
    Know Sure Thing (KST)
    
    Args:
        data: Price data
        roc1-4: ROC periods
        sma1-4: SMA periods
        
    Returns:
        KST values
    """
    data = pd.Series(data)
    
    rcma1 = ROC(data, roc1).rolling(window=sma1).mean()
    rcma2 = ROC(data, roc2).rolling(window=sma2).mean()
    rcma3 = ROC(data, roc3).rolling(window=sma3).mean()
    rcma4 = ROC(data, roc4).rolling(window=sma4).mean()
    
    kst = (rcma1 * 1) + (rcma2 * 2) + (rcma3 * 3) + (rcma4 * 4)
    
    return kst


def AwesomeOscillator(high: pd.Series, low: pd.Series) -> pd.Series:
    """
    Awesome Oscillator
    
    Args:
        high: High prices
        low: Low prices
        
    Returns:
        Awesome Oscillator values
    """
    median_price = (high + low) / 2
    
    ao = median_price.rolling(window=5).mean() - median_price.rolling(window=34).mean()
    
    return ao


def ChandeMomentumOscillator(data: Union[pd.Series, np.ndarray], period: int = 14) -> pd.Series:
    """
    Chande Momentum Oscillator
    
    Args:
        data: Price data
        period: Period for CMO
        
    Returns:
        CMO values
    """
    delta = pd.Series(data).diff()
    
    gain = delta.where(delta > 0, 0).rolling(window=period).sum()
    loss = -delta.where(delta < 0, 0).rolling(window=period).sum()
    
    cmo = 100 * (gain - loss) / (gain + loss)
    
    return cmo


def DetrendedPriceOscillator(data: Union[pd.Series, np.ndarray], period: int = 20) -> pd.Series:
    """
    Detrended Price Oscillator
    
    Args:
        data: Price data
        period: Period for DPO
        
    Returns:
        DPO values
    """
    data = pd.Series(data)
    sma = data.rolling(window=period).mean()
    
    dpo = data.shift(int(period / 2) + 1) - sma
    
    return dpo


def PPO(data: Union[pd.Series, np.ndarray], fast: int = 12, slow: int = 26) -> pd.Series:
    """
    Percentage Price Oscillator
    
    Args:
        data: Price data
        fast: Fast period
        slow: Slow period
        
    Returns:
        PPO values
    """
    data = pd.Series(data)
    
    ema_fast = data.ewm(span=fast, adjust=False).mean()
    ema_slow = data.ewm(span=slow, adjust=False).mean()
    
    ppo = 100 * (ema_fast - ema_slow) / ema_slow
    
    return ppo


def RelativeVigorIndex(
    open_: pd.Series,
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 10
) -> pd.Series:
    """
    Relative Vigor Index
    
    Args:
        open_: Open prices
        high: High prices
        low: Low prices
        close: Close prices
        period: Period for RVI
        
    Returns:
        RVI values
    """
    numerator = (close - open_) + 2 * (close.shift(1) - open_.shift(1)) + \
                2 * (close.shift(2) - open_.shift(2)) + (close.shift(3) - open_.shift(3))
    numerator = numerator / 6
    
    denominator = (high - low) + 2 * (high.shift(1) - low.shift(1)) + \
                  2 * (high.shift(2) - low.shift(2)) + (high.shift(3) - low.shift(3))
    denominator = denominator / 6
    
    rvi = numerator.rolling(window=period).sum() / denominator.rolling(window=period).sum()
    
    return rvi


def SchaffTrendCycle(data: Union[pd.Series, np.ndarray], period: int = 10) -> pd.Series:
    """
    Schaff Trend Cycle
    
    Args:
        data: Price data
        period: Period for STC
        
    Returns:
        STC values
    """
    # Simplified version - full implementation is more complex
    data = pd.Series(data)
    
    ema_fast = data.ewm(span=23, adjust=False).mean()
    ema_slow = data.ewm(span=50, adjust=False).mean()
    
    macd = ema_fast - ema_slow
    
    # Stochastic of MACD
    lowest = macd.rolling(window=period).min()
    highest = macd.rolling(window=period).max()
    
    stc = 100 * (macd - lowest) / (highest - lowest)
    stc = stc.ewm(span=3, adjust=False).mean()
    
    return stc
