"""
QC Analysis with Date Tracking for Min/Max/Median + Market Hours Validation
===========================================================================
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

def qc_analysis_with_all_dates():
    """Complete QC with dates for min/max/median + market hours validation"""
    
    print("\n" + "="*80)
    print("QC ANALYSIS WITH DATE TRACKING & MARKET HOURS VALIDATION")
    print("="*80)
    
    # Load data
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
    daily['prev_mid'] = (daily['prev_high'] + daily['prev_low']) / 2
    
    # Opening classification
    def classify_open(row):
        if row['day_open'] > row['prev_high']:
            return 'ABOVE'
        elif row['day_open'] < row['prev_low']:
            return 'BELOW'
        else:
            return 'INSIDE'
    
    daily['opening_position'] = daily.apply(classify_open, axis=1)
    
    # Analyze timing for each day
    for idx, day in daily.iterrows():
        day_data = df_5min[df_5min['date'] == day['date']].copy()
        if len(day_data) == 0:
            continue
        
        # Time to touch prev high
        touched_high = day_data[day_data['high'] >= day['prev_high']]
        if len(touched_high) > 0:
            daily.at[idx, 'time_to_high'] = touched_high.iloc[0]['minutes_since_915']
        
        # Time to touch prev low
        touched_low = day_data[day_data['low'] <= day['prev_low']]
        if len(touched_low) > 0:
            daily.at[idx, 'time_to_low'] = touched_low.iloc[0]['minutes_since_915']
    
    results = {}
    
    # ============================================================================
    # INSIDE OPENING - TOUCHED HIGH FIRST
    # ============================================================================
    print("\n" + "="*80)
    print("INSIDE → TOUCHED HIGH FIRST")
    print("="*80)
    
    inside_days = daily[daily['opening_position'] == 'INSIDE'].copy()
    touched_high_first = inside_days[
        (inside_days['time_to_high'].notna()) &
        ((inside_days['time_to_low'].isna()) | (inside_days['time_to_high'] < inside_days['time_to_low']))
    ].copy()
    
    if len(touched_high_first) > 0:
        times = touched_high_first['time_to_high'].dropna()
        
        # Get dates for min, max, median
        min_idx = times.idxmin()
        max_idx = times.idxmax()
        median_val = times.median()
        median_idx = (times - median_val).abs().idxmin()
        
        min_date = touched_high_first.loc[min_idx, 'date']
        min_time = touched_high_first.loc[min_idx, 'time_to_high']
        
        max_date = touched_high_first.loc[max_idx, 'date']
        max_time = touched_high_first.loc[max_idx, 'time_to_high']
        
        median_date = touched_high_first.loc[median_idx, 'date']
        median_time = touched_high_first.loc[median_idx, 'time_to_high']
        
        print(f"Count: {len(touched_high_first)} days")
        print(f"\nMin: {int(min_time)} min on {min_date}")
        print(f"Max: {int(max_time)} min on {max_date}")
        print(f"Median: {int(median_time)} min on {median_date}")
        print(f"Avg: {int(times.mean())} min")
        
        # QC - Flag values beyond market hours
        beyond_market = times[times > 375]
        if len(beyond_market) > 0:
            print(f"\n⚠️ QC WARNING: {len(beyond_market)} days have times > 375 min (market close)")
            print(f"   Max value: {int(beyond_market.max())} min")
            print(f"   These might be data errors or next-day touches")
            
            # Show example
            example_idx = beyond_market.idxmax()
            example_date = touched_high_first.loc[example_idx, 'date']
            example_time = touched_high_first.loc[example_idx, 'time_to_high']
            print(f"   Example: {int(example_time)} min on {example_date}")
        
        # 2nd order
        high_then_low = touched_high_first[touched_high_first['day_low'] <= touched_high_first['prev_low']].copy()
        high_stayed_above = touched_high_first[touched_high_first['day_low'] > touched_high_first['prev_low']].copy()
        
        results['inside_touched_high_first'] = {
            'count': len(touched_high_first),
            'time_to_1st_order': {
                'min': int(min_time),
                'min_date': str(min_date),
                'max': int(max_time),
                'max_date': str(max_date),
                'median': int(median_time),
                'median_date': str(median_date),
                'avg': int(times.mean()),
                'qc_beyond_market_hours': int(len(beyond_market)),
                'qc_max_valid': int(max_time) if max_time <= 375 else 375
            },
            'second_order': {
                'returned_to_low': {'count': len(high_then_low)},
                'stayed_above_low': {'count': len(high_stayed_above)}
            }
        }
    
    # ============================================================================
    # INSIDE OPENING - TOUCHED LOW FIRST
    # ============================================================================
    print("\n" + "="*80)
    print("INSIDE → TOUCHED LOW FIRST")
    print("="*80)
    
    touched_low_first = inside_days[
        (inside_days['time_to_low'].notna()) &
        ((inside_days['time_to_high'].isna()) | (inside_days['time_to_low'] < inside_days['time_to_high']))
    ].copy()
    
    if len(touched_low_first) > 0:
        times = touched_low_first['time_to_low'].dropna()
        
        # Get dates for min, max, median
        min_idx = times.idxmin()
        max_idx = times.idxmax()
        median_val = times.median()
        median_idx = (times - median_val).abs().idxmin()
        
        min_date = touched_low_first.loc[min_idx, 'date']
        min_time = touched_low_first.loc[min_idx, 'time_to_low']
        
        max_date = touched_low_first.loc[max_idx, 'date']
        max_time = touched_low_first.loc[max_idx, 'time_to_low']
        
        median_date = touched_low_first.loc[median_idx, 'date']
        median_time = touched_low_first.loc[median_idx, 'time_to_low']
        
        print(f"Count: {len(touched_low_first)} days")
        print(f"\nMin: {int(min_time)} min on {min_date}")
        print(f"Max: {int(max_time)} min on {max_date}")
        print(f"Median: {int(median_time)} min on {median_date}")
        print(f"Avg: {int(times.mean())} min")
        
        # QC - Flag values beyond market hours
        beyond_market = times[times > 375]
        if len(beyond_market) > 0:
            print(f"\n⚠️ QC WARNING: {len(beyond_market)} days have times > 375 min (market close)")
            print(f"   Max value: {int(beyond_market.max())} min")
            
            example_idx = beyond_market.idxmax()
            example_date = touched_low_first.loc[example_idx, 'date']
            example_time = touched_low_first.loc[example_idx, 'time_to_low']
            print(f"   Example: {int(example_time)} min on {example_date}")
        
        # 2nd order
        low_then_high = touched_low_first[touched_low_first['day_high'] >= touched_low_first['prev_high']].copy()
        low_stayed_below = touched_low_first[touched_low_first['day_high'] < touched_low_first['prev_high']].copy()
        
        results['inside_touched_low_first'] = {
            'count': len(touched_low_first),
            'time_to_1st_order': {
                'min': int(min_time),
                'min_date': str(min_date),
                'max': int(max_time),
                'max_date': str(max_date),
                'median': int(median_time),
                'median_date': str(median_date),
                'avg': int(times.mean()),
                'qc_beyond_market_hours': int(len(beyond_market)),
                'qc_max_valid': int(max_time) if max_time <= 375 else 375
            },
            'second_order': {
                'returned_to_high': {'count': len(low_then_high)},
                'stayed_below_high': {'count': len(low_stayed_below)}
            }
        }
    
    # Save results
    output_path = Path(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid')
    json_path = output_path / 'qc_analysis_with_dates.json'
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Saved: {json_path}")
    return results

if __name__ == '__main__':
    qc_analysis_with_all_dates()
    print("\n✅ QC analysis with dates complete!")
