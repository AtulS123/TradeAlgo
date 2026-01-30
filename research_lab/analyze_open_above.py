"""
Market Open Above Analysis
Analyzes days where first 5-min candle closes ABOVE previous day high
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path

def analyze_open_above():
    """Analyze days that open above prev day high with detailed breakdowns"""
    
    # Load data
    df = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv')
    df['datetime'] = pd.to_datetime(df['date'])
    df.set_index('datetime', inplace=True)
    
    # Resample to 5-min
    df_5min = df.resample('5min', closed='left', label='left').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'
    }).dropna()
    
    df_5min['date'] = df_5min.index.date
    df_5min['time'] = df_5min.index.time
    df_5min['minutes_since_915'] = df_5min.index.hour * 60 + df_5min.index.minute - 555
    df_5min = df_5min[df_5min['minutes_since_915'] >= 0]
    df_5min.reset_index(inplace=True)
    
    # Daily aggregation
    daily = df_5min.groupby('date').agg({
        'high': 'max', 'low': 'min', 'open': 'first', 'close': 'last'
    }).reset_index()
    daily.columns = ['date', 'day_high', 'day_low', 'day_open', 'day_close']
    
    # Get first 5-min candle close
    first_candles = df_5min[df_5min['minutes_since_915'] == 0][['date', 'close']].rename(
        columns={'close': 'first_5min_close'})
    daily = daily.merge(first_candles, on='date', how='left')
    
    # Previous day levels
    daily['prev_high'] = daily['day_high'].shift(1)
    daily['prev_low'] = daily['day_low'].shift(1)
    daily['prev_mid'] = (daily['prev_high'] + daily['prev_low']) / 2
    daily['prev_range'] = daily['prev_high'] - daily['prev_low']
    daily = daily.dropna()
    
    # Load VIX
    vix = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\INDIA VIX_minute.csv')
    vix['datetime'] = pd.to_datetime(vix['date'])
    vix['date'] = vix['datetime'].dt.date
    vix_daily = vix.groupby('date').agg({'close': 'last'}).reset_index().rename(columns={'close': 'vix'})
    daily = daily.merge(vix_daily, on='date', how='left')
    
    # Filter for ABOVE opening
    above_days = daily[daily['first_5min_close'] > daily['prev_high']].copy()
    
    print(f"Total ABOVE days: {len(above_days)}")
    
    # Initialize columns
    above_days['touched_prev_high_by_10am'] = False
    above_days['time_touched_high'] = np.nan
    above_days['went_below_high'] = False
    above_days['time_went_below'] = np.nan
    above_days['touched_mid'] = False
    above_days['time_touched_mid'] = np.nan
    above_days['touched_low'] = False
    above_days['time_touched_low'] = np.nan
    above_days['touched_prev_high_by_eod'] = False
    above_days['time_touched_high_eod'] = np.nan
    
    # Analyze each day
    cutoff_10am = 45  # minutes since 9:15
    
    for idx, day in above_days.iterrows():
        day_candles = df_5min[df_5min['date'] == day['date']].copy()
        
        # Exclude first candle (start from minute 5)
        after_first = day_candles[day_candles['minutes_since_915'] >= 5]
        
        # Check touched prev_high by 10 AM
        by_10am = after_first[after_first['minutes_since_915'] <= cutoff_10am]
        touched = by_10am[by_10am['low'] <= day['prev_high']]
        
        if len(touched) > 0:
            above_days.at[idx, 'touched_prev_high_by_10am'] = True
            above_days.at[idx, 'time_touched_high'] = touched.iloc[0]['minutes_since_915']
            
            # Analyze what happened after touching
            touch_time = touched.iloc[0]['minutes_since_915']
            after_touch = after_first[after_first['minutes_since_915'] >= touch_time]
            
            # Check if went below prev_high
            went_below = after_touch[after_touch['low'] < day['prev_high']]
            if len(went_below) > 0:
                above_days.at[idx, 'went_below_high'] = True
                above_days.at[idx, 'time_went_below'] = went_below.iloc[0]['minutes_since_915']
                
                # Check how far below
                touched_mid_candles = after_touch[after_touch['low'] <= day['prev_mid']]
                if len(touched_mid_candles) > 0:
                    above_days.at[idx, 'touched_mid'] = True
                    above_days.at[idx, 'time_touched_mid'] = touched_mid_candles.iloc[0]['minutes_since_915']
                    
                touched_low_candles = after_touch[after_touch['low'] <= day['prev_low']]
                if len(touched_low_candles) > 0:
                    above_days.at[idx, 'touched_low'] = True
                    above_days.at[idx, 'time_touched_low'] = touched_low_candles.iloc[0]['minutes_since_915']
        
        # Check if touched prev_high by EOD (entire day, excluding first candle)
        touched_eod = after_first[after_first['low'] <= day['prev_high']]
        if len(touched_eod) > 0:
            above_days.at[idx, 'touched_prev_high_by_eod'] = True
            above_days.at[idx, 'time_touched_high_eod'] = touched_eod.iloc[0]['minutes_since_915']
    
    return above_days, daily

def calculate_statistics(above_days):
    """Calculate probabilities and statistics for all categories"""
    
    total = len(above_days)
    
    # Level 2: Touched prev high by 10 AM
    touched_by_10am = above_days[above_days['touched_prev_high_by_10am'] == True]
    not_touched_by_10am = above_days[above_days['touched_prev_high_by_10am'] == False]
    
    stats = {
        'total_above_days': total,
        'touched_by_10am': {
            'count': len(touched_by_10am),
            'prob': round(len(touched_by_10am) / total * 100, 1) if total > 0 else 0,
            'dates': get_recent_dates(touched_by_10am)
        },
        'not_touched_by_10am': {
            'count': len(not_touched_by_10am),
            'prob': round(len(not_touched_by_10am) / total * 100, 1) if total > 0 else 0,
            'dates': get_recent_dates(not_touched_by_10am)
        }
    }
    
    # Level 3: For touched by 10 AM - analyze post-touch behavior
    if len(touched_by_10am) > 0:
        # Did not go below high
        stayed_above = touched_by_10am[touched_by_10am['went_below_high'] == False]
        
        # Went below but not to mid
        below_not_mid = touched_by_10am[
            (touched_by_10am['went_below_high'] == True) &
            (touched_by_10am['touched_mid'] == False)
        ]
        
        # Touched mid but not low
        touched_mid_only = touched_by_10am[
            (touched_by_10am['touched_mid'] == True) &
            (touched_by_10am['touched_low'] == False)
        ]
        
        # Touched low
        touched_low = touched_by_10am[touched_by_10am['touched_low'] == True]
        
        stats['touched_by_10am']['breakdown'] = {
            'stayed_above': {
                'count': len(stayed_above),
                'prob': round(len(stayed_above) / len(touched_by_10am) * 100, 1),
                'dates': get_recent_dates(stayed_above),
                'vix': get_vix_stats(stayed_above),
                'timing': get_timing_stats(stayed_above, 'time_touched_high')
            },
            'below_not_mid': {
                'count': len(below_not_mid),
                'prob': round(len(below_not_mid) / len(touched_by_10am) * 100, 1),
                'dates': get_recent_dates(below_not_mid),
                'vix': get_vix_stats(below_not_mid),
                'timing': get_timing_stats(below_not_mid, 'time_went_below')
            },
            'touched_mid': {
                'count': len(touched_mid_only),
                'prob': round(len(touched_mid_only) / len(touched_by_10am) * 100, 1),
                'dates': get_recent_dates(touched_mid_only),
                'vix': get_vix_stats(touched_mid_only),
                'timing': get_timing_stats(touched_mid_only, 'time_touched_mid')
            },
            'touched_low': {
                'count': len(touched_low),
                'prob': round(len(touched_low) / len(touched_by_10am) * 100, 1),
                'dates': get_recent_dates(touched_low),
                'vix': get_vix_stats(touched_low),
                'timing': get_timing_stats(touched_low, 'time_touched_low')
            }
        }
        
        # Level 4: For below_not_mid - check EOD touch
        if len(below_not_mid) > 0:
            touched_eod = below_not_mid[below_not_mid['touched_prev_high_by_eod'] == True]
            not_touched_eod = below_not_mid[below_not_mid['touched_prev_high_by_eod'] == False]
            
            stats['touched_by_10am']['breakdown']['below_not_mid']['eod_breakdown'] = {
                'touched_eod': {
                    'count': len(touched_eod),
                    'prob': round(len(touched_eod) / len(below_not_mid) * 100, 1),
                    'dates': get_recent_dates(touched_eod),
                    'vix': get_vix_stats(touched_eod),
                    'timing': get_timing_stats(touched_eod, 'time_touched_high_eod')
                },
                'not_touched_eod': {
                    'count': len(not_touched_eod),
                    'prob': round(len(not_touched_eod) / len(below_not_mid) * 100, 1),
                    'dates': get_recent_dates(not_touched_eod),
                    'vix': get_vix_stats(not_touched_eod),
                    'timing': None
                }
            }
    
    # Level 3: For NOT touched by 10 AM - check EOD touch  
    if len(not_touched_by_10am) > 0:
        touched_eod = not_touched_by_10am[not_touched_by_10am['touched_prev_high_by_eod'] == True]
        not_touched_eod = not_touched_by_10am[not_touched_by_10am['touched_prev_high_by_eod'] == False]
        
        stats['not_touched_by_10am']['breakdown'] = {
            'touched_eod': {
                'count': len(touched_eod),
                'prob': round(len(touched_eod) / len(not_touched_by_10am) * 100, 1),
                'dates': get_recent_dates(touched_eod),
                'vix': get_vix_stats(touched_eod),
                'timing': get_timing_stats(touched_eod, 'time_touched_high_eod')
            },
            'not_touched_eod': {
                'count': len(not_touched_eod),
                'prob': round(len(not_touched_eod) / len(not_touched_by_10am) * 100, 1),
                'dates': get_recent_dates(not_touched_eod),
                'vix': get_vix_stats(not_touched_eod),
                'timing': None
            }
        }
    
    return stats

def get_vix_stats(df):
    """Get VIX statistics"""
    valid = df['vix'].dropna()
    if len(valid) == 0:
        return None
    return {
        'min': round(valid.min(), 2),
        'max': round(valid.max(), 2),
        'median': round(valid.median(), 2),
        'avg': round(valid.mean(), 2)
    }

def get_timing_stats(df, time_column):
    """Get timing statistics"""
    valid = df[time_column].dropna()
    if len(valid) == 0:
        return None
    return {
        'min': int(valid.min()),
        'max': int(valid.max()),
        'median': int(valid.median()),
        'avg': int(valid.mean())
    }

def get_recent_dates(df, limit=5):
    """Get recent example dates"""
    if len(df) == 0:
        return []
    return [str(d) for d in df.sort_values('date', ascending=False).head(limit)['date'].tolist()]

if __name__ == '__main__':
    print("Analyzing Market Open Above scenarios...")
    above_days, daily = analyze_open_above()
    
    print("\nCalculating statistics...")
    stats = calculate_statistics(above_days)
    
    # Save results
    output_dir = Path(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / 'open_above_stats.json', 'w') as f:
        json.dump(stats, f, indent=4)
    
    print(f"\n✅ Analysis complete!")
    print(f"Total ABOVE days: {stats['total_above_days']}")
    print(f"Touched by 10 AM: {stats['touched_by_10am']['count']} ({stats['touched_by_10am']['prob']}%)")
    print(f"Not touched by 10 AM: {stats['not_touched_by_10am']['count']} ({stats['not_touched_by_10am']['prob']}%)")
