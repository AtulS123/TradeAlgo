"""
Get VIX and example dates for each 2nd order scenario separately
"""

import pandas as pd
import numpy as np

def get_2nd_order_details():
    """Get VIX and dates for each 2nd order scenario"""
    
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
    
    # Analyze timing for each day
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
    
    # 2nd order after touching HIGH first
    # Define 10% of prev range
    touched_high_first['threshold_above'] = touched_high_first['prev_high'] + 0.1 * touched_high_first['prev_range']
    
    high_returned_to_low = touched_high_first[touched_high_first['day_low'] <= touched_high_first['prev_low']].copy()
    high_went_above = touched_high_first[touched_high_first['day_high'] >= touched_high_first['threshold_above']].copy()
    
    print("\n" + "="*80)
    print("TOUCHED HIGH FIRST - 2nd Order Scenarios")
    print("="*80)
    
    print(f"\n1. Returned to prev LOW (touches prev low without going >=10% above):")
    print(f"   Count: {len(high_returned_to_low)}")
    print(f"   Median VIX: {high_returned_to_low['vix'].median():.2f}")
    recent = high_returned_to_low.sort_values('date', ascending=False).head(5)
    print(f"   Recent examples:")
    for _, row in recent.iterrows():
        vix_str = f"{row['vix']:.2f}" if pd.notna(row['vix']) else 'N/A'
        print(f"     {row['date']} (VIX: {vix_str})")
    
    print(f"\n2. Went >=10% ABOVE prev high:")
    print(f"   Count: {len(high_went_above)}")
    if len(high_went_above) > 0:
        print(f"   Median VIX: {high_went_above['vix'].median():.2f}")
        recent = high_went_above.sort_values('date', ascending=False).head(5)
        print(f"   Recent examples:")
        for _, row in recent.iterrows():
            vix_str = f"{row['vix']:.2f}" if pd.notna(row['vix']) else 'N/A'
            print(f"     {row['date']} (VIX: {vix_str})")
    
    # Touched LOW first
    touched_low_first = inside_days[
        (inside_days['time_to_low'].notna()) &
        ((inside_days['time_to_high'].isna()) | (inside_days['time_to_low'] < inside_days['time_to_high']))
    ].copy()
    
    # 2nd order after touching LOW first
    touched_low_first['threshold_below'] = touched_low_first['prev_low'] - 0.1 * touched_low_first['prev_range']
    
    low_returned_to_high = touched_low_first[touched_low_first['day_high'] >= touched_low_first['prev_high']].copy()
    low_went_below = touched_low_first[touched_low_first['day_low'] <= touched_low_first['threshold_below']].copy()
    
    print("\n" + "="*80)
    print("TOUCHED LOW FIRST - 2nd Order Scenarios")
    print("="*80)
    
    print(f"\n1. Returned to prev HIGH (touches prev high without going >=10% below):")
    print(f"   Count: {len(low_returned_to_high)}")
    print(f"   Median VIX: {low_returned_to_high['vix'].median():.2f}")
    recent = low_returned_to_high.sort_values('date', ascending=False).head(5)
    print(f"   Recent examples:")
    for _, row in recent.iterrows():
        vix_str = f"{row['vix']:.2f}" if pd.notna(row['vix']) else 'N/A'
        print(f"     {row['date']} (VIX: {vix_str})")
    
    print(f"\n2. Went >=10% BELOW prev low:")
    print(f"   Count: {len(low_went_below)}")
    if len(low_went_below) > 0:
        print(f"   Median VIX: {low_went_below['vix'].median():.2f}")
        recent = low_went_below.sort_values('date', ascending=False).head(5)
        print(f"   Recent examples:")
        for _, row in recent.iterrows():
            vix_str = f"{row['vix']:.2f}" if pd.notna(row['vix']) else 'N/A'
            print(f"     {row['date']} (VIX: {vix_str})")

if __name__ == '__main__':
    get_2nd_order_details()
    print("\n✅ Analysis complete!")
