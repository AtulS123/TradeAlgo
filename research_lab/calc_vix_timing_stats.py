"""
Calculate VIX and timing statistics - EXCLUDING special trading days
"""

import pandas as pd
import numpy as np
import json
from datetime import time

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

# Identify normal trading days (start at 9:15 AM)
first_candle_each_day = df_5min.groupby('date').first()
# Normal trading should start at 09:15 or 09:20 (allowing 5min buffer)
normal_start_time_1 = time(9, 15)
normal_start_time_2 = time(9, 20)
normal_trading_days = first_candle_each_day[
    (first_candle_each_day['time'] == normal_start_time_1) | 
    (first_candle_each_day['time'] == normal_start_time_2)
].index

print(f"Total days in data: {len(first_candle_each_day)}")
print(f"Normal trading days (starting at 9:15-9:20): {len(normal_trading_days)}")
print(f"Special trading days (excluded): {len(first_candle_each_day) - len(normal_trading_days)}")

# Filter to only normal trading days
df_5min = df_5min[df_5min['date'].isin(normal_trading_days)].copy()

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

# Timing - need to calculate when 2nd order move happened
for idx, day in daily.iterrows():
    day_data = df_5min[df_5min['date'] == day['date']].copy()
    if len(day_data) == 0:
        continue
    
    # Time to touch high
    touched_high = day_data[day_data['high'] >= day['prev_high']]
    if len(touched_high) > 0:
        daily.at[idx, 'time_to_high'] = touched_high.iloc[0]['minutes_since_915']
    
    # Time to touch low
    touched_low = day_data[day_data['low'] <= day['prev_low']]
    if len(touched_low) > 0:
        daily.at[idx, 'time_to_low'] = touched_low.iloc[0]['minutes_since_915']
    
    # Time to 2nd order moves (after touching 1st order)
    # For HIGH first scenarios
    if idx in daily.index and 'time_to_high' in daily.columns and pd.notna(daily.loc[idx, 'time_to_high']):
        time_high = daily.loc[idx, 'time_to_high']
        after_high = day_data[day_data['minutes_since_915'] >= time_high]
        
        # Check when it went >=10% above
        threshold_above = day['prev_high'] + 0.1 * day['prev_range']
        went_above = after_high[after_high['high'] >= threshold_above]
        if len(went_above) > 0:
            daily.at[idx, 'time_to_10pct_above'] = went_above.iloc[0]['minutes_since_915']
    
    # For LOW first scenarios
    if idx in daily.index and 'time_to_low' in daily.columns and pd.notna(daily.loc[idx, 'time_to_low']):
        time_low = daily.loc[idx, 'time_to_low']
        after_low = day_data[day_data['minutes_since_915'] >= time_low]
        
        # Check when it went >=10% below
        threshold_below = day['prev_low'] - 0.1 * day['prev_range']
        went_below = after_low[after_low['low'] <= threshold_below]
        if len(went_below) > 0:
            daily.at[idx, 'time_to_10pct_below'] = went_below.iloc[0]['minutes_since_915']

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

# Calculate time to 2nd order for "went >=10% above"
high_went_10pct_above['time_to_2nd_order'] = high_went_10pct_above['time_to_10pct_above'] - high_went_10pct_above['time_to_high']

# Touched LOW first
touched_low_first = inside_days[
    (inside_days['time_to_low'].notna()) &
    ((inside_days['time_to_high'].isna()) | (inside_days['time_to_low'] < inside_days['time_to_high']))
].copy()

touched_low_first['pct_below_low'] = ((touched_low_first['prev_low'] - touched_low_first['day_low']) / touched_low_first['prev_range']) * 100

low_stayed_within_10pct = touched_low_first[touched_low_first['pct_below_low'] < 10].copy()
low_went_10pct_below = touched_low_first[touched_low_first['pct_below_low'] >= 10].copy()

# Calculate time to 2nd order for "went >=10% below"  
low_went_10pct_below['time_to_2nd_order'] = low_went_10pct_below['time_to_10pct_below'] - low_went_10pct_below['time_to_low']

# Build statistics
def get_stats(series):
    valid = series.dropna()
    if len(valid) == 0:
        return {"min": None, "max": None, "avg": None, "median": None}
    return {
        "min": round(float(valid.min()), 2),
        "max": round(float(valid.max()), 2),
        "avg": round(float(valid.mean()), 2),
        "median": round(float(valid.median()), 2)
    }

def get_timing_stats(df_subset):
    """Get timing stats with dates"""
    valid = df_subset.dropna(subset=['time_to_2nd_order'])
    if len(valid) == 0:
        return None
    
    min_idx = valid['time_to_2nd_order'].idxmin()
    max_idx = valid['time_to_2nd_order'].idxmax()
    median_val = valid['time_to_2nd_order'].median()
    # Find closest to median
    median_idx = (valid['time_to_2nd_order'] - median_val).abs().idxmin()
    
    return {
        "min": round(float(valid.loc[min_idx, 'time_to_2nd_order']), 2),
        "min_date": str(valid.loc[min_idx, 'date']),
        "max": round(float(valid.loc[max_idx, 'time_to_2nd_order']), 2),
        "max_date": str(valid.loc[max_idx, 'date']),
        "avg": round(float(valid['time_to_2nd_order'].mean()), 2),
        "median": round(float(valid['time_to_2nd_order'].median()), 2),
        "median_date": str(valid.loc[median_idx, 'date'])
    }

output = {
    "row1_stayed_within_10pct_above": {
        "vix_stats": get_stats(high_stayed_within_10pct['vix']),
        "timing_stats": None  # No 2nd order move for this scenario
    },
    "row2_went_10pct_above": {
        "vix_stats": get_stats(high_went_10pct_above['vix']),
        "timing_stats": get_timing_stats(high_went_10pct_above)
    },
    "row3_stayed_within_10pct_below": {
        "vix_stats": get_stats(low_stayed_within_10pct['vix']),
        "timing_stats": None  # No 2nd order move for this scenario
    },
    "row4_went_10pct_below": {
        "vix_stats": get_stats(low_went_10pct_below['vix']),
        "timing_stats": get_timing_stats(low_went_10pct_below)
    },
    "row5_stayed_inside": {
        "vix_stats": get_stats(inside_days[
            (inside_days['day_high'] < inside_days['prev_high']) &
            (inside_days['day_low'] > inside_days['prev_low'])
        ]['vix']),
        "timing_stats": None  # No 2nd order move for this scenario
    },
    "meta": {
        "total_days": len(first_candle_each_day),
        "normal_trading_days": len(normal_trading_days),
        "special_days_excluded": len(first_candle_each_day) - len(normal_trading_days)
    }
}

# Save to JSON
with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\vix_timing_stats.json', 'w') as f:
    json.dump(output, f, indent=2)

print("✅ VIX and timing statistics calculated (excluding special trading days)!")
print(f"\nSpecial days excluded: {output['meta']['special_days_excluded']}")
print(json.dumps(output, indent=2))
