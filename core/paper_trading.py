"""
Paper trading simulator for risk-free strategy testing
"""

import time
import threading
from datetime import datetime
from typing import Optional, Dict
from queue import Queue

from core.strategy import Strategy
from core.order import Order, OrderType, OrderStatus, OrderSide
# from data.fetcher import KiteDataFetcher  # Commented for demo
from utils.config import config
from utils.logger import logger


class PaperTradingEngine:
    """
    Paper trading engine with real-time market simulation
    """
    
    def __init__(
        self,
        strategy: Strategy,
        data_fetcher: Optional[any] = None,  # Changed from KiteDataFetcher
        slippage_percent: float = 0.1,
        brokerage_percent: float = 0.03,
        update_interval: int = 60  # seconds
    ):
        """
        Initialize paper trading engine
        
        Args:
            strategy: Strategy to paper trade
            data_fetcher: Data fetcher for real-time quotes
            slippage_percent: Slippage percentage
            brokerage_percent: Brokerage percentage
            update_interval: Data update interval in seconds
        """
        self.strategy = strategy
        self.data_fetcher = data_fetcher
        self.slippage_percent = slippage_percent
        self.brokerage_percent = brokerage_percent
        self.update_interval = update_interval
        
        # State
        self.is_running = False
        self.start_time = None
        self.current_quotes = {}
        
        # Threading
        self.data_thread = None
        self.strategy_thread = None
        self.event_queue = Queue()
        
        # Performance tracking
        self.trades = []
        self.equity_history = []
        
        logger.info(f"Paper trading engine initialized for strategy: {strategy.name}")
    
    def start(self):
        """Start paper trading"""
        if self.is_running:
            logger.warning("Paper trading already running")
            return
        
        self.is_running = True
        self.start_time = datetime.now()
        
        logger.info("="*60)
        logger.info("PAPER TRADING STARTED")
        logger.info("="*60)
        logger.info(f"Strategy: {self.strategy.name}")
        logger.info(f"Symbols: {', '.join(self.strategy.symbols)}")
        logger.info(f"Initial Capital: ₹{self.strategy.initial_capital:,.2f}")
        logger.info(f"Update Interval: {self.update_interval}s")
        logger.info("="*60)
        
        # Start data fetching thread
        self.data_thread = threading.Thread(target=self._data_loop, daemon=True)
        self.data_thread.start()
        
        # Start strategy execution thread
        self.strategy_thread = threading.Thread(target=self._strategy_loop, daemon=True)
        self.strategy_thread.start()
        
        logger.info("Paper trading threads started")
    
    def stop(self):
        """Stop paper trading"""
        if not self.is_running:
            logger.warning("Paper trading not running")
            return
        
        self.is_running = False
        
        # Wait for threads to finish
        if self.data_thread:
            self.data_thread.join(timeout=5)
        if self.strategy_thread:
            self.strategy_thread.join(timeout=5)
        
        # Print summary
        self._print_summary()
        
        logger.info("="*60)
        logger.info("PAPER TRADING STOPPED")
        logger.info("="*60)
    
    def _data_loop(self):
        """Data fetching loop"""
        while self.is_running:
            try:
                # Fetch real-time quotes
                if self.data_fetcher:
                    quotes = self.data_fetcher.get_quote(self.strategy.symbols)
                    self.current_quotes = quotes
                    
                    # Put quotes in event queue
                    self.event_queue.put(('quote', quotes))
                    
                    logger.debug(f"Fetched quotes for {len(quotes)} symbols")
                
                # Sleep until next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in data loop: {e}")
                time.sleep(self.update_interval)
    
    def _strategy_loop(self):
        """Strategy execution loop"""
        while self.is_running:
            try:
                # Process events from queue
                if not self.event_queue.empty():
                    event_type, event_data = self.event_queue.get()
                    
                    if event_type == 'quote':
                        self._process_quotes(event_data)
                
                # Execute pending orders
                self._execute_pending_orders()
                
                # Record equity
                portfolio_value = self.strategy.get_portfolio_value()
                self.equity_history.append({
                    'timestamp': datetime.now(),
                    'value': portfolio_value
                })
                
                # Small sleep to prevent busy waiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in strategy loop: {e}")
                time.sleep(1)
    
    def _process_quotes(self, quotes: Dict):
        """
        Process real-time quotes
        
        Args:
            quotes: Dictionary of quotes from data fetcher
        """
        for symbol_key, quote_data in quotes.items():
            # Extract symbol from key (format: "NSE:SYMBOL")
            symbol = symbol_key.split(':')[-1]
            
            if symbol not in self.strategy.symbols:
                continue
            
            # Create bar data from quote
            bar_data = {
                'open': quote_data.get('ohlc', {}).get('open', 0),
                'high': quote_data.get('ohlc', {}).get('high', 0),
                'low': quote_data.get('ohlc', {}).get('low', 0),
                'close': quote_data.get('last_price', 0),
                'volume': quote_data.get('volume', 0),
                'timestamp': datetime.now()
            }
            
            # Update strategy data
            if symbol not in self.strategy.data:
                import pandas as pd
                self.strategy.data[symbol] = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
            
            # Append new bar
            import pandas as pd
            new_bar = pd.DataFrame([bar_data])
            new_bar.set_index('timestamp', inplace=True)
            self.strategy.data[symbol] = pd.concat([self.strategy.data[symbol], new_bar])
            
            # Keep only recent data (last 1000 bars)
            if len(self.strategy.data[symbol]) > 1000:
                self.strategy.data[symbol] = self.strategy.data[symbol].iloc[-1000:]
            
            # Call strategy's on_data
            self.strategy.on_data(symbol, new_bar.iloc[0])
    
    def _execute_pending_orders(self):
        """Execute pending orders with realistic simulation"""
        pending_orders = self.strategy.order_manager.get_pending_orders()
        
        for order in pending_orders:
            self._execute_order(order)
    
    def _execute_order(self, order: Order):
        """
        Execute order with realistic simulation
        
        Args:
            order: Order to execute
        """
        symbol = order.symbol
        
        # Get current quote
        symbol_key = f"NSE:{symbol}"
        if symbol_key not in self.current_quotes:
            logger.debug(f"No quote available for {symbol}")
            return
        
        quote = self.current_quotes[symbol_key]
        
        # Get bid/ask prices
        bid_price = quote.get('depth', {}).get('buy', [{}])[0].get('price', 0) if quote.get('depth') else quote.get('last_price', 0)
        ask_price = quote.get('depth', {}).get('sell', [{}])[0].get('price', 0) if quote.get('depth') else quote.get('last_price', 0)
        last_price = quote.get('last_price', 0)
        
        # Determine execution price
        execution_price = None
        
        if order.order_type == OrderType.MARKET:
            # Market orders execute at ask (buy) or bid (sell)
            if order.side == OrderSide.BUY:
                execution_price = ask_price if ask_price > 0 else last_price
                # Add slippage
                execution_price *= (1 + self.slippage_percent / 100)
            else:
                execution_price = bid_price if bid_price > 0 else last_price
                # Subtract slippage
                execution_price *= (1 - self.slippage_percent / 100)
        
        elif order.order_type == OrderType.LIMIT:
            # Limit orders execute if price crosses limit
            if order.side == OrderSide.BUY:
                if ask_price <= order.price:
                    execution_price = order.price
            else:
                if bid_price >= order.price:
                    execution_price = order.price
        
        elif order.order_type == OrderType.STOP_LOSS:
            # Stop loss triggers at trigger price
            if order.side == OrderSide.BUY:
                if last_price >= order.trigger_price:
                    execution_price = ask_price
            else:
                if last_price <= order.trigger_price:
                    execution_price = bid_price
        
        if execution_price is None:
            return  # Order not filled
        
        # Calculate costs
        trade_value = order.quantity * execution_price
        brokerage = trade_value * (self.brokerage_percent / 100)
        gst = brokerage * 0.18
        stt = trade_value * 0.00025 if order.side == OrderSide.SELL else 0
        total_cost = brokerage + gst + stt
        
        # Check capital
        if order.side == OrderSide.BUY:
            required_capital = trade_value + total_cost
            if self.strategy.capital < required_capital:
                order.reject("Insufficient capital")
                logger.warning(f"Order rejected: Insufficient capital for {symbol}")
                return
        
        # Fill order
        order.fill(order.quantity, execution_price)
        self.strategy.on_order_fill(order)
        self.strategy.capital -= total_cost
        
        # Record trade
        trade_record = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'side': order.side.value,
            'quantity': order.quantity,
            'price': execution_price,
            'value': trade_value,
            'brokerage': brokerage,
            'total_cost': total_cost
        }
        self.trades.append(trade_record)
        
        logger.info(f"✅ ORDER FILLED: {order.side.value} {symbol} x {order.quantity} @ ₹{execution_price:.2f}")
        logger.info(f"   Portfolio Value: ₹{self.strategy.get_portfolio_value():,.2f}")
    
    def _print_summary(self):
        """Print paper trading summary"""
        duration = (datetime.now() - self.start_time).total_seconds() / 60  # minutes
        final_value = self.strategy.get_portfolio_value()
        total_return = ((final_value - self.strategy.initial_capital) / self.strategy.initial_capital) * 100
        
        print("\n" + "="*60)
        print("PAPER TRADING SUMMARY")
        print("="*60)
        print(f"Duration: {duration:.1f} minutes")
        print(f"Initial Capital: ₹{self.strategy.initial_capital:,.2f}")
        print(f"Final Value: ₹{final_value:,.2f}")
        print(f"Total Return: {total_return:.2f}%")
        print(f"Total Trades: {len(self.trades)}")
        print(f"Current Positions: {self.strategy.positions}")
        print("="*60 + "\n")
    
    def get_status(self) -> Dict:
        """Get current paper trading status"""
        return {
            'is_running': self.is_running,
            'start_time': self.start_time,
            'duration_minutes': (datetime.now() - self.start_time).total_seconds() / 60 if self.start_time else 0,
            'portfolio_value': self.strategy.get_portfolio_value(),
            'total_trades': len(self.trades),
            'positions': dict(self.strategy.positions),
            'capital': self.strategy.capital
        }
    
    def get_performance(self) -> Dict:
        """Get performance metrics"""
        if not self.equity_history:
            return {}
        
        import pandas as pd
        equity_series = pd.Series([e['value'] for e in self.equity_history])
        
        final_value = equity_series.iloc[-1]
        total_return = ((final_value - self.strategy.initial_capital) / self.strategy.initial_capital) * 100
        
        returns = equity_series.pct_change().dropna()
        volatility = returns.std() * 100 if len(returns) > 0 else 0
        
        return {
            'total_return_percent': total_return,
            'volatility': volatility,
            'total_trades': len(self.trades),
            'equity_curve': [e['value'] for e in self.equity_history]
        }
