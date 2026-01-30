import pandas as pd
import numpy as np
import json
from pathlib import Path

def get_vix_stats(df):
    if len(df) == 0:
        return None
    
    if 'vix' in df.columns:
        vix_values = df['vix'].dropna()
        if len(vix_values) == 0:
            return None
        return {
            'min': round(vix_values.min(), 2),
            'max': round(vix_values.max(), 2),
            'median': round(vix_values.median(), 2),
            'avg': round(vix_values.mean(), 2)
        }
    return None

def get_recent_dates(df, n=5):
    if len(df) == 0:
        return []
    sorted_df = df.sort_values('date', ascending=False)
    dates = sorted_df['date'].head(n).astype(str).tolist()
    return dates

def get_timing_stats(df, time_column):
    if len(df) == 0:
        return None
    times = df[time_column].dropna()
    if len(times) == 0:
        return None
    return {
        'min': int(times.min()),
        'max': int(times.max()),
        'median': int(times.median()),
        'avg': int(times.mean())
    }

def analyze_open_below_days():
    # Load data (Same method as analyze_open_above.py)
    df = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv')
    df['datetime'] = pd.to_datetime(df['date'])
    df.set_index('datetime', inplace=True)
    
    # Resample to 5-min
    df_5min = df.resample('5min', closed='left', label='left').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'
    }).dropna()
    
    df_5min['date'] = df_5min.index.date
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
    
    # Filter for BELOW opening (Close < Prev Low)
    # Using strict less than. If close == prev_low, it's not strictly below.
    below_days = daily[daily['first_5min_close'] < daily['prev_low']].copy()
    
    print(f"Total BELOW days: {len(below_days)}")
    
    # Initialize columns
    below_days['touched_prev_low_by_10am'] = False
    below_days['time_touched_low'] = np.nan
    below_days['went_above_low'] = False
    below_days['time_went_above'] = np.nan
    below_days['touched_mid'] = False
    below_days['time_touched_mid'] = np.nan
    below_days['touched_high'] = False
    below_days['time_touched_high'] = np.nan
    
    # EOD Checks
    below_days['touched_prev_low_by_eod'] = False # Generic touch check for not_touched group
    below_days['time_touched_low_eod'] = np.nan
    below_days['retested_low_by_eod'] = False # Specific retest check for went_above group
    below_days['time_retested_low'] = np.nan
    
    cutoff_10am = 45  # minutes since 9:15
    
    for idx, day in below_days.iterrows():
        day_date = day['date']
        # Get candles for this day
        # Optimization: Filter df_5min by date strictly
        day_candles = df_5min[df_5min['date'] == day_date].copy()
        
        # Exclude first candle
        after_first = day_candles[day_candles['minutes_since_915'] >= 5]
        
        # Check touched prev_low by 10 AM (Resistance Test)
        # Condition: High >= Prev Low
        by_10am = after_first[after_first['minutes_since_915'] <= cutoff_10am]
        touched = by_10am[by_10am['high'] >= day['prev_low']]
        
        if len(touched) > 0:
            below_days.at[idx, 'touched_prev_low_by_10am'] = True
            below_days.at[idx, 'time_touched_low'] = touched.iloc[0]['minutes_since_915']
            
            touch_time = touched.iloc[0]['minutes_since_915']
            after_touch = after_first[after_first['minutes_since_915'] >= touch_time]
            
            # Check went ABOVE prev low (False Breakout / Reclaim)
            # Condition: High > Prev Low (Strictly above, meaning it broke the resistance)
            went_above = after_touch[after_touch['high'] > day['prev_low']]
            
            if len(went_above) > 0:
                below_days.at[idx, 'went_above_low'] = True
                below_days.at[idx, 'time_went_above'] = went_above.iloc[0]['minutes_since_915']
                
                # Check Mid/High Targets
                touched_mid_candles = after_touch[after_touch['high'] >= day['prev_mid']]
                if len(touched_mid_candles) > 0:
                    below_days.at[idx, 'touched_mid'] = True
                    below_days.at[idx, 'time_touched_mid'] = touched_mid_candles.iloc[0]['minutes_since_915']
                
                touched_high_candles = after_touch[after_touch['high'] >= day['prev_high']]
                if len(touched_high_candles) > 0:
                    below_days.at[idx, 'touched_high'] = True
                    below_days.at[idx, 'time_touched_high'] = touched_high_candles.iloc[0]['minutes_since_915']
                    
                # Check Retest of Low (Support Test) by EOD
                # Condition: Low <= Prev Low AFTER going above
                went_above_time = went_above.iloc[0]['minutes_since_915']
                after_break_in = day_candles[day_candles['minutes_since_915'] > went_above_time]
                
                retest = after_break_in[after_break_in['low'] <= day['prev_low']]
                
                if len(retest) > 0:
                    below_days.at[idx, 'retested_low_by_eod'] = True
                    below_days.at[idx, 'time_retested_low'] = retest.iloc[0]['minutes_since_915']
        
        # Check Touched Prev Low by EOD (for the not_touched group mainly)
        # Condition: High >= Prev Low
        touched_eod = after_first[after_first['high'] >= day['prev_low']]
        if len(touched_eod) > 0:
            below_days.at[idx, 'touched_prev_low_by_eod'] = True
            below_days.at[idx, 'time_touched_low_eod'] = touched_eod.iloc[0]['minutes_since_915']
            
    return below_days

