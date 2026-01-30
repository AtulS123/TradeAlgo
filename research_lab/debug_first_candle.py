"""
Test if first_candle is correctly capturing the 9:15-9:20 candle
"""
import pandas as pd
from datetime import date, time

df = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv')
df['datetime'] = pd.to_datetime(df['date'])
df.set_index('datetime', inplace=True)

df_5min_full = df.resample('5T', closed='left', label='left').agg({
    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'
}).dropna()

df_5min_full.reset_index(inplace=True)
df_5min_full['date'] = df_5min_full['datetime'].dt.date
df_5min_full['time'] = df_5min_full['datetime'].dt.time

# Get first candle using groupby
first_candle = df_5min_full.groupby('date').first()

# Check Jan 24, 2025
jan24_date = date(2025, 1, 24)
jan24_all = df_5min_full[df_5min_full['date'] == jan24_date]

print("All 5-min candles for Jan 24, 2025 (first 3):")
print(jan24_all[['datetime', 'time', 'open', 'high', 'low', 'close']].head(3))

print("\nFirst candle from groupby:")
if jan24_date in first_candle.index:
    fc = first_candle.loc[jan24_date]
    print(f"Time: {fc['time']}, Open: {fc['open']:.2f}, Close: {fc['close']:.2f}")

# Also check what minutes_since_915 == 0 gives us
df_5min_full['minutes_since_915'] = (df_5min_full['datetime'].dt.hour * 60 + df_5min_full['datetime'].dt.minute) - (9 * 60 + 15)
jan24_915 = jan24_all[jan24_all['minutes_since_915'] == 0]

print("\nCandle with minutes_since_915 == 0:")
if len(jan24_915) > 0:
    print(jan24_915[['datetime', 'time', 'open', 'high', 'low', 'close']])

# Get prev day high
jan23_data = df_5min_full[df_5min_full['date'] == date(2025, 1, 23)]
prev_high = jan23_data['high'].max()
print(f"\nJan 23 prev_high: {prev_high:.2f}")

# Check classification
if jan24_date in first_candle.index:
    fc_close = first_candle.loc[jan24_date]['close']
    print(f"First candle close: {fc_close:.2f}")
    if fc_close > prev_high:
        print("Classification: ABOVE")
    else:
        print("Classification: INSIDE or BELOW")
