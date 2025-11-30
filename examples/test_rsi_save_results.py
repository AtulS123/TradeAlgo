"""
RSI backtest on RELIANCE - Save results to file
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from kiteconnect import KiteConnect

# Load saved token
try:
    from utils.saved_token import ACCESS_TOKEN
except:
    print("❌ No saved token found")
    exit(1)

KITE_API_KEY = "5f814cggb2e7m8z9"

# Output file
output_file = "backtest_results/rsi_reliance_results.txt"
os.makedirs(os.path.dirname(output_file), exist_ok=True)

def log(message):
    """Print and save to file"""
    print(message)
    with open(output_file, 'a') as f:
        f.write(message + '\n')

# Clear previous results
open(output_file, 'w').close()

log("\n" + "="*70)
log("RSI STRATEGY BACKTEST - RELIANCE (Real Kite Data)")
log("="*70 + "\n")

# Authenticate
log("🔐 Using saved access token...")
kite = KiteConnect(api_key=KITE_API_KEY)
kite.set_access_token(ACCESS_TOKEN)
log("✅ Authenticated!\n")

# Fetch data
log("📥 Fetching RELIANCE data from Kite API...")
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

instruments = kite.instruments("NSE")
reliance = next((inst for inst in instruments if inst['tradingsymbol'] == 'RELIANCE'), None)

data = kite.historical_data(
    instrument_token=reliance['instrument_token'],
    from_date=start_date,
    to_date=end_date,
    interval="5minute"
)

df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)

log(f"✅ Fetched {len(df):,} bars of real market data\n")

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
log("🚀 Running RSI backtest...")
log(f"   Period: {df.index[0].date()} to {df.index[-1].date()}")
log(f"   Timeframe: 5-minute candles")
log(f"   Strategy: Buy when RSI < 30, Sell when RSI > 70\n")

capital = 100000
position = 0
trades = []
equity_curve = [capital]

for i in range(15, len(df)):
    current_rsi = df['rsi'].iloc[i]
    prev_rsi = df['rsi'].iloc[i-1]
    price = df['close'].iloc[i]
    timestamp = df.index[i]
    
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
    
    portfolio_value = capital + (position * price if position > 0 else 0)
    equity_curve.append(portfolio_value)

final_value = capital + (position * df['close'].iloc[-1] if position > 0 else 0)

# Results
log("="*70)
log("BACKTEST RESULTS - REAL MARKET DATA")
log("="*70)
log(f"\n💰 Performance:")
log(f"   Initial Capital:  ₹{100000:>12,.2f}")
log(f"   Final Value:      ₹{final_value:>12,.2f}")
log(f"   Total Return:     {((final_value - 100000) / 100000 * 100):>12.2f}%")
log(f"   Max Equity:       ₹{max(equity_curve):>12,.2f}")
log(f"   Min Equity:       ₹{min(equity_curve):>12,.2f}")

log(f"\n📈 Trading Activity:")
log(f"   Total Trades:     {len(trades):>12}")
log(f"   Buy Trades:       {sum(1 for t in trades if t['action'] == 'BUY'):>12}")
log(f"   Sell Trades:      {sum(1 for t in trades if t['action'] == 'SELL'):>12}")
log(f"   Current Position: {position:>12} shares")

if trades:
    log(f"\n📋 All Trades:")
    log("-" * 70)
    for trade in trades:
        log(f"   {trade['time'].strftime('%Y-%m-%d %H:%M')} | "
              f"{trade['action']:4} | ₹{trade['price']:>8,.2f} | "
              f"Qty: {trade['quantity']:>3} | RSI: {trade['rsi']:>5.1f}")

log("\n" + "="*70)
log(f"\n✅ Results saved to: {output_file}\n")

print(f"\n📄 Full results saved to: {output_file}")
print("   Open this file to see complete backtest details!")