def calculate_and_save_stats(below_days):
    total_below = len(below_days)
    touched_by_10am = below_days[below_days['touched_prev_low_by_10am'] == True]
    not_touched_by_10am = below_days[below_days['touched_prev_low_by_10am'] == False]
    
    # Breakdown of Touched
    # 1. Stayed Below (Tested Resistance but failed to break)
    stayed_below = touched_by_10am[touched_by_10am['went_above_low'] == False]
    
    # 2. Went Above (Broke Resistance / Reclaim)
    went_above = touched_by_10am[touched_by_10am['went_above_low'] == True]
    
    # Breakdown of Went Above
    touched_high = went_above[went_above['touched_high'] == True]
    touched_mid_not_high = went_above[(went_above['touched_mid'] == True) & (went_above['touched_high'] == False)]
    # "Went above but not to mid"
    above_not_mid = went_above[went_above['touched_mid'] == False]
    
    # EOD Breakdown for "Above Not Mid": Did it retest the low?
    retested_low = above_not_mid[above_not_mid['retested_low_by_eod'] == True]
    not_retested_low = above_not_mid[above_not_mid['retested_low_by_eod'] == False]
    
    # EOD Breakdown for "Not Touched by 10 AM": Did it touch by EOD?
    touched_eod = not_touched_by_10am[not_touched_by_10am['touched_prev_low_by_eod'] == True]
    not_touched_eod = not_touched_by_10am[not_touched_by_10am['touched_prev_low_by_eod'] == False]
    
    stats = {
        'total_below_days': total_below,
        'touched_by_10am': {
            'count': len(touched_by_10am),
            'prob': round(len(touched_by_10am) / total_below * 100, 1),
            'breakdown': {
                'stayed_below': {
                    'count': len(stayed_below),
                    'prob': round(len(stayed_below) / len(touched_by_10am) * 100, 1),
                    'dates': get_recent_dates(stayed_below),
                    'vix': get_vix_stats(stayed_below),
                    'timing': get_timing_stats(stayed_below, 'time_touched_low')
                },
                'above_not_mid': {
                    'count': len(above_not_mid),
                    'prob': round(len(above_not_mid) / len(touched_by_10am) * 100, 1),
                    'dates': get_recent_dates(above_not_mid),
                    'vix': get_vix_stats(above_not_mid),
                    'timing': get_timing_stats(above_not_mid, 'time_went_above'),
                    'eod_breakdown': {
                        'retested': {
                            'count': len(retested_low),
                            'prob': round(len(retested_low) / len(above_not_mid) * 100, 1),
                            'dates': get_recent_dates(retested_low),
                            'vix': get_vix_stats(retested_low),
                            'timing': get_timing_stats(retested_low, 'time_retested_low')
                        },
                        'not_retested': {
                            'count': len(not_retested_low),
                            'prob': round(len(not_retested_low) / len(above_not_mid) * 100, 1),
                            'dates': get_recent_dates(not_retested_low),
                            'vix': get_vix_stats(not_retested_low),
                            'timing': None
                        }
                    }
                },
                'touched_mid': {
                    'count': len(touched_mid_not_high),
                    'prob': round(len(touched_mid_not_high) / len(touched_by_10am) * 100, 1),
                    'dates': get_recent_dates(touched_mid_not_high),
                    'vix': get_vix_stats(touched_mid_not_high),
                    'timing': get_timing_stats(touched_mid_not_high, 'time_touched_mid')
                },
                'touched_high': {
                    'count': len(touched_high),
                    'prob': round(len(touched_high) / len(touched_by_10am) * 100, 1),
                    'dates': get_recent_dates(touched_high),
                    'vix': get_vix_stats(touched_high),
                    'timing': get_timing_stats(touched_high, 'time_touched_high')
                }
            }
        },
        'not_touched_by_10am': {
            'count': len(not_touched_by_10am),
            'prob': round(len(not_touched_by_10am) / total_below * 100, 1),
            'breakdown': {
                'touched_eod': {
                    'count': len(touched_eod),
                    'prob': round(len(touched_eod) / len(not_touched_by_10am) * 100, 1),
                    'dates': get_recent_dates(touched_eod),
                    'vix': get_vix_stats(touched_eod),
                    'timing': get_timing_stats(touched_eod, 'time_touched_low_eod')
                },
                'not_touched_eod': {
                    'count': len(not_touched_eod),
                    'prob': round(len(not_touched_eod) / len(not_touched_by_10am) * 100, 1),
                    'dates': get_recent_dates(not_touched_eod),
                    'vix': get_vix_stats(not_touched_eod),
                    'timing': None
                }
            }
        }
    }
    
    with open('open_below_stats.json', 'w') as f:
        json.dump(stats, f, indent=4)
        print("Stats saved to open_below_stats.json")

if __name__ == "__main__":
    below_days = analyze_open_below_days()
    calculate_and_save_stats(below_days)
