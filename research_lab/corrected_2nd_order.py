"""
CORRECTED 2nd order classification - based on magnitude of move, not whether touched low
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
df_5min['time'] = df_5min.index.time
df_5min['minutes_since_915'] = df_5min.index.hour * 60 + df_5min.index.minute - (9*60 + 15)
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

# Load VIX
vix = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\INDIA VIX_minute.csv')
vix['datetime'] = pd.to_datetime(vix['date'])
vix['date'] = vix['datetime'].dt.date
vix_daily = vix.groupby('date').agg({'close': 'last'}).reset_index()
vix_daily = vix_daily.rename(columns={'close': 'vix'})
daily = daily.merge(vix_daily, on='date', how='left')

# Timing
for idx, day in daily.iterrows():
    day_data = df_5min[df_5min['date'] == day['date']].copy()
    if len(day_data) == 0:
        continue
    
    touched_high = day_data[day_data['high'] >= day['prev_high']]
    if len(touched_high) > 0:
        daily.at[idx, 'time_to_high'] = touched_high.iloc[0]['minutes_since_915']
    
    touched_low = day_data[day_data['low'] <= day['prev_low']]
    if len(touched_low) > 0:
        daily.at[idx, 'time_to_low'] = touched_low.iloc[0]['minutes_since_915']

# Opening classification
def classify_open(row):
    if row['day_open'] > row['prev_high']:
        return 'ABOVE'
    elif row['day_open'] < row['prev_low']:
        return 'BELOW'
    else:
        return 'INSIDE'

daily['opening_position'] = daily.apply(classify_open, axis=1)
inside_days = daily[daily['opening_position'] == 'INSIDE'].copy()

# Touched HIGH first
touched_high_first = inside_days[
    (inside_days['time_to_high'].notna()) &
    ((inside_days['time_to_low'].isna()) | (inside_days['time_to_high'] < inside_days['time_to_low']))
].copy()

# CORRECTED 2nd order classification - based on magnitude above high
touched_high_first['pct_above_high'] = ((touched_high_first['day_high'] - touched_high_first['prev_high']) / touched_high_first['prev_range']) * 100

# Row 1: Stayed within 10% above (< 10%)
high_stayed_within_10pct = touched_high_first[touched_high_first['pct_above_high'] < 10].copy()

# Row 2: Went >= 10% above
high_went_10pct_above = touched_high_first[touched_high_first['pct_above_high'] >= 10].copy()

print("="*80)
print("TOUCHED HIGH FIRST - CORRECTED 2nd Order Classification")
print("="*80)

print(f"\nRow 1: Stayed within 10% above prev high (< 10% of range)")
print(f"  Count: {len(high_stayed_within_10pct)} ({len(high_stayed_within_10pct)/len(touched_high_first)*100:.1f}%)")
print(f"  Median VIX: {high_stayed_within_10pct['vix'].median():.2f}")
recent = high_stayed_within_10pct.sort_values('date', ascending=False).head(5)
print(f"  Recent examples:")
for _, row in recent.iterrows():
    vix_str = f"{row['vix']:.2f}" if pd.notna(row['vix']) else 'N/A'
    print(f"    {row['date']} (VIX: {vix_str}, went {row['pct_above_high']:.1f}% above)")

print(f"\nRow 2: Went >= 10% above prev high")
print(f"  Count: {len(high_went_10pct_above)} ({len(high_went_10pct_above)/len(touched_high_first)*100:.1f}%)")
print(f"  Median VIX: {high_went_10pct_above['vix'].median():.2f}")
recent = high_went_10pct_above.sort_values('date', ascending=False).head(5)
print(f"  Recent examples:")
for _, row in recent.iterrows():
    vix_str = f"{row['vix']:.2f}" if pd.notna(row['vix']) else 'N/A'
    print(f"    {row['date']} (VIX: {vix_str}, went {row['pct_above_high']:.1f}% above)")

print(f"\nQC: {len(high_stayed_within_10pct)} + {len(high_went_10pct_above)} = {len(high_stayed_within_10pct) + len(high_went_10pct_above)} (should be {len(touched_high_first)})")

# Touched LOW first - same logic
touched_low_first = inside_days[
    (inside_days['time_to_low'].notna()) &
    ((inside_days['time_to_high'].isna()) | (inside_days['time_to_low'] < inside_days['time_to_high']))
].copy()

touched_low_first['pct_below_low'] = ((touched_low_first['prev_low'] - touched_low_first['day_low']) / touched_low_first['prev_range']) * 100

low_stayed_within_10pct = touched_low_first[touched_low_first['pct_below_low'] < 10].copy()
low_went_10pct_below = touched_low_first[touched_low_first['pct_below_low'] >= 10].copy()

print("\n" + "="*80)
print("TOUCHED LOW FIRST - CORRECTED 2nd Order Classification")
print("="*80)

print(f"\nRow 3: Stayed within 10% below prev low (< 10% of range)")
print(f"  Count: {len(low_stayed_within_10pct)} ({len(low_stayed_within_10pct)/len(touched_low_first)*100:.1f}%)")
print(f"  Median VIX: {low_stayed_within_10pct['vix'].median():.2f}")
recent = low_stayed_within_10pct.sort_values('date', ascending=False).head(5)
print(f"  Recent examples:")
for _, row in recent.iterrows():
    vix_str = f"{row['vix']:.2f}" if pd.notna(row['vix']) else 'N/A'
    print(f"    {row['date']} (VIX: {vix_str}, went {row['pct_below_low']:.1f}% below)")

print(f"\nRow 4: Went >= 10% below prev low")
print(f"  Count: {len(low_went_10pct_below)} ({len(low_went_10pct_below)/len(touched_low_first)*100:.1f}%)")
print(f"  Median VIX: {low_went_10pct_below['vix'].median():.2f}")
recent = low_went_10pct_below.sort_values('date', ascending=False).head(5)
print(f"  Recent examples:")
for _, row in recent.iterrows():
    vix_str = f"{row['vix']:.2f}" if pd.notna(row['vix']) else 'N/A'
    print(f"    {row['date']} (VIX: {vix_str}, went {row['pct_below_low']:.1f}% below)")

print(f"\nQC: {len(low_stayed_within_10pct)} + {len(low_went_10pct_below)} = {len(low_stayed_within_10pct) + len(low_went_10pct_below)} (should be {len(touched_low_first)})")
