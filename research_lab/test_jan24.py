import pandas as pd
from datetime import date, time

df = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv')
df['datetime'] = pd.to_datetime(df['date'])
df.set_index('datetime', inplace=True)

df_5min = df.resample('5min', closed='left', label='left').agg({
    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'
}).dropna().reset_index()

df_5min['date'] = df_5min['datetime'].dt.date
df_5min['time'] = df_5min['datetime'].dt.time

# Get first candle per day
first_candle = df_5min.groupby('date').first()

# Check Jan 24
jan24 = date(2025, 1, 24)
jan23 = date(2025, 1, 23)

# All Jan 24 candles
jan24_all = df_5min[df_5min['date'] == jan24]
print("First 3 candles on Jan 24:")
print(jan24_all[['time', 'open', 'high', 'low', 'close']].head(3).to_string())

# What groupby gives
print("\nGroupby first candle:")
print(f"Time: {first_candle.loc[jan24, 'time']}")  
print(f"Close: {first_candle.loc[jan24, 'close']:.2f}")

# Prev high
jan23_all = df_5min[df_5min['date'] == jan23]
prev_high = jan23_all['high'].max()
print(f"\nJan 23 prev_high: {prev_high:.2f}")

# Classification
fc_close = first_candle.loc[jan24, 'close']
if fc_close > prev_high:
    print(f"RESULT: ABOVE ({fc_close:.2f} > {prev_high:.2f})")
elif fc_close < jan23_all['low'].min():
    print(f"RESULT: BELOW")
else:
    print(f"RESULT: INSIDE")
