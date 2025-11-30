"""
Simple RSI backtest without config dependencies
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List

# Import only what we need
from core.order import Order, OrderManager, OrderType, OrderSide, OrderStatus
from indicators.momentum import RSI


class SimpleRSIBacktest:
    """Simple RSI backtest without heavy dependencies"""
    
    def __init__(self, symbols: List[str], capital: float = 100000):
        self.symbols = symbols
        self.initial_capital = capital
        self.capital = capital
        self.positions = {symbol: 0 for symbol in symbols}
        self.data = {}
        self.trades = []
        self.equity_curve = [capital]
        
    def run(self, start_date, end_date):
        """Run the backtest"""
        print("\n" + "="*70)
        print("RSI STRATEGY BACKTEST")
        print("="*70)
        print(f"\nSymbols: {', '.join(self.symbols)}")
        print(f"Period: {start_date.date()} to {end_date.date()}")
        print(f"Initial Capital: ₹{self.initial_capital:,.2f}\n")
        
        # Generate sample data
        print("Generating sample data...")
        for symbol in self.symbols:
            self.data[symbol] = self._generate_data(symbol, start_date, end_date)
            print(f"  ✓ {symbol}: {len(self.data[symbol])} bars")
        
        # Run backtest
        print("\nRunning backtest...")
        all_dates = sorted(set().union(*[set(self.data[s].index) for s in self.symbols]))
        
        for date in all_dates:
            for symbol in self.symbols:
                if date in self.data[symbol].index:
                    self._process_bar(symbol, date)
            
            # Record equity
            portfolio_value = self._get_portfolio_value()
            self.equity_curve.append(portfolio_value)
        
        # Calculate metrics
        self._print_results()
        
    def _generate_data(self, symbol, start_date, end_date):
        """Generate realistic sample data"""
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        np.random.seed(hash(symbol) % 2**32)
        
        base_prices = {"RELIANCE": 2500, "TCS": 3500, "INFY": 1500, "HDFCBANK": 1600}
        base_price = base_prices.get(symbol, 1000)
        
        returns = np.random.normal(0.0005, 0.015, len(dates))
        prices = base_price * (1 + returns).cumprod()
        prices = prices + 50 * np.sin(np.arange(len(dates)) / 20)  # Add oscillation for RSI signals
        
        return pd.DataFrame({
            'open': prices * (1 + np.random.uniform(-0.005, 0.005, len(dates))),
            'high': prices * (1 + np.random.uniform(0.005, 0.015, len(dates))),
            'low': prices * (1 + np.random.uniform(-0.015, -0.005, len(dates))),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
    
    def _process_bar(self, symbol, date):
        """Process a single bar"""
        df = self.data[symbol]
        idx = df.index.get_loc(date)
        
        if idx < 15:  # Need 15 bars for RSI
            return
        
        # Calculate RSI
        close_prices = df['close'].iloc[:idx+1]
        rsi = RSI(close_prices, 14)
        current_rsi = rsi.iloc[-1]
        
        current_price = df.loc[date, 'close']
        
        # Trading logic
        if current_rsi < 30 and self.positions[symbol] == 0:  # Oversold - Buy
            quantity = int(10000 / current_price)
            cost = quantity * current_price * 1.001  # Include costs
            
            if self.capital >= cost:
                self.positions[symbol] = quantity
                self.capital -= cost
                self.trades.append({
                    'date': date,
                    'symbol': symbol,
                    'action': 'BUY',
                    'quantity': quantity,
                    'price': current_price,
                    'rsi': current_rsi
                })
                
        elif current_rsi > 70 and self.positions[symbol] > 0:  # Overbought - Sell
            quantity = self.positions[symbol]
            proceeds = quantity * current_price * 0.999  # Include costs
            
            self.capital += proceeds
            self.positions[symbol] = 0
            self.trades.append({
                'date': date,
                'symbol': symbol,
                'action': 'SELL',
                'quantity': quantity,
                'price': current_price,
                'rsi': current_rsi
            })
    
    def _get_portfolio_value(self):
        """Calculate current portfolio value"""
        value = self.capital
        for symbol, quantity in self.positions.items():
            if quantity > 0:
                latest_price = self.data[symbol]['close'].iloc[-1]
                value += quantity * latest_price
        return value
    
    def _print_results(self):
        """Print backtest results"""
        final_value = self._get_portfolio_value()
        total_return = ((final_value - self.initial_capital) / self.initial_capital) * 100
        
        print("\n" + "="*70)
        print("RESULTS")
        print("="*70)
        print(f"\n💰 Performance:")
        print(f"   Initial Capital:  ₹{self.initial_capital:>12,.2f}")
        print(f"   Final Value:      ₹{final_value:>12,.2f}")
        print(f"   Total Return:     {total_return:>12.2f}%")
        
        print(f"\n📈 Trading Activity:")
        print(f"   Total Trades:     {len(self.trades):>12}")
        print(f"   Buy Trades:       {sum(1 for t in self.trades if t['action'] == 'BUY'):>12}")
        print(f"   Sell Trades:      {sum(1 for t in self.trades if t['action'] == 'SELL'):>12}")
        
        if self.trades:
            print(f"\n📊 Recent Trades:")
            for trade in self.trades[-5:]:
                print(f"   {trade['date'].date()} | {trade['action']:4} | {trade['symbol']:10} | "
                      f"₹{trade['price']:>8,.2f} | RSI: {trade['rsi']:>5.1f}")
        
        print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    backtest = SimpleRSIBacktest(
        symbols=["RELIANCE", "TCS", "INFY", "HDFCBANK"],
        capital=100000
    )
    
    backtest.run(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 11, 30)
    )
    
    print("✅ Backtest completed!\n")
