"""
Debug version to see why Volatility and ATR strategies don't generate trades
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from kiteconnect import KiteConnect

try:
    from utils.saved_token import ACCESS_TOKEN
except:
    print("❌ No saved token found")
    exit(1)

KITE_API_KEY = "5f814cggb2e7m8z9"

print("\n🔍 DEBUGGING VOLATILITY & ATR STRATEGIES\n")

# Fetch data
kite = KiteConnect(api_key=KITE_API_KEY)
kite.set_access_token(ACCESS_TOKEN)

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

# Filter trading hours
df['hour'] = df.index.hour
df['minute'] = df.index.minute
df['time_decimal'] = df['hour'] + df['minute'] / 60
trading_hours_mask = (df['time_decimal'] >= 9.25) & (df['time_decimal'] <= 15.5)
df = df[trading_hours_mask].copy()

# Calculate ATR
df['tr'] = np.maximum(
    df['high'] - df['low'],
    np.maximum(
        abs(df['high'] - df['close'].shift()),
        abs(df['low'] - df['close'].shift())
    )
)
df['atr'] = df['tr'].rolling(14).mean()

print(f"Data ready: {len(df)} bars\n")

# Test Volatility strategy
print("="*70)
print("TESTING: Volatility Based Strategy")
print("="*70)

initial_capital = 100000
capital = initial_capital
position = 0
buy_signals = 0
trades_executed = 0

for i in range(15, min(len(df), 100)):  # Test first 100 bars
    current_rsi = df['rsi'].iloc[i]
    prev_rsi = df['rsi'].iloc[i-1]
    price = df['close'].iloc[i]
    
    # BUY SIGNAL
    if prev_rsi >= 30 and current_rsi < 30 and position == 0:
        buy_signals += 1
        print(f"\n🔔 Buy Signal #{buy_signals} at {df.index[i]}")
        print(f"   Price: ₹{price:.2f}, RSI: {current_rsi:.1f}")
        
        # Volatility calculation
        recent_prices = df['close'].iloc[max(0, i-20):i]
        if len(recent_prices) > 1:
            volatility = recent_prices.pct_change().std()
            volatility = max(volatility, 0.015)
            volatility = min(volatility, 0.03)
        else:
            volatility = 0.02
        
        print(f"   Volatility: {volatility*100:.2f}%")
        
        # Position sizing
        stop_loss = price * 0.98
        risk_per_share = price - stop_loss
        max_risk = capital * 0.02
        quantity = int(max_risk / risk_per_share)
        quantity = max(quantity, 5)
        
        cost = quantity * price * 1.001
        
        print(f"   Stop Loss: ₹{stop_loss:.2f}")
        print(f"   Risk per share: ₹{risk_per_share:.2f}")
        print(f"   Max risk (2%): ₹{max_risk:.2f}")
        print(f"   Calculated quantity: {quantity}")
        print(f"   Cost: ₹{cost:.2f}")
        print(f"   Available capital: ₹{capital:.2f}")
        
        if capital >= cost and quantity > 0:
            print(f"   ✅ TRADE EXECUTED!")
            trades_executed += 1
            position = quantity
            capital -= cost
        else:
            print(f"   ❌ TRADE REJECTED: ", end="")
            if capital < cost:
                print(f"Insufficient capital (need ₹{cost:.2f}, have ₹{capital:.2f})")
            else:
                print(f"Invalid quantity ({quantity})")

print(f"\n📊 Summary:")
print(f"   Buy signals: {buy_signals}")
print(f"   Trades executed: {trades_executed}")
print(f"   Execution rate: {(trades_executed/buy_signals*100) if buy_signals > 0 else 0:.1f}%")
