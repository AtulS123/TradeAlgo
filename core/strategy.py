"""
Base strategy class for creating trading strategies
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime

from core.order import Order, OrderSide, OrderType, OrderManager
from utils.logger import logger


class Strategy(ABC):
    """
    Base class for all trading strategies
    
    Subclasses must implement:
    - on_data(): Called on each new data bar
    - generate_signals(): Generate buy/sell signals
    """
    
    def __init__(
        self,
        name: str,
        symbols: List[str],
        timeframe: str = "day",
        capital: float = 100000,
        position_size: float = 10000
    ):
        """
        Initialize strategy
        
        Args:
            name: Strategy name
            symbols: List of symbols to trade
            timeframe: Data timeframe (1minute, 5minute, day, etc.)
            capital: Initial capital
            position_size: Default position size in INR
        """
        self.name = name
        self.symbols = symbols
        self.timeframe = timeframe
        self.capital = capital
        self.initial_capital = capital
        self.position_size = position_size
        
        # Data storage
        self.data: Dict[str, pd.DataFrame] = {}
        self.current_bar: Dict[str, int] = {}
        
        # Positions and orders
        self.positions: Dict[str, int] = {}  # symbol -> quantity
        self.order_manager = OrderManager()
        
        # Performance tracking
        self.trades: List[Dict] = []
        self.equity_curve: List[float] = []
        
        # Indicators
        self.indicators: Dict[str, Any] = {}
        
        logger.info(f"Strategy '{name}' initialized with capital: ₹{capital:,.2f}")
    
    def set_data(self, symbol: str, data: pd.DataFrame):
        """
        Set historical data for a symbol
        
        Args:
            symbol: Trading symbol
            data: OHLCV DataFrame
        """
        self.data[symbol] = data
        self.current_bar[symbol] = 0
        logger.info(f"Loaded {len(data)} bars for {symbol}")
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current close price for symbol"""
        if symbol not in self.data or self.current_bar[symbol] >= len(self.data[symbol]):
            return None
        return self.data[symbol].iloc[self.current_bar[symbol]]['close']
    
    def get_position(self, symbol: str) -> int:
        """Get current position quantity for symbol"""
        return self.positions.get(symbol, 0)
    
    def get_position_value(self, symbol: str) -> float:
        """Get current position value"""
        quantity = self.get_position(symbol)
        if quantity == 0:
            return 0.0
        
        price = self.get_current_price(symbol)
        if price is None:
            return 0.0
        
        return quantity * price
    
    def get_portfolio_value(self) -> float:
        """Get total portfolio value (cash + positions)"""
        total = self.capital
        
        for symbol in self.positions:
            total += self.get_position_value(symbol)
        
        return total
    
    def buy(
        self,
        symbol: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        order_type: OrderType = OrderType.MARKET
    ) -> Order:
        """
        Place a buy order
        
        Args:
            symbol: Trading symbol
            quantity: Quantity to buy (if None, calculated from position_size)
            price: Limit price (for LIMIT orders)
            order_type: Order type
            
        Returns:
            Created order
        """
        if quantity is None:
            current_price = self.get_current_price(symbol)
            if current_price:
                quantity = int(self.position_size / current_price)
        
        order = self.order_manager.create_order(
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=quantity,
            order_type=order_type,
            price=price
        )
        
        logger.info(f"BUY order created: {symbol} x {quantity} @ {price or 'MARKET'}")
        return order
    
    def sell(
        self,
        symbol: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        order_type: OrderType = OrderType.MARKET
    ) -> Order:
        """
        Place a sell order
        
        Args:
            symbol: Trading symbol
            quantity: Quantity to sell (if None, sells entire position)
            price: Limit price (for LIMIT orders)
            order_type: Order type
            
        Returns:
            Created order
        """
        if quantity is None:
            quantity = self.get_position(symbol)
        
        order = self.order_manager.create_order(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=quantity,
            order_type=order_type,
            price=price
        )
        
        logger.info(f"SELL order created: {symbol} x {quantity} @ {price or 'MARKET'}")
        return order
    
    @abstractmethod
    def on_data(self, symbol: str, bar: pd.Series):
        """
        Called on each new data bar
        
        Args:
            symbol: Trading symbol
            bar: Current OHLCV bar
        """
        pass
    
    @abstractmethod
    def generate_signals(self) -> Dict[str, int]:
        """
        Generate trading signals
        
        Returns:
            Dictionary of symbol -> signal (1 for buy, -1 for sell, 0 for hold)
        """
        pass
    
    def calculate_position_size(self, symbol: str, signal: int) -> int:
        """
        Calculate position size based on signal
        
        Args:
            symbol: Trading symbol
            signal: Trading signal (1 or -1)
            
        Returns:
            Position size in quantity
        """
        current_price = self.get_current_price(symbol)
        if not current_price:
            return 0
        
        return int(self.position_size / current_price)
    
    def on_order_fill(self, order: Order):
        """
        Called when an order is filled
        
        Args:
            order: Filled order
        """
        # Update positions
        if order.side == OrderSide.BUY:
            self.positions[order.symbol] = self.positions.get(order.symbol, 0) + order.filled_quantity
            self.capital -= order.filled_quantity * order.average_price
        else:  # SELL
            self.positions[order.symbol] = self.positions.get(order.symbol, 0) - order.filled_quantity
            self.capital += order.filled_quantity * order.average_price
        
        # Record trade
        self.trades.append({
            'timestamp': order.timestamp,
            'symbol': order.symbol,
            'side': order.side.value,
            'quantity': order.filled_quantity,
            'price': order.average_price,
            'value': order.filled_quantity * order.average_price
        })
        
        logger.info(f"Order filled: {order.side.value} {order.symbol} x {order.filled_quantity} @ ₹{order.average_price:.2f}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get strategy statistics
        
        Returns:
            Dictionary of statistics
        """
        portfolio_value = self.get_portfolio_value()
        total_return = ((portfolio_value - self.initial_capital) / self.initial_capital) * 100
        
        return {
            'name': self.name,
            'initial_capital': self.initial_capital,
            'current_capital': self.capital,
            'portfolio_value': portfolio_value,
            'total_return_percent': total_return,
            'total_trades': len(self.trades),
            'positions': dict(self.positions)
        }
