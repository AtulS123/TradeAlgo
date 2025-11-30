"""
Example SMA Crossover Strategy
"""

import pandas as pd
from core.strategy import Strategy
from indicators.trend import SMA
from utils.logger import logger


class SMACrossoverStrategy(Strategy):
    """
    Simple Moving Average Crossover Strategy
    
    Buy when fast SMA crosses above slow SMA
    Sell when fast SMA crosses below slow SMA
    """
    
    def __init__(
        self,
        symbols: list,
        fast_period: int = 10,
        slow_period: int = 20,
        capital: float = 100000,
        position_size: float = 10000
    ):
        """
        Initialize SMA Crossover Strategy
        
        Args:
            symbols: List of symbols to trade
            fast_period: Fast SMA period
            slow_period: Slow SMA period
            capital: Initial capital
            position_size: Position size per trade
        """
        super().__init__(
            name=f"SMA Crossover ({fast_period}/{slow_period})",
            symbols=symbols,
            capital=capital,
            position_size=position_size
        )
        
        self.fast_period = fast_period
        self.slow_period = slow_period
        
        logger.info(f"SMA Crossover Strategy initialized: {fast_period}/{slow_period}")
    
    def on_data(self, symbol: str, bar: pd.Series):
        """
        Called on each new data bar
        
        Args:
            symbol: Trading symbol
            bar: Current OHLCV bar
        """
        # Need enough data for slow SMA
        if len(self.data[symbol]) < self.slow_period:
            return
        
        # Calculate SMAs
        close_prices = self.data[symbol]['close']
        fast_sma = SMA(close_prices, self.fast_period)
        slow_sma = SMA(close_prices, self.slow_period)
        
        # Get current and previous values
        current_fast = fast_sma.iloc[-1]
        current_slow = slow_sma.iloc[-1]
        prev_fast = fast_sma.iloc[-2]
        prev_slow = slow_sma.iloc[-2]
        
        # Check for crossover
        current_position = self.get_position(symbol)
        
        # Bullish crossover (fast crosses above slow)
        if prev_fast <= prev_slow and current_fast > current_slow:
            if current_position == 0:
                logger.info(f"BUY signal for {symbol}: Fast SMA crossed above Slow SMA")
                self.buy(symbol)
        
        # Bearish crossover (fast crosses below slow)
        elif prev_fast >= prev_slow and current_fast < current_slow:
            if current_position > 0:
                logger.info(f"SELL signal for {symbol}: Fast SMA crossed below Slow SMA")
                self.sell(symbol)
    
    def generate_signals(self) -> dict:
        """
        Generate trading signals for all symbols
        
        Returns:
            Dictionary of symbol -> signal (1 for buy, -1 for sell, 0 for hold)
        """
        signals = {}
        
        for symbol in self.symbols:
            if len(self.data[symbol]) < self.slow_period:
                signals[symbol] = 0
                continue
            
            close_prices = self.data[symbol]['close']
            fast_sma = SMA(close_prices, self.fast_period)
            slow_sma = SMA(close_prices, self.slow_period)
            
            current_fast = fast_sma.iloc[-1]
            current_slow = slow_sma.iloc[-1]
            
            if current_fast > current_slow:
                signals[symbol] = 1  # Buy signal
            elif current_fast < current_slow:
                signals[symbol] = -1  # Sell signal
            else:
                signals[symbol] = 0  # Hold
        
        return signals
