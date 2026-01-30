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

# Load VIX data
vix = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\INDIA VIX_minute.csv')
vix['datetime'] = pd.to_datetime(vix['date'])
vix['date'] = vix['datetime'].dt.date
vix_daily = vix.groupby('date').agg({'close': 'last'}).reset_index()
vix_daily = vix_daily.rename(columns={'close': 'vix'})

daily = daily.merge(vix_daily, on='date', how='left')

# Analyze timing
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

# Filter INSIDE opening days
inside_days = daily[daily['opening_position'] == 'INSIDE'].copy()

# Touched HIGH first
touched_high_first = inside_days[
    (inside_days['time_to_high'].notna()) &
    ((inside_days['time_to_low'].isna()) | (inside_days['time_to_high'] < inside_days['time_to_low']))
].copy()

# 2nd order - went >= 10% above
touched_high_first['threshold_above'] = touched_high_first['prev_high'] + 0.1 * touched_high_first['prev_range']
high_went_above = touched_high_first[touched_high_first['day_high'] >= touched_high_first['threshold_above']].copy()

print("HIGH_WENT_ABOVE_VIX:", round(high_went_above['vix'].median(), 2) if len(high_went_above) > 0 else "N/A")
if len(high_went_above) > 0:
    recent = high_went_above.sort_values('date', ascending=False).head(5)
    for _, row in recent.iterrows():
        print(f"HIGH_WENT_ABOVE_DATE: {row['date']}")

# Touched LOW first
touched_low_first = inside_days[
    (inside_days['time_to_low'].notna()) &
    ((inside_days['time_to_high'].isna()) | (inside_days['time_to_low'] < inside_days['time_to_high']))
].copy()

# 2nd order - went >= 10% below
touched_low_first['threshold_below'] = touched_low_first['prev_low'] - 0.1 * touched_low_first['prev_range']
low_went_below = touched_low_first[touched_low_first['day_low'] <= touched_low_first['threshold_below']].copy()

print("LOW_WENT_BELOW_VIX:", round(low_went_below['vix'].median(), 2) if len(low_went_below) > 0 else "N/A")
if len(low_went_below) > 0:
    recent = low_went_below.sort_values('date', ascending=False).head(5)
    for _, row in recent.iterrows():
        print(f"LOW_WENT_BELOW_DATE: {row['date']}")
