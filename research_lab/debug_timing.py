"""
Debug timing for specific dates: 2016-01-14 and 2024-10-11
"""
import pandas as pd
import numpy as np

# Load data
df = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv')
df['datetime'] = pd.to_datetime(df['date'])
df = df.sort_values('datetime').reset_index(drop=True)

df.set_index('datetime', inplace=True)
df_5min = df.resample('5min').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last'
}).dropna()
df_5min['date'] = df_5min.index.date
df_5min['time'] = df_5min.index.time
df_5min['minutes_since_915'] = df_5min.index.hour * 60 + df_5min.index.minute - (9*60 + 15)
df_5min.reset_index(inplace=True)

# Calculate Daily
daily = df_5min.groupby('date').agg({
    'high': 'max',
    'low': 'min',
    'open': 'first',
    'close': 'last'
}).reset_index()
daily['prev_low'] = daily['low'].shift(1)
daily['prev_high'] = daily['high'].shift(1)
daily['prev_range'] = daily['prev_high'] - daily['prev_low']

dates_to_check = ['2024-10-11', '2016-01-14']

for date_str in dates_to_check:
    print(f"\n{'='*20} {date_str} {'='*20}")
    d = pd.to_datetime(date_str).date()
    
    day_row = daily[daily['date'] == d]
    if len(day_row) == 0:
        print("Date not found in daily data")
        continue
        
    prev_low = float(day_row.iloc[0]['prev_low'])
    prev_range = float(day_row.iloc[0]['prev_range'])
    threshold = prev_low - (0.10 * prev_range)
    
    print(f"Prev Low: {prev_low}")
    print(f"Prev Range: {prev_range:.2f}")
    print(f"10% Extension Threshold: {threshold:.2f}")
    
    # 5-min analysis
    day_data = df_5min[df_5min['date'] == d].copy()
    
    touched_low = day_data[day_data['low'] <= prev_low]
    if len(touched_low) == 0:
        print("Did not touch low.")
        continue
        
    first_touch_time = touched_low.iloc[0]['minutes_since_915']
    print(f"First Touch Low: {touched_low.iloc[0]['time']} (Min: {first_touch_time})")
    
    went_below = day_data[(day_data['minutes_since_915'] >= first_touch_time) & (day_data['low'] <= threshold)]
    
    if len(went_below) == 0:
        print("Did not go 10% below.")
    else:
        first_ext_time = went_below.iloc[0]['minutes_since_915']
        print(f"First 10% Ext: {went_below.iloc[0]['time']} (Min: {first_ext_time})")
        print(f"Duration: {first_ext_time - first_touch_time} min")
