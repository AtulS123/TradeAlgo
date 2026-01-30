"""
Complete Probability Analysis with QC Validation + Median Date Tracking
=======================================================================
Calculate ALL counts, probabilities, timings with median date examples
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

def complete_analysis_with_median_dates():
    """Complete analysis with QC + actual dates for median values"""
    
    print("\n" + "="*80)
    print("COMPLETE PROBABILITY ANALYSIS WITH MEDIAN DATE TRACKING")
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
    
    total_days = len(daily)
    print(f"\nTotal trading days: {total_days}")
    
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
    # SCENARIO 1: INSIDE OPENING
    # ============================================================================
    print("\n" + "="*80)
    print("SCENARIO 1: INSIDE OPENING")
    print("="*80)
    
    inside_days = daily[daily['opening_position'] == 'INSIDE'].copy()
    inside_count = len(inside_days)
    print(f"Total INSIDE days: {inside_count} ({inside_count/total_days*100:.1f}%)")
    
    # 1st Order: Which level touched first?
    touched_high_first = inside_days[
        (inside_days['time_to_high'].notna()) &
        ((inside_days['time_to_low'].isna()) | (inside_days['time_to_high'] < inside_days['time_to_low']))
    ].copy()
    
    touched_low_first = inside_days[
        (inside_days['time_to_low'].notna()) &
        ((inside_days['time_to_high'].isna()) | (inside_days['time_to_low'] < inside_days['time_to_high']))
    ].copy()
    
    stayed_inside = inside_days[
        (inside_days['day_high'] <= inside_days['prev_high']) &
        (inside_days['day_low'] >= inside_days['prev_low'])
    ].copy()
    
    print(f"\n1st Order Classification:")
    print(f"  Touched HIGH first: {len(touched_high_first)} ({len(touched_high_first)/inside_count*100:.1f}%)")
    print(f"  Touched LOW first: {len(touched_low_first)} ({len(touched_low_first)/inside_count*100:.1f}%)")
    print(f"  Stayed INSIDE: {len(stayed_inside)} ({len(stayed_inside)/inside_count*100:.1f}%)")
    
    # Touched HIGH first analysis
    if len(touched_high_first) > 0:
        times = touched_high_first['time_to_high'].dropna()
        median_val = times.median()
        
        # Find the date closest to median
        median_idx = (times - median_val).abs().idxmin()
        median_date = touched_high_first.loc[median_idx, 'date']
        median_time = touched_high_first.loc[median_idx, 'time_to_high']
        
        print(f"\n  Touched HIGH first timing:")
        print(f"    Min: {int(times.min())} min")
        print(f"    Max: {int(times.max())} min")
        print(f"    Median: {int(median_val)} min on {median_date}")
        print(f"    Avg: {int(times.mean())} min")
        
        # 2nd order
        high_then_low = touched_high_first[touched_high_first['day_low'] <= touched_high_first['prev_low']].copy()
        high_stayed_above = touched_high_first[touched_high_first['day_low'] > touched_high_first['prev_low']].copy()
        
        print(f"\n  2nd Order after touching HIGH:")
        print(f"    Returned to LOW: {len(high_then_low)} ({len(high_then_low)/len(touched_high_first)*100:.1f}%)")
        print(f"    Stayed above LOW: {len(high_stayed_above)} ({len(high_stayed_above)/len(touched_high_first)*100:.1f}%)")
        print(f"    QC: {len(high_then_low)} + {len(high_stayed_above)} = {len(high_then_low) + len(high_stayed_above)} (should be {len(touched_high_first)})")
        
        results['inside_touched_high_first'] = {
            'count': len(touched_high_first),
            'probability_of_inside': round(len(touched_high_first) / inside_count * 100, 1),
            'time_to_1st_order': {
                'min': int(times.min()),
                'max': int(times.max()),
                'median': int(median_val),
                'median_date': str(median_date),
                'median_time_actual': int(median_time),
                'avg': int(times.mean())
            },
            'second_order': {
                'returned_to_low': {
                    'count': len(high_then_low),
                    'probability': round(len(high_then_low) / len(touched_high_first) * 100, 1)
                },
                'stayed_above_low': {
                    'count': len(high_stayed_above),
                    'probability': round(len(high_stayed_above) / len(touched_high_first) * 100, 1)
                }
            }
        }
    
    # Touched LOW first analysis
    if len(touched_low_first) > 0:
        times = touched_low_first['time_to_low'].dropna()
        median_val = times.median()
        
        # Find the date closest to median
        median_idx = (times - median_val).abs().idxmin()
        median_date = touched_low_first.loc[median_idx, 'date']
        median_time = touched_low_first.loc[median_idx, 'time_to_low']
        
        print(f"\n  Touched LOW first timing:")
        print(f"    Min: {int(times.min())} min")
        print(f"    Max: {int(times.max())} min")
        print(f"    Median: {int(median_val)} min on {median_date}")
        print(f"    Avg: {int(times.mean())} min")
        
        # 2nd order
        low_then_high = touched_low_first[touched_low_first['day_high'] >= touched_low_first['prev_high']].copy()
        low_stayed_below = touched_low_first[touched_low_first['day_high'] < touched_low_first['prev_high']].copy()
        
        print(f"\n  2nd Order after touching LOW:")
        print(f"    Returned to HIGH: {len(low_then_high)} ({len(low_then_high)/len(touched_low_first)*100:.1f}%)")
        print(f"    Stayed below HIGH: {len(low_stayed_below)} ({len(low_stayed_below)/len(touched_low_first)*100:.1f}%)")
        print(f"    QC: {len(low_then_high)} + {len(low_stayed_below)} = {len(low_then_high) + len(low_stayed_below)} (should be {len(touched_low_first)})")
        
        results['inside_touched_low_first'] = {
            'count': len(touched_low_first),
            'probability_of_inside': round(len(touched_low_first) / inside_count * 100, 1),
            'time_to_1st_order': {
                'min': int(times.min()),
                'max': int(times.max()),
                'median': int(median_val),
                'median_date': str(median_date),
                'median_time_actual': int(median_time),
                'avg': int(times.mean())
            },
            'second_order': {
                'returned_to_high': {
                    'count': len(low_then_high),
                    'probability': round(len(low_then_high) / len(touched_low_first) * 100, 1)
                },
                'stayed_below_high': {
                    'count': len(low_stayed_below),
                    'probability': round(len(low_stayed_below) / len(touched_low_first) * 100, 1)
                }
            }
        }
    
    # Stayed inside
    results['inside_stayed'] = {
        'count': len(stayed_inside),
        'probability_of_inside': round(len(stayed_inside) / inside_count * 100, 1)
    }
    
    # Save results
    output_path = Path(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid')
    json_path = output_path / 'complete_analysis_with_median_dates.json'
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Saved: {json_path}")
    return results

if __name__ == '__main__':
    complete_analysis_with_median_dates()
    print("\n✅ Complete analysis with median dates done!")
