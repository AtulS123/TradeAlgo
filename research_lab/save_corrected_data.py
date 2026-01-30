"""
Get all corrected values and save to JSON for HTML update
"""

import pandas as pd
import numpy as np
import json

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

touched_high_first['pct_above_high'] = ((touched_high_first['day_high'] - touched_high_first['prev_high']) / touched_high_first['prev_range']) * 100

high_stayed_within_10pct = touched_high_first[touched_high_first['pct_above_high'] < 10].copy()
high_went_10pct_above = touched_high_first[touched_high_first['pct_above_high'] >= 10].copy()

# Touched LOW first
touched_low_first = inside_days[
    (inside_days['time_to_low'].notna()) &
    ((inside_days['time_to_high'].isna()) | (inside_days['time_to_low'] < inside_days['time_to_high']))
].copy()

touched_low_first['pct_below_low'] = ((touched_low_first['prev_low'] - touched_low_first['day_low']) / touched_low_first['prev_range']) * 100

low_stayed_within_10pct = touched_low_first[touched_low_first['pct_below_low'] < 10].copy()
low_went_10pct_below = touched_low_first[touched_low_first['pct_below_low'] >= 10].copy()

# Stayed inside
stayed_inside = inside_days[
    (inside_days['day_high'] < inside_days['prev_high']) &
    (inside_days['day_low'] > inside_days['prev_low'])
].copy()

stayed_inside['pct_range'] = (stayed_inside['day_range'] / stayed_inside['prev_range']) * 100
stayed_inside['gap_from_high'] = ((stayed_inside['prev_high'] - stayed_inside['day_high']) / stayed_inside['prev_range']) * 100
stayed_inside['gap_from_low'] = ((stayed_inside['day_low'] - stayed_inside['prev_low']) / stayed_inside['prev_range']) * 100

# Build JSON output
output = {
    "row1_stayed_within_10pct_above": {
        "count": len(high_stayed_within_10pct),
        "probability": round(len(high_stayed_within_10pct) / len(touched_high_first) * 100, 1),
        "vix": round(high_stayed_within_10pct['vix'].median(), 2),
        "dates": [str(d) for d in high_stayed_within_10pct.sort_values('date', ascending=False).head(5)['date'].tolist()]
    },
    "row2_went_10pct_above": {
        "count": len(high_went_10pct_above),
        "probability": round(len(high_went_10pct_above) / len(touched_high_first) * 100, 1),
        "vix": round(high_went_10pct_above['vix'].median(), 2),
        "dates": [str(d) for d in high_went_10pct_above.sort_values('date', ascending=False).head(5)['date'].tolist()]
    },
    "row3_stayed_within_10pct_below": {
        "count": len(low_stayed_within_10pct),
        "probability": round(len(low_stayed_within_10pct) / len(touched_low_first) * 100, 1),
        "vix": round(low_stayed_within_10pct['vix'].median(), 2),
        "dates": [str(d) for d in low_stayed_within_10pct.sort_values('date', ascending=False).head(5)['date'].tolist()]
    },
    "row4_went_10pct_below": {
        "count": len(low_went_10pct_below),
        "probability": round(len(low_went_10pct_below) / len(touched_low_first) * 100, 1),
        "vix": round(low_went_10pct_below['vix'].median(), 2),
        "dates": [str(d) for d in low_went_10pct_below.sort_values('date', ascending=False).head(5)['date'].tolist()]
    },
    "row5_stayed_inside": {
        "count": len(stayed_inside),
        "probability": round(len(stayed_inside) / len(inside_days) * 100, 1),
        "vix": round(stayed_inside['vix'].median(), 2),
        "avg_pct_range": round(stayed_inside['pct_range'].mean(), 1),
        "avg_gap_from_high": round(stayed_inside['gap_from_high'].mean(), 1),
        "avg_gap_from_low": round(stayed_inside['gap_from_low'].mean(), 1),
        "dates": [str(d) for d in stayed_inside.sort_values('date', ascending=False).head(5)['date'].tolist()]
    }
}

# Save to JSON
with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\corrected_data.json', 'w') as f:
    json.dump(output, f, indent=2)

print("✅ Corrected data saved to corrected_data.json")
print(json.dumps(output, indent=2))
