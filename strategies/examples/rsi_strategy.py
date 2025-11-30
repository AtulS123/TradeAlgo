"""
RSI Strategy - Example momentum-based strategy
"""

import pandas as pd
from core.strategy import Strategy
from indicators.momentum import RSI
from utils.logger import logger


class RSIStrategy(Strategy):
    """
    RSI (Relative Strength Index) Strategy
    
    Buy when RSI crosses below oversold level (default 30)
    Sell when RSI crosses above overbought level (default 70)
    """
    
    def __init__(
        self,
        symbols: list,
        rsi_period: int = 14,
        oversold: float = 30,
        overbought: float = 70,
        capital: float = 100000,
        position_size: float = 10000
    ):
        """
        Initialize RSI Strategy
        
        Args:
            symbols: List of symbols to trade
            rsi_period: RSI calculation period
            oversold: Oversold threshold (buy signal)
            overbought: Overbought threshold (sell signal)
            capital: Initial capital
            position_size: Position size per trade
        """
        super().__init__(
            name=f"RSI Strategy ({rsi_period}, {oversold}/{overbought})",
            symbols=symbols,
            capital=capital,
            position_size=position_size
        )
        
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        
        logger.info(f"RSI Strategy initialized: Period={rsi_period}, Oversold={oversold}, Overbought={overbought}")
    
    def on_data(self, symbol: str, bar: pd.Series):
        """
        Called on each new data bar
        
        Args:
            symbol: Trading symbol
            bar: Current OHLCV bar
        """
        # Need enough data for RSI
        if len(self.data[symbol]) < self.rsi_period + 1:
            return
        
        # Calculate RSI
        close_prices = self.data[symbol]['close']
        rsi = RSI(close_prices, self.rsi_period)
        
        # Get current and previous RSI values
        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2]
        
        # Check for signals
        current_position = self.get_position(symbol)
        
        # Buy signal: RSI crosses below oversold level
        if prev_rsi >= self.oversold and current_rsi < self.oversold:
            if current_position == 0:
                logger.info(f"BUY signal for {symbol}: RSI crossed below {self.oversold} (RSI={current_rsi:.2f})")
                self.buy(symbol)
        
        # Sell signal: RSI crosses above overbought level
        elif prev_rsi <= self.overbought and current_rsi > self.overbought:
            if current_position > 0:
                logger.info(f"SELL signal for {symbol}: RSI crossed above {self.overbought} (RSI={current_rsi:.2f})")
                self.sell(symbol)
    
    def generate_signals(self) -> dict:
        """
        Generate trading signals for all symbols
        
        Returns:
            Dictionary of symbol -> signal (1 for buy, -1 for sell, 0 for hold)
        """
        signals = {}
        
        for symbol in self.symbols:
            if len(self.data[symbol]) < self.rsi_period + 1:
                signals[symbol] = 0
                continue
            
            close_prices = self.data[symbol]['close']
            rsi = RSI(close_prices, self.rsi_period)
            
            current_rsi = rsi.iloc[-1]
            
            if current_rsi < self.oversold:
                signals[symbol] = 1  # Buy signal (oversold)
            elif current_rsi > self.overbought:
                signals[symbol] = -1  # Sell signal (overbought)
            else:
                signals[symbol] = 0  # Hold
        
        return signals
