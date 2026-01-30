import pandas as pd
from datetime import date

df = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv')
df['datetime'] = pd.to_datetime(df['date'])
df.set_index('datetime', inplace=True)

df_5min = df.resample('5min').agg({
    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'
}).dropna()

df_5min['date'] = df_5min.index.date
df_5min['time'] = df_5min.index.time
df_5min['minutes_since_915'] = df_5min.index.hour * 60 + df_5min.index.minute - (9*60 + 15)
df_5min.reset_index(inplace=True)

# Get first candle
first_candles = df_5min[df_5min['minutes_since_915'] == 0].copy()

# Check Jan 24
jan24 = date(2025, 1, 24)
jan24_first = first_candles[first_candles['date'] == jan24]

print("First candle for Jan 24 (minutes_since_915 == 0):")
print(jan24_first[['date', 'time', 'minutes_since_915', 'open', 'close']])

# Check prev day
jan23 = date(2025, 1, 23)
daily = df_5min.groupby('date').agg({'high': 'max', 'low': 'min'}).reset_index()
jan23_row = daily[daily['date'] == jan23]
prev_high = jan23_row['high'].values[0]

print(f"\nPrev high: {prev_high:.2f}")
if len(jan24_first) > 0:
    fc_close = jan24_first['close'].values[0]
    print(f"First candle close: {fc_close:.2f}")
    
    if fc_close > prev_high:
        print("CLASS: ABOVE")
    else:
        print("CLASS: NOT ABOVE")
