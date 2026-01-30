"""
Debug July 23, 2025 and check 2nd order classification logic
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
    'close': 'last',
    'volume': 'sum'
}).dropna()

df_5min['date'] = df_5min.index.date
df_5min.reset_index(inplace=True)

# Daily aggregation
daily = df_5min.groupby('date').agg({
    'high': 'max',
    'low': 'min',
    'open': 'first',
    'close': 'last'
}).reset_index()
daily.columns = ['date', 'day_high', 'day_low', 'day_open', 'day_close']

daily['prev_high'] = daily['day_high'].shift(1)
daily['prev_low'] = daily['day_low'].shift(1)
daily = daily.dropna()
daily['prev_range'] = daily['prev_high'] - daily['prev_low']

# Check July 23, 2025
from datetime import date
target_date = date(2025, 7, 23)
if target_date in daily['date'].values:
    row = daily[daily['date'] == target_date].iloc[0]
    print(f"July 23, 2025 Data:")
    print(f"  Prev High: {row['prev_high']:.2f}")
    print(f"  Prev Low: {row['prev_low']:.2f}")
    print(f"  Prev Range: {row['prev_range']:.2f}")
    print(f"  Day High: {row['day_high']:.2f}")
    print(f"  Day Low: {row['day_low']:.2f}")
    print(f"  Day Open: {row['day_open']:.2f}")
    
    # Calculate how much above prev high
    above_high = row['day_high'] - row['prev_high']
    pct_of_range = (above_high / row['prev_range']) * 100
    print(f"\n  Went {above_high:.2f} points above prev high")
    print(f"  That's {pct_of_range:.1f}% of prev day range")
    
    # Check if touched prev low
    touched_low = row['day_low'] <= row['prev_low']
    print(f"  Touched prev low? {touched_low}")
    
    # Current (wrong) classification
    if touched_low:
        print(f"\n  CURRENT LOGIC: Classified as 'touched low without going >=10% above'")
    
    # Correct classification
    if pct_of_range >= 10:
        print(f"  CORRECT CLASSIFICATION: Should be 'goes >=10% above prev high'")
    else:
        print(f"  CORRECT CLASSIFICATION: Should be 'touches low without going >=10% above'")
else:
    print("July 23, 2025 not found in data")

print("\n" + "="*80)
print("CORRECT 2nd ORDER LOGIC:")
print("="*80)
print("For days that touched HIGH first:")
print("  1. Calculate: (day_high - prev_high) / prev_range")
print("  2. If >= 10%: Row 2 (goes >=10% above)")
print("  3. If < 10%: Row 1 (touches low without going >=10% above)")
print("\nThis is INDEPENDENT of whether it also touched the low!")
print("The classification is based ONLY on magnitude of move above high.")
