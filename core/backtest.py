"""
Backtesting engine for strategy testing
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, List
from copy import deepcopy

from core.strategy import Strategy
from core.order import Order, OrderType, OrderStatus, OrderSide
from data.storage import get_session, Backtest as BacktestModel, Trade as TradeModel
from utils.config import config
from utils.logger import logger


class BacktestEngine:
    """
    Event-driven backtesting engine with realistic order execution
    """
    
    def __init__(
        self,
        strategy: Strategy,
        start_date: datetime,
        end_date: datetime,
        slippage_percent: Optional[float] = None,
        brokerage_percent: Optional[float] = None,
        stt_percent: float = 0.025,
        gst_percent: float = 18.0
    ):
        """
        Initialize backtest engine
        
        Args:
            strategy: Strategy to backtest
            start_date: Backtest start date
            end_date: Backtest end date
            slippage_percent: Slippage percentage (default from config)
            brokerage_percent: Brokerage percentage (default from config)
            stt_percent: Securities Transaction Tax percentage
            gst_percent: GST on brokerage percentage
        """
        self.strategy = strategy
        self.start_date = start_date
        self.end_date = end_date
        
        # Transaction costs
        self.slippage_percent = slippage_percent or config.default_slippage_percent
        self.brokerage_percent = brokerage_percent or config.default_brokerage_percent
        self.stt_percent = stt_percent
        self.gst_percent = gst_percent
        
        # Backtest state
        self.current_date = None
        self.current_bar = {}
        self.equity_curve = []
        self.trades = []
        
        # Performance tracking
        self.metrics = {}
        
        logger.info(f"Backtest initialized: {start_date} to {end_date}")
        logger.info(f"Slippage: {self.slippage_percent}%, Brokerage: {self.brokerage_percent}%")
    
    def run(self) -> Dict:
        """
        Run the backtest
        
        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Starting backtest for strategy: {self.strategy.name}")
        
        # Initialize equity curve
        self.equity_curve = [self.strategy.initial_capital]
        
        # Get data for all symbols
        for symbol in self.strategy.symbols:
            if symbol not in self.strategy.data or self.strategy.data[symbol].empty:
                logger.warning(f"No data for {symbol}, skipping")
                continue
            
            # Filter data by date range
            data = self.strategy.data[symbol]
            data = data[(data.index >= self.start_date) & (data.index <= self.end_date)]
            self.strategy.data[symbol] = data
        
        # Event loop - process each bar
        self._run_event_loop()
        
        # Calculate final metrics
        self.metrics = self._calculate_metrics()
        
        # Save to database
        self._save_to_database()
        
        logger.info(f"Backtest completed: {len(self.trades)} trades executed")
        logger.info(f"Final portfolio value: ₹{self.strategy.get_portfolio_value():,.2f}")
        
        return {
            'metrics': self.metrics,
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'strategy': self.strategy
        }
    
    def _run_event_loop(self):
        """Run the main event loop"""
        # Get all unique timestamps across all symbols
        all_timestamps = set()
        for symbol in self.strategy.symbols:
            if symbol in self.strategy.data:
                all_timestamps.update(self.strategy.data[symbol].index)
        
        all_timestamps = sorted(all_timestamps)
        
        # Process each timestamp
        for i, timestamp in enumerate(all_timestamps):
            self.current_date = timestamp
            
            # Update current bar for each symbol
            for symbol in self.strategy.symbols:
                if symbol in self.strategy.data:
                    data = self.strategy.data[symbol]
                    if timestamp in data.index:
                        self.current_bar[symbol] = data.loc[timestamp]
                        self.strategy.current_bar[symbol] = data.index.get_loc(timestamp)
            
            # Execute pending orders from previous bar
            self._execute_pending_orders()
            
            # Call strategy's on_data for each symbol
            for symbol in self.strategy.symbols:
                if symbol in self.current_bar:
                    self.strategy.on_data(symbol, self.current_bar[symbol])
            
            # Record equity
            portfolio_value = self.strategy.get_portfolio_value()
            self.equity_curve.append(portfolio_value)
    
    def _execute_pending_orders(self):
        """Execute pending orders"""
        pending_orders = self.strategy.order_manager.get_pending_orders()
        
        for order in pending_orders:
            self._execute_order(order)
    
    def _execute_order(self, order: Order):
        """
        Execute an order with realistic simulation
        
        Args:
            order: Order to execute
        """
        symbol = order.symbol
        
        # Get current bar
        if symbol not in self.current_bar:
            order.reject("No data available")
            return
        
        bar = self.current_bar[symbol]
        
        # Determine execution price based on order type
        if order.order_type == OrderType.MARKET:
            # Market orders execute at next bar's open with slippage
            execution_price = bar['open']
            
            # Apply slippage
            if order.side == OrderSide.BUY:
                execution_price *= (1 + self.slippage_percent / 100)
            else:
                execution_price *= (1 - self.slippage_percent / 100)
        
        elif order.order_type == OrderType.LIMIT:
            # Limit orders execute if price crosses limit
            if order.side == OrderSide.BUY:
                if bar['low'] <= order.price:
                    execution_price = order.price
                else:
                    return  # Order not filled
            else:  # SELL
                if bar['high'] >= order.price:
                    execution_price = order.price
                else:
                    return  # Order not filled
        
        elif order.order_type == OrderType.STOP_LOSS:
            # Stop loss orders trigger when price crosses trigger price
            if order.side == OrderSide.BUY:
                if bar['high'] >= order.trigger_price:
                    execution_price = bar['open']
                else:
                    return
            else:  # SELL
                if bar['low'] <= order.trigger_price:
                    execution_price = bar['open']
                else:
                    return
        
        else:
            order.reject("Unsupported order type")
            return
        
        # Calculate transaction costs
        trade_value = order.quantity * execution_price
        brokerage = trade_value * (self.brokerage_percent / 100)
        gst = brokerage * (self.gst_percent / 100)
        stt = trade_value * (self.stt_percent / 100) if order.side == OrderSide.SELL else 0
        
        total_cost = brokerage + gst + stt
        
        # Check if sufficient capital
        if order.side == OrderSide.BUY:
            required_capital = trade_value + total_cost
            if self.strategy.capital < required_capital:
                order.reject("Insufficient capital")
                logger.warning(f"Order rejected: Insufficient capital for {symbol}")
                return
        
        # Fill the order
        order.fill(order.quantity, execution_price)
        
        # Update strategy positions and capital
        self.strategy.on_order_fill(order)
        
        # Deduct transaction costs
        self.strategy.capital -= total_cost
        
        # Record trade
        self.trades.append({
            'timestamp': self.current_date,
            'symbol': symbol,
            'side': order.side.value,
            'quantity': order.quantity,
            'price': execution_price,
            'value': trade_value,
            'brokerage': brokerage,
            'gst': gst,
            'stt': stt,
            'total_cost': total_cost
        })
        
        logger.debug(f"Order executed: {order.side.value} {symbol} x {order.quantity} @ ₹{execution_price:.2f}")
    
    def _calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        from utils.metrics import PerformanceMetrics
        
        metrics_calculator = PerformanceMetrics(
            equity_curve=self.equity_curve,
            trades=self.trades,
            initial_capital=self.strategy.initial_capital
        )
        
        return metrics_calculator.calculate_all()
    
    def _save_to_database(self):
        """Save backtest results to database"""
        session = get_session()
        
        try:
            # Create backtest record
            backtest = BacktestModel(
                strategy_id=None,  # Will be set if strategy is saved
                start_date=self.start_date,
                end_date=self.end_date,
                initial_capital=self.strategy.initial_capital,
                final_capital=self.strategy.get_portfolio_value(),
                total_return_percent=self.metrics.get('total_return_percent', 0),
                total_trades=len(self.trades),
                winning_trades=self.metrics.get('winning_trades', 0),
                losing_trades=self.metrics.get('losing_trades', 0),
                win_rate=self.metrics.get('win_rate', 0),
                max_drawdown=self.metrics.get('max_drawdown', 0),
                sharpe_ratio=self.metrics.get('sharpe_ratio', 0),
                sortino_ratio=self.metrics.get('sortino_ratio', 0),
                status='COMPLETED',
                completed_at=datetime.now()
            )
            
            session.add(backtest)
            session.commit()
            
            # Save trades
            for trade in self.trades:
                trade_record = TradeModel(
                    backtest_id=backtest.id,
                    symbol=trade['symbol'],
                    side=trade['side'],
                    quantity=trade['quantity'],
                    entry_price=trade['price'],
                    entry_time=trade['timestamp'],
                    brokerage=trade['brokerage'],
                    taxes=trade['stt'] + trade['gst'],
                    status='CLOSED'
                )
                session.add(trade_record)
            
            session.commit()
            logger.info(f"Backtest results saved to database (ID: {backtest.id})")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving backtest to database: {e}")
        finally:
            session.close()
    
    def get_results(self) -> Dict:
        """Get backtest results"""
        return {
            'strategy_name': self.strategy.name,
            'period': f"{self.start_date.date()} to {self.end_date.date()}",
            'initial_capital': self.strategy.initial_capital,
            'final_capital': self.strategy.get_portfolio_value(),
            'total_return': self.metrics.get('total_return_percent', 0),
            'total_trades': len(self.trades),
            'metrics': self.metrics,
            'equity_curve': self.equity_curve
        }
