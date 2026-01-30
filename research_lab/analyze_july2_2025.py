"""
Analyze what happened on July 2nd, 2025
"""
import pandas as pd
import numpy as np
from datetime import date, time

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
    'close': 'last',
    'volume': 'sum'
}).dropna()

df_5min['date'] = df_5min.index.date
df_5min['time'] = df_5min.index.time
df_5min['minutes_since_915'] = df_5min.index.hour * 60 + df_5min.index.minute - (9*60 + 15)
df_5min.reset_index(inplace=True)

# Filter for July 2, 2025
target_date = date(2025, 7, 2)
july2_data = df_5min[df_5min['date'] == target_date].copy()

# Get previous day (July 1, 2025)
prev_date = date(2025, 7, 1)
july1_data = df_5min[df_5min['date'] == prev_date].copy()

if len(july1_data) == 0:
    print(f"ERROR: No data for previous day {prev_date}")
    exit(1)

if len(july2_data) == 0:
    print(f"ERROR: No data for {target_date}")
    exit(1)

# Calculate previous day high/low
prev_high = july1_data['high'].max()
prev_low = july1_data['low'].min()
prev_mid = (prev_high + prev_low) / 2
prev_range = prev_high - prev_low

# Get first 5-min candle
first_candle = july2_data[july2_data['minutes_since_915'] == 0].iloc[0]

# Day stats
day_high = july2_data['high'].max()
day_low = july2_data['low'].min()
day_open = july2_data['open'].iloc[0]
day_close = july2_data['close'].iloc[-1]

print("=" * 80)
print(f"ANALYSIS FOR JULY 2, 2025")
print("=" * 80)

print(f"\n📊 PREVIOUS DAY (July 1, 2025) LEVELS:")
print(f"  High: {prev_high:.2f}")
print(f"  Mid:  {prev_mid:.2f}")
print(f"  Low:  {prev_low:.2f}")
print(f"  Range: {prev_range:.2f}")

print(f"\n🕒 FIRST 5-MIN CANDLE (9:15-9:20 AM):")
print(f"  Open:  {first_candle['open']:.2f}")
print(f"  High:  {first_candle['high']:.2f}")
print(f"  Low:   {first_candle['low']:.2f}")
print(f"  Close: {first_candle['close']:.2f}")

print(f"\n📈 FULL DAY STATS (July 2, 2025):")
print(f"  Day High:  {day_high:.2f}")
print(f"  Day Low:   {day_low:.2f}")
print(f"  Day Open:  {day_open:.2f}")
print(f"  Day Close: {day_close:.2f}")

# Classification
if first_candle['close'] > prev_high:
    opening_position = 'ABOVE'
elif first_candle['close'] < prev_low:
    opening_position = 'BELOW'
else:
    opening_position = 'INSIDE'

print(f"\n🎯 CLASSIFICATION:")
print(f"  Opening Position: {opening_position}")
print(f"  (Based on first 5-min candle CLOSE at {first_candle['close']:.2f})")

# Detailed analysis for INSIDE days
if opening_position == 'INSIDE':
    # Check what happened during the day
    touched_high = july2_data[july2_data['high'] >= prev_high]
    touched_low = july2_data[july2_data['low'] <= prev_low]
    
    print(f"\n📍 INSIDE DAY ANALYSIS:")
    
    if len(touched_high) > 0:
        time_to_high = touched_high.iloc[0]['minutes_since_915']
        print(f"  ✓ Touched prev day HIGH at {time_to_high} minutes ({touched_high.iloc[0]['time']})")
    else:
        print(f"  ✗ Did NOT touch prev day high")
        time_to_high = None
        
    if len(touched_low) > 0:
        time_to_low = touched_low.iloc[0]['minutes_since_915']
        print(f"  ✓ Touched prev day LOW at {time_to_low} minutes ({touched_low.iloc[0]['time']})")
    else:
        print(f"  ✗ Did NOT touch prev day low")
        time_to_low = None
    
    # Determine which was touched first
    if time_to_high is not None and time_to_low is not None:
        if time_to_high < time_to_low:
            print(f"\n  → Touched HIGH FIRST (Row 1-2 scenarios)")
            
            # Check for 10% extension
            threshold_above = prev_high + 0.1 * prev_range
            after_high = july2_data[july2_data['minutes_since_915'] >= time_to_high]
            went_above = after_high[after_high['close'] >= threshold_above]
            
            if len(went_above) > 0:
                print(f"  → Went ≥10% above prev high (close >= {threshold_above:.2f})")
                time_ext = went_above.iloc[0]['minutes_since_915']
                
                # Check if touched mid before extension
                between = after_high[after_high['minutes_since_915'] <= time_ext]
                touched_mid = between[between['low'] <= prev_mid]
                
                if len(touched_mid) > 0:
                    print(f"  → Category: ROW 2 - Went ≥10% above AFTER touching mid")
                else:
                    print(f"  → Category: ROW 2 - Went ≥10% above BEFORE touching mid")
            else:
                print(f"  → Did NOT go ≥10% above prev high")
                print(f"  → Category: ROW 1 - Stayed within 10% above prev high")
                
        else:
            print(f"\n  → Touched LOW FIRST (Row 3-4 scenarios)")
            
            # Check for 10% extension
            threshold_below = prev_low - 0.1 * prev_range
            after_low = july2_data[july2_data['minutes_since_915'] >= time_to_low]
            went_below = after_low[after_low['close'] <= threshold_below]
            
            if len(went_below) > 0:
                print(f"  → Went ≥10% below prev low (close <= {threshold_below:.2f})")
                time_ext = went_below.iloc[0]['minutes_since_915']
                
                # Check if touched mid before extension
                between = after_low[after_low['minutes_since_915'] <= time_ext]
                touched_mid = between[between['high'] >= prev_mid]
                
                if len(touched_mid) > 0:
                    print(f"  → Category: ROW 4 - Went ≥10% below AFTER touching mid")
                else:
                    print(f"  → Category: ROW 4 - Went ≥10% below BEFORE touching mid")
            else:
                print(f"  → Did NOT go ≥10% below prev low")
                print(f"  → Category: ROW 3 - Stayed within 10% below prev low")
                
    elif time_to_high is not None:
        print(f"\n  → Only touched HIGH (not low)")
        print(f"  → Category: Part of Row 1-2 analysis")
    elif time_to_low is not None:
        print(f"\n  → Only touched LOW (not high)")
        print(f"  → Category: Part of Row 3-4 analysis")
    else:
        print(f"\n  → Stayed within range all day")
        pct_range = ((day_high - day_low) / prev_range) * 100
        print(f"  → Day's range was {pct_range:.1f}% of previous day's range")
        print(f"  → Category: ROW 5 - Stayed inside prev day range")

# Check closing position
print(f"\n📍 CLOSING POSITION:")
if day_close > prev_high:
    print(f"  Closed ABOVE prev day high ({day_close:.2f} > {prev_high:.2f})")
    print(f"  → Part of 'Close: Top of Prev Day High' analysis")
elif day_close < prev_low:
    print(f"  Closed BELOW prev day low ({day_close:.2f} < {prev_low:.2f})")
    print(f"  → Part of 'Close: Below Prev Day Low' analysis")
else:
    print(f"  Closed INSIDE prev day range")

print("\n" + "=" * 80)
