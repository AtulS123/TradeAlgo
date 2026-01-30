"""
Debug specific date: 2019-10-10
Analyze why it was classified into Row 4 (touched low -> went >=10% below)
"""

import pandas as pd
import numpy as np

# Load NIFTY data
df = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv')
df['datetime'] = pd.to_datetime(df['date'])
df = df.sort_values('datetime').reset_index(drop=True)

# Resample to 5-min
df.set_index('datetime', inplace=True)
df_5min = df.resample('5min').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last'
}).dropna()

df_5min['date'] = df_5min.index.date
df_5min['time'] = df_5min.index.time
df_5min.reset_index(inplace=True)

# Get data for 2019-10-09 (prev day) and 2019-10-10 (current day)
target_date = pd.to_datetime('2019-10-10').date()
prev_date_candidate = pd.to_datetime('2019-10-09').date()

print(f"Analyzing {target_date}...")

# Get daily stats
daily_df = df_5min.groupby('date').agg({
    'high': 'max',
    'low': 'min',
    'open': 'first',
    'close': 'last'
}).reset_index()

day_idx = daily_df[daily_df['date'] == target_date].index[0]
today = daily_df.iloc[day_idx]
prev_day = daily_df.iloc[day_idx-1]

print("\nPrevious Day Stats:")
print(f"Date: {prev_day['date']}")
print(f"High: {prev_day['high']}")
print(f"Low: {prev_day['low']}")
print(f"Range: {prev_day['high'] - prev_day['low']:.2f}")

print(f"\nTarget Day Stats ({today['date']}):")
print(f"Open: {today['open']}")
print(f"High: {today['high']}")
print(f"Low: {today['low']}")

print(f"P_LOW: {prev_day['low']}")
print(f"T_LOW: {today['low']}")
print(f"TOUCH: {'YES' if today['low'] <= prev_day['low'] else 'NO'}")

prev_range = prev_day['high'] - prev_day['low']
threshold = prev_day['low'] - (0.10 * prev_range)
print(f"THRESH: {threshold}")
print(f"BELOW_THRESH: {'YES' if today['low'] <= threshold else 'NO'}")
