"""
Calculate Row 5 (Stayed Inside) statistics
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
daily['day_range'] = daily['day_high'] - daily['day_low']

# Load VIX
vix = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\INDIA VIX_minute.csv')
vix['datetime'] = pd.to_datetime(vix['date'])
vix['date'] = vix['datetime'].dt.date
vix_daily = vix.groupby('date').agg({'close': 'last'}).reset_index()
vix_daily = vix_daily.rename(columns={'close': 'vix'})
daily = daily.merge(vix_daily, on='date', how='left')

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

# Row 5: Stayed inside (neither high nor low touched)
stayed_inside = inside_days[
    (inside_days['day_high'] < inside_days['prev_high']) &
    (inside_days['day_low'] > inside_days['prev_low'])
].copy()

print("="*80)
print("ROW 5: STAYED INSIDE (Neither high nor low touched)")
print("="*80)

print(f"\nCount: {len(stayed_inside)}")
print(f"Probability: {len(stayed_inside) / len(inside_days) * 100:.1f}%")

# Calculate metrics
stayed_inside['pct_range'] = (stayed_inside['day_range'] / stayed_inside['prev_range']) * 100
stayed_inside['gap_from_high'] = ((stayed_inside['prev_high'] - stayed_inside['day_high']) / stayed_inside['prev_range']) * 100
stayed_inside['gap_from_low'] = ((stayed_inside['day_low'] - stayed_inside['prev_low']) / stayed_inside['prev_range']) * 100

print(f"\nAvg % range of day compared to prev day range: {stayed_inside['pct_range'].mean():.1f}%")
print(f"Avg % gap from prev day high: {stayed_inside['gap_from_high'].mean():.1f}%")
print(f"Avg % gap from prev day low: {stayed_inside['gap_from_low'].mean():.1f}%")

print(f"\nMedian VIX: {stayed_inside['vix'].median():.2f}")

recent = stayed_inside.sort_values('date', ascending=False).head(5)
print(f"\nRecent examples:")
for _, row in recent.iterrows():
    vix_str = f"{row['vix']:.2f}" if pd.notna(row['vix']) else 'N/A'
    print(f"  {row['date']} (VIX: {vix_str}, range: {row['pct_range']:.1f}%, gap_high: {row['gap_from_high']:.1f}%, gap_low: {row['gap_from_low']:.1f}%)")

# QC Check - all percentages should add up to 100%
print("\n" + "="*80)
print("QC CHECK - All scenarios should add to 100%")
print("="*80)

# Need to get counts for all scenarios
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

inside_days_full = daily[daily['opening_position'] == 'INSIDE'].copy()

touched_high_first = inside_days_full[
    (inside_days_full['time_to_high'].notna()) &
    ((inside_days_full['time_to_low'].isna()) | (inside_days_full['time_to_high'] < inside_days_full['time_to_low']))
]

touched_low_first = inside_days_full[
    (inside_days_full['time_to_low'].notna()) &
    ((inside_days_full['time_to_high'].isna()) | (inside_days_full['time_to_low'] < inside_days_full['time_to_high']))
]

stayed_inside_full = inside_days_full[
    (inside_days_full['day_high'] < inside_days_full['prev_high']) &
    (inside_days_full['day_low'] > inside_days_full['prev_low'])
]

total = len(touched_high_first) + len(touched_low_first) + len(stayed_inside_full)
pct_high = len(touched_high_first) / len(inside_days_full) * 100
pct_low = len(touched_low_first) / len(inside_days_full) * 100
pct_stayed = len(stayed_inside_full) / len(inside_days_full) * 100

print(f"Touched HIGH first: {len(touched_high_first)} ({pct_high:.1f}%)")
print(f"Touched LOW first: {len(touched_low_first)} ({pct_low:.1f}%)")
print(f"Stayed inside: {len(stayed_inside_full)} ({pct_stayed:.1f}%)")
print(f"Total: {total} (should be {len(inside_days_full)})")
print(f"Sum of %: {pct_high + pct_low + pct_stayed:.1f}% (should be 100.0%)")
