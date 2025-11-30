"""
Volatility indicators
"""

import pandas as pd
import numpy as np
from typing import Union, tuple


def BollingerBands(
    data: Union[pd.Series, np.ndarray],
    period: int = 20,
    std_dev: float = 2.0
) -> tuple:
    """
    Bollinger Bands
    
    Args:
        data: Price data
        period: Period for moving average
        std_dev: Number of standard deviations
        
    Returns:
        Tuple of (Upper Band, Middle Band, Lower Band)
    """
    data = pd.Series(data)
    
    middle_band = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()
    
    upper_band = middle_band + (std_dev * std)
    lower_band = middle_band - (std_dev * std)
    
    return upper_band, middle_band, lower_band


def ATR(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Average True Range
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Period for ATR
        
    Returns:
        ATR values
    """
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


def KeltnerChannels(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    ema_period: int = 20,
    atr_period: int = 10,
    multiplier: float = 2.0
) -> tuple:
    """
    Keltner Channels
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        ema_period: EMA period
        atr_period: ATR period
        multiplier: ATR multiplier
        
    Returns:
        Tuple of (Upper Channel, Middle Channel, Lower Channel)
    """
    middle = close.ewm(span=ema_period, adjust=False).mean()
    atr = ATR(high, low, close, atr_period)
    
    upper = middle + (multiplier * atr)
    lower = middle - (multiplier * atr)
    
    return upper, middle, lower


def DonchianChannels(high: pd.Series, low: pd.Series, period: int = 20) -> tuple:
    """
    Donchian Channels
    
    Args:
        high: High prices
        low: Low prices
        period: Period for channels
        
    Returns:
        Tuple of (Upper Channel, Middle Channel, Lower Channel)
    """
    upper = high.rolling(window=period).max()
    lower = low.rolling(window=period).min()
    middle = (upper + lower) / 2
    
    return upper, middle, lower


def StandardDeviation(data: Union[pd.Series, np.ndarray], period: int = 20) -> pd.Series:
    """
    Standard Deviation
    
    Args:
        data: Price data
        period: Period for standard deviation
        
    Returns:
        Standard deviation values
    """
    return pd.Series(data).rolling(window=period).std()


def HistoricalVolatility(data: Union[pd.Series, np.ndarray], period: int = 20) -> pd.Series:
    """
    Historical Volatility (annualized)
    
    Args:
        data: Price data
        period: Period for volatility calculation
        
    Returns:
        Historical volatility values
    """
    log_returns = np.log(pd.Series(data) / pd.Series(data).shift(1))
    volatility = log_returns.rolling(window=period).std() * np.sqrt(252)  # Annualized
    
    return volatility


def ChaikinVolatility(high: pd.Series, low: pd.Series, ema_period: int = 10, roc_period: int = 10) -> pd.Series:
    """
    Chaikin Volatility
    
    Args:
        high: High prices
        low: Low prices
        ema_period: EMA period
        roc_period: ROC period
        
    Returns:
        Chaikin Volatility values
    """
    hl_diff = high - low
    ema_hl = hl_diff.ewm(span=ema_period, adjust=False).mean()
    
    cv = 100 * (ema_hl - ema_hl.shift(roc_period)) / ema_hl.shift(roc_period)
    
    return cv


def MassIndex(high: pd.Series, low: pd.Series, ema_period: int = 9, sum_period: int = 25) -> pd.Series:
    """
    Mass Index
    
    Args:
        high: High prices
        low: Low prices
        ema_period: EMA period
        sum_period: Sum period
        
    Returns:
        Mass Index values
    """
    hl_range = high - low
    ema1 = hl_range.ewm(span=ema_period, adjust=False).mean()
    ema2 = ema1.ewm(span=ema_period, adjust=False).mean()
    
    ratio = ema1 / ema2
    mass_index = ratio.rolling(window=sum_period).sum()
    
    return mass_index


def UlcerIndex(data: Union[pd.Series, np.ndarray], period: int = 14) -> pd.Series:
    """
    Ulcer Index
    
    Args:
        data: Price data
        period: Period for Ulcer Index
        
    Returns:
        Ulcer Index values
    """
    data = pd.Series(data)
    
    max_close = data.rolling(window=period).max()
    drawdown = 100 * (data - max_close) / max_close
    
    ulcer = np.sqrt((drawdown ** 2).rolling(window=period).mean())
    
    return ulcer


def TrueRange(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """
    True Range
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        
    Returns:
        True Range values
    """
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    return tr
