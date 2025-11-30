"""
Live API-Based Backtesting Engine
Fetches data from Kite API on-demand during backtest
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
from kiteconnect import KiteConnect

from core.strategy import Strategy
from core.order import Order, OrderType, OrderStatus, OrderSide
from utils.logger import logger
from utils.config import config


class LiveAPIBacktest:
    """
    Backtesting engine that fetches data from Kite API on-demand
    Perfect for options strategies and testing with latest data
    """
    
    def __init__(
        self,
        strategy: Strategy,
        kite: KiteConnect,
        start_date: datetime,
        end_date: datetime,
        interval: str = "minute",
        slippage_percent: float = 0.1,
        brokerage_percent: float = 0.03
    ):
        """
        Initialize live API backtest
        
        Args:
            strategy: Strategy to backtest
            kite: Authenticated KiteConnect instance
            start_date: Backtest start date
            end_date: Backtest end date
            interval: Data interval (minute, 5minute, 15minute, day)
            slippage_percent: Slippage percentage
            brokerage_percent: Brokerage percentage
        """
        self.strategy = strategy
        self.kite = kite
        self.start_date = start_date
        self.end_date = end_date
        self.interval = interval
        self.slippage_percent = slippage_percent
        self.brokerage_percent = brokerage_percent
        
        self.trades = []
        self.equity_curve = [strategy.initial_capital]
        
        logger.info(f"Live API Backtest initialized: {start_date} to {end_date}")
    
    def fetch_data(self, symbol: str, exchange: str = "NSE") -> pd.DataFrame:
        """
        Fetch historical data from Kite API
        
        Args:
            symbol: Trading symbol
            exchange: Exchange (NSE, NFO, etc.)
            
        Returns:
            DataFrame with OHLCV data
        """
        print(f"📥 Fetching {symbol} data from Kite API...", end=' ', flush=True)
        
        try:
            # Get instrument token
            instruments = self.kite.instruments(exchange)
            instrument = next((inst for inst in instruments if inst['tradingsymbol'] == symbol), None)
            
            if not instrument:
                print(f"❌ Not found")
                return pd.DataFrame()
            
            # Fetch historical data
            data = self.kite.historical_data(
                instrument_token=instrument['instrument_token'],
                from_date=self.start_date,
                to_date=self.end_date,
                interval=self.interval
            )
            
            if data:
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df.rename(columns={'date': 'timestamp'}, inplace=True)
                
                print(f"✅ {len(df)} bars")
                return df
            else:
                print(f"⚠️  No data")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")
            return pd.DataFrame()
    
    def run(self):
        """Run the backtest"""
        print("\n" + "="*70)
        print("LIVE API BACKTEST")
        print("="*70)
        print(f"\nStrategy: {self.strategy.name}")
        print(f"Period: {self.start_date.date()} to {self.end_date.date()}")
        print(f"Interval: {self.interval}")
        print(f"Symbols: {', '.join(self.strategy.symbols)}\n")
        
        # Fetch data for all symbols from API
        print("📊 Fetching data from Kite API...")
        print("-" * 70)
        
        for symbol in self.strategy.symbols:
            df = self.fetch_data(symbol)
            if not df.empty:
                self.strategy.set_data(symbol, df)
        
        print("-" * 70)
        
        # Run backtest logic
        print("\n🚀 Running backtest...\n")
        
        # Get all timestamps
        all_timestamps = set()
        for symbol in self.strategy.symbols:
            if symbol in self.strategy.data:
                all_timestamps.update(self.strategy.data[symbol].index)
        
        all_timestamps = sorted(all_timestamps)
        
        # Process each timestamp
        for i, timestamp in enumerate(all_timestamps):
            # Update current bar for each symbol
            for symbol in self.strategy.symbols:
                if symbol in self.strategy.data:
                    data = self.strategy.data[symbol]
                    if timestamp in data.index:
                        bar = data.loc[timestamp]
                        self.strategy.current_bar[symbol] = data.index.get_loc(timestamp)
                        self.strategy.on_data(symbol, bar)
            
            # Execute pending orders
            self._execute_pending_orders(timestamp)
            
            # Record equity
            portfolio_value = self.strategy.get_portfolio_value()
            self.equity_curve.append(portfolio_value)
            
            # Progress indicator
            if i % 1000 == 0:
                print(f"  Progress: {i}/{len(all_timestamps)} bars processed", end='\r')
        
        print(f"  Progress: {len(all_timestamps)}/{len(all_timestamps)} bars processed ✅\n")
        
        # Calculate metrics
        final_value = self.strategy.get_portfolio_value()
        total_return = ((final_value - self.strategy.initial_capital) / self.strategy.initial_capital) * 100
        
        # Print results
        print("="*70)
        print("BACKTEST RESULTS")
        print("="*70)
        print(f"\n💰 Performance:")
        print(f"   Initial Capital:  ₹{self.strategy.initial_capital:>12,.2f}")
        print(f"   Final Value:      ₹{final_value:>12,.2f}")
        print(f"   Total Return:     {total_return:>12.2f}%")
        print(f"\n📈 Trading:")
        print(f"   Total Trades:     {len(self.trades):>12}")
        print("="*70 + "\n")
        
        return {
            'final_value': final_value,
            'total_return': total_return,
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }
    
    def _execute_pending_orders(self, timestamp):
        """Execute pending orders"""
        pending_orders = self.strategy.order_manager.get_pending_orders()
        
        for order in pending_orders:
            symbol = order.symbol
            
            if symbol not in self.strategy.data:
                continue
            
            data = self.strategy.data[symbol]
            if timestamp not in data.index:
                continue
            
            bar = data.loc[timestamp]
            
            # Determine execution price
            if order.order_type == OrderType.MARKET:
                execution_price = bar['open']
                if order.side == OrderSide.BUY:
                    execution_price *= (1 + self.slippage_percent / 100)
                else:
                    execution_price *= (1 - self.slippage_percent / 100)
            else:
                continue  # Skip limit/stop orders for now
            
            # Calculate costs
            trade_value = order.quantity * execution_price
            brokerage = trade_value * (self.brokerage_percent / 100)
            total_cost = brokerage * 1.18  # Include GST
            
            # Check capital
            if order.side == OrderSide.BUY:
                required = trade_value + total_cost
                if self.strategy.capital < required:
                    order.reject("Insufficient capital")
                    continue
            
            # Fill order
            order.fill(order.quantity, execution_price)
            self.strategy.on_order_fill(order)
            self.strategy.capital -= total_cost
            
            # Record trade
            self.trades.append({
                'timestamp': timestamp,
                'symbol': symbol,
                'side': order.side.value,
                'quantity': order.quantity,
                'price': execution_price,
                'cost': total_cost
            })


def create_authenticated_kite(request_token: str) -> Optional[KiteConnect]:
    """
    Create authenticated Kite instance
    
    Args:
        request_token: Request token from Kite login
        
    Returns:
        Authenticated KiteConnect instance or None
    """
    api_key = config.kite_api_key
    api_secret = config.kite_api_secret
    
    if not api_key or not api_secret:
        print("❌ Error: KITE_API_KEY or KITE_API_SECRET not found in environment variables.")
        return None
        
    kite = KiteConnect(api_key=api_key)
    
    try:
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        kite.set_access_token(access_token)
        print(f"✅ Authenticated with Kite API")
        return kite
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None


# Example usage
if __name__ == "__main__":
    print("\n" + "="*70)
    print("Live API Backtesting - Example")
    print("="*70 + "\n")
    
    print("This script requires a valid Kite request token.")
    print("Run: python scripts/download_kite_data.py to get one\n")
    
    if len(sys.argv) > 1:
        request_token = sys.argv[1]
        kite = create_authenticated_kite(request_token)
        
        if kite:
            print("\n✅ Ready to backtest with live API data!")
            print("Import this module in your backtest scripts.\n")
    else:
        print("Usage: python core/live_api_backtest.py YOUR_REQUEST_TOKEN\n")
