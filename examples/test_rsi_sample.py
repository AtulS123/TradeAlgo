"""
RSI Strategy Test on RELIANCE with Sample Data
(Token expired - using realistic sample data)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("\n" + "="*70)
print("RSI STRATEGY BACKTEST - RELIANCE (Sample Data)")
print("="*70 + "\n")

# Generate realistic RELIANCE data
print("📊 Generating realistic RELIANCE price data...")

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
dates = pd.date_range(start=start_date, end=end_date, freq='5T')  # 5-minute intervals

# Realistic RELIANCE price movement
np.random.seed(42)
base_price = 2500
returns = np.random.normal(0.0001, 0.002, len(dates))
prices = base_price * (1 + returns).cumprod()

# Add oscillation for RSI signals
prices = prices + 30 * np.sin(np.arange(len(dates)) / 100)

df = pd.DataFrame({
    'open': prices * (1 + np.random.uniform(-0.002, 0.002, len(dates))),
    'high': prices * (1 + np.random.uniform(0.002, 0.005, len(dates))),
    'low': prices * (1 + np.random.uniform(-0.005, -0.002, len(dates))),
    'close': prices,
    'volume': np.random.randint(100000, 500000, len(dates))
}, index=dates)

print(f"✅ Generated {len(df)} bars (5-minute candles)\n")

# Calculate RSI
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

df['rsi'] = calculate_rsi(df['close'])

# Backtest
print("🚀 Running RSI backtest...")
print(f"   Period: {start_date.date()} to {end_date.date()}")
print(f"   Timeframe: 5-minute")
print(f"   Strategy: Buy RSI<30, Sell RSI>70\n")

capital = 100000
position = 0
trades = []
equity_curve = [capital]

for i in range(15, len(df)):
    current_rsi = df['rsi'].iloc[i]
    prev_rsi = df['rsi'].iloc[i-1]
    price = df['close'].iloc[i]
    timestamp = df.index[i]
    
    # Buy signal
    if prev_rsi >= 30 and current_rsi < 30 and position == 0:
        quantity = int(20000 / price)
        cost = quantity * price * 1.001
        
        if capital >= cost:
            position = quantity
            capital -= cost
            trades.append({
                'time': timestamp,
                'action': 'BUY',
                'price': price,
                'quantity': quantity,
                'rsi': current_rsi
            })
    
    # Sell signal
    elif prev_rsi <= 70 and current_rsi > 70 and position > 0:
        proceeds = position * price * 0.999
        capital += proceeds
        trades.append({
            'time': timestamp,
            'action': 'SELL',
            'price': price,
            'quantity': position,
            'rsi': current_rsi
        })
        position = 0
    
    # Track equity
    portfolio_value = capital + (position * price if position > 0 else 0)
    equity_curve.append(portfolio_value)

# Final value
final_value = capital + (position * df['close'].iloc[-1] if position > 0 else 0)

# Results
print("="*70)
print("BACKTEST RESULTS")
print("="*70)
print(f"\n💰 Performance:")
print(f"   Initial Capital:  ₹{100000:>12,.2f}")
print(f"   Final Value:      ₹{final_value:>12,.2f}")
print(f"   Total Return:     {((final_value - 100000) / 100000 * 100):>12.2f}%")
print(f"   Max Equity:       ₹{max(equity_curve):>12,.2f}")
print(f"   Min Equity:       ₹{min(equity_curve):>12,.2f}")

print(f"\n📈 Trading Activity:")
print(f"   Total Trades:     {len(trades):>12}")
print(f"   Buy Trades:       {sum(1 for t in trades if t['action'] == 'BUY'):>12}")
print(f"   Sell Trades:      {sum(1 for t in trades if t['action'] == 'SELL'):>12}")

if trades:
    print(f"\n📋 Sample Trades:")
    print("-" * 70)
    for trade in trades[:10]:  # First 10 trades
        print(f"   {trade['time'].strftime('%Y-%m-%d %H:%M')} | "
              f"{trade['action']:4} | ₹{trade['price']:>8,.2f} | "
              f"Qty: {trade['quantity']:>3} | RSI: {trade['rsi']:>5.1f}")
    if len(trades) > 10:
        print(f"   ... and {len(trades) - 10} more trades")

print("\n" + "="*70)
print("\n✅ RSI Strategy demonstration complete!")
print("\nNote: This used sample data. For real Kite API data:")
print("  1. Get new request token from Kite login")
print("  2. Run: python examples/test_rsi_reliance.py NEW_TOKEN\n")
