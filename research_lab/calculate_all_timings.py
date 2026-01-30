"""
Complete Timing Analysis for All Scenarios
==========================================
Calculate min, max, median, avg times for all transitions
"""

import pandas as pd
import numpy as np
from datetime import time
import json

def calculate_all_timings():
    """Calculate all timing metrics for the probability table"""
    
    print("\n" + "="*80)
    print("COMPLETE TIMING ANALYSIS")
    print("="*80)
    
    # Load minute data
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
    
    # Get daily agg
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
    
    # Opening classification
    def classify_open(row):
        if row['day_open'] > row['prev_high']:
            return 'ABOVE'
        elif row['day_open'] < row['prev_low']:
            return 'BELOW'
        else:
            return 'INSIDE'
    
    daily['opening_position'] = daily.apply(classify_open, axis=1)
    
    results = {}
    
    # INSIDE OPENING - Touched High First
    print("\n" + "-"*80)
    print("INSIDE → TOUCHED HIGH FIRST")
    print("-"*80)
    
    inside_days = daily[daily['opening_position'] == 'INSIDE'].copy()
    
    for idx, day in inside_days.iterrows():
        day_data = df_5min[df_5min['date'] == day['date']].copy()
        if len(day_data) == 0:
            continue
        
        # When did it first touch prev high?
        touched_high = day_data[day_data['high'] >= day['prev_high']]
        # When did it first touch prev low?
        touched_low = day_data[day_data['low'] <= day['prev_low']]
        
        if len(touched_high) > 0:
            time_to_high = touched_high.iloc[0]['minutes_since_915']
            day['time_to_high'] = time_to_high
        
        if len(touched_low) > 0:
            time_to_low = touched_low.iloc[0]['minutes_since_915']
            day['time_to_low'] = time_to_low
    
    # Touched high first (before touching low)
    touched_high_first = inside_days[
        (inside_days['time_to_high'].notna()) &
        ((inside_days['time_to_low'].isna()) | (inside_days['time_to_high'] < inside_days['time_to_low']))
    ]
    
    if len(touched_high_first) > 0:
        times = touched_high_first['time_to_high'].dropna()
        results['inside_touched_high_first'] = {
            'count': len(touched_high_first),
            'probability': len(touched_high_first) / len(inside_days) * 100,
            'time_to_1st_order': {
                'min': int(times.min()),
                'max': int(times.max()),
                'median': int(times.median()),
                'avg': int(times.mean())
            }
        }
        print(f"Touched high first: {len(touched_high_first)} days")
        print(f"Time to touch high - Min: {int(times.min())}m, Max: {int(times.max())}m, "
              f"Median: {int(times.median())}m, Avg: {int(times.mean())}m")
    
    # INSIDE OPENING - Touched Low First
    print("\n" + "-"*80)
    print("INSIDE → TOUCHED LOW FIRST")
    print("-"*80)
    
    touched_low_first = inside_days[
        (inside_days['time_to_low'].notna()) &
        ((inside_days['time_to_high'].isna()) | (inside_days['time_to_low'] < inside_days['time_to_high']))
    ]
    
    if len(touched_low_first) > 0:
        times = touched_low_first['time_to_low'].dropna()
        results['inside_touched_low_first'] = {
            'count': len(touched_low_first),
            'probability': len(touched_low_first) / len(inside_days) * 100,
            'time_to_1st_order': {
                'min': int(times.min()),
                'max': int(times.max()),
                'median': int(times.median()),
                'avg': int(times.mean())
            }
        }
        print(f"Touched low first: {len(touched_low_first)} days")
        print(f"Time to touch low - Min: {int(times.min())}m, Max: {int(times.max())}m, "
              f"Median: {int(times.median())}m, Avg: {int(times.mean())}m")
    
    # GAP UP
    print("\n" + "-"*80)
    print("GAP UP SCENARIOS")
    print("-"*80)
    
    gap_up = daily[daily['opening_position'] == 'ABOVE'].copy()
    print(f"Total gap up days: {len(gap_up)}")
    
    # Stayed inside
    stayed_inside = inside_days[
        (inside_days['day_high'] <= inside_days['prev_high']) &
        (inside_days['day_low'] >= inside_days['prev_low'])
    ]
    results['inside_stayed'] = {
        'count': len(stayed_inside),
        'probability': len(stayed_inside) / len(inside_days) * 100
    }
    print(f"Stayed inside: {len(stayed_inside)} days")
    
    # Save
    import json
    with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\complete_timings.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Saved complete timings")
    return results

if __name__ == '__main__':
    calculate_all_timings()
    print("\n✅ Complete timing analysis done!")
