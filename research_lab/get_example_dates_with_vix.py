"""
Get example dates with VIX values for all scenarios in first row
"""

import pandas as pd
import numpy as np
from pathlib import Path

def get_example_dates():
    """Get real example dates with VIX values"""
    
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
    
    # Get first 5-min candle for each day
    first_candles = df_5min[df_5min['minutes_since_915'] == 0].copy()
    first_candles = first_candles.rename(columns={
        'open': 'first_5min_open',
        'close': 'first_5min_close',
        'high': 'first_5min_high',
        'low': 'first_5min_low'
    })
    
    # Daily aggregation
    daily = df_5min.groupby('date').agg({
        'high': 'max',
        'low': 'min',
        'open': 'first',
        'close': 'last'
    }).reset_index()
    daily.columns = ['date', 'day_high', 'day_low', 'day_open', 'day_close']
    
    # Merge with first 5-min candle data
    daily = daily.merge(first_candles[['date', 'first_5min_open', 'first_5min_close', 'first_5min_high', 'first_5min_low']], on='date', how='left')
    
    daily['prev_high'] = daily['day_high'].shift(1)
    daily['prev_low'] = daily['day_low'].shift(1)
    daily = daily.dropna()
    
    daily['prev_range'] = daily['prev_high'] - daily['prev_low']
    
    # Load VIX data
    vix = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\INDIA VIX_minute.csv')
    vix['datetime'] = pd.to_datetime(vix['date'])
    vix['date'] = vix['datetime'].dt.date
    # Get daily VIX (using close of last minute bar each day)
    vix_daily = vix.groupby('date').agg({'close': 'last'}).reset_index()
    vix_daily = vix_daily.rename(columns={'close': 'vix'})
    
    # Merge VIX
    daily = daily.merge(vix_daily, on='date', how='left')
    
    # Analyze timing for each day
    for idx, day in daily.iterrows():
        day_data = df_5min[df_5min['date'] == day['date']].copy()
        if len(day_data) == 0:
            continue
        
        # EXCLUDE first 5-min candle (9:15-9:20) for actionable post-opening data
        after_first_candle = day_data[day_data['minutes_since_915'] >= 5]
        
        # Time to touch prev high (starting from second candle)
        touched_high = after_first_candle[after_first_candle['high'] >= day['prev_high']]
        if len(touched_high) > 0:
            daily.at[idx, 'time_to_high'] = touched_high.iloc[0]['minutes_since_915']
        
        # Time to touch prev low (starting from second candle)
        touched_low = after_first_candle[after_first_candle['low'] <= day['prev_low']]
        if len(touched_low) > 0:
            daily.at[idx, 'time_to_low'] = touched_low.iloc[0]['minutes_since_915']
    
    # Opening classification based on first 5-min candle
    def classify_open_5min(row):
        """Classify based on first 5-min candle CLOSE being inside"""
        # Only check if CLOSE is inside, not the open
        if row['first_5min_close'] > row['prev_high']:
            return 'ABOVE'
        elif row['first_5min_close'] < row['prev_low']:
            return 'BELOW'
        else:
            return 'INSIDE'
    
    daily['opening_position'] = daily.apply(classify_open_5min, axis=1)
    
    # Filter INSIDE opening days
    inside_days = daily[daily['opening_position'] == 'INSIDE'].copy()
    
    # Touched HIGH first
    touched_high_first = inside_days[
        (inside_days['time_to_high'].notna()) &
        ((inside_days['time_to_low'].isna()) | (inside_days['time_to_high'] < inside_days['time_to_low']))
    ].copy()
    
    # Touched LOW first
    touched_low_first = inside_days[
        (inside_days['time_to_low'].notna()) &
        ((inside_days['time_to_high'].isna()) | (inside_days['time_to_low'] < inside_days['time_to_high']))
    ].copy()
    
    # 2nd order after touching HIGH first
    high_then_low = touched_high_first[touched_high_first['day_low'] <= touched_high_first['prev_low']].copy()
    high_stayed_above = touched_high_first[touched_high_first['day_low'] > touched_high_first['prev_low']].copy()
    
    # 2nd order after touching LOW first
    low_then_high = touched_low_first[touched_low_first['day_high'] >= touched_low_first['prev_high']].copy()
    low_stayed_below = touched_low_first[touched_low_first['day_high'] < touched_low_first['prev_high']].copy()
    
    # Get recent examples for touched HIGH first scenarios
    print("\n" + "="*80)
    print("FIRST ROW: Touched PREV DAY HIGH First (after opening inside)")
    print("="*80)
    
    # Calculate stats for timing to hit high
    times_high = touched_high_first['time_to_high'].dropna()
    print(f"\nTotal days: {len(touched_high_first)}")
    print(f"Probability of inside: {len(touched_high_first)/len(inside_days)*100:.1f}%")
    
    # Find actual example dates for min, max, median
    min_idx = times_high.idxmin()
    max_idx = times_high.idxmax()
    median_val = times_high.median()
    median_idx = (times_high - median_val).abs().idxmin()
    
    min_date = touched_high_first.loc[min_idx, 'date']
    max_date = touched_high_first.loc[max_idx, 'date']
    median_date = touched_high_first.loc[median_idx, 'date']
    
    print(f"\nTime to hit HIGH (1st order):")
    print(f"  min: {int(times_high.min())} on {min_date}")
    print(f"  max: {int(times_high.max())} on {max_date}")
    print(f"  median: {int(median_val)} on {median_date}")
    print(f"  avg: {int(times_high.mean())} min")
    
    # Get VIX for this scenario
    median_vix = touched_high_first['vix'].median()
    print(f"\nMedian VIX: {median_vix:.2f}")
    
    # Get 5 most recent examples
    recent = touched_high_first.sort_values('date', ascending=False).head(5)
    print(f"\n5 Most Recent Examples:")
    for _, row in recent.iterrows():
        vix_str = f"{row['vix']:.2f}" if pd.notna(row['vix']) else 'N/A'
        print(f"  {row['date']} - VIX: {vix_str}")
    
    # 2nd order stats
    print(f"\n2nd Order Move (after touching high first):")
    print(f"  Touched prev low without going ≥10% over prev high: {len(high_stayed_above)} ({len(high_stayed_above)/len(touched_high_first)*100:.1f}%)")
    print(f"  Went ≥10% over prev high: {len(high_then_low)} ({len(high_then_low)/len(touched_high_first)*100:.1f}%)")
    
    # Get timing stats for 2nd order (time from high to low)
    if len(high_stayed_above) > 0:
        # Calculate time from touching high to touching low
        high_stayed_times = []
        for idx, row in high_stayed_above.iterrows():
            if pd.notna(row['time_to_low']) and pd.notna(row['time_to_high']):
                time_diff = row['time_to_low'] - row['time_to_high']
                high_stayed_times.append(time_diff)
        
        if high_stayed_times:
            print(f"\nTime from HIGH to LOW (2nd order - returned to low):")
            print(f"  min: {int(min(high_stayed_times))} min")
            print(f"  max: {int(max(high_stayed_times))} min")
            print(f"  median: {int(np.median(high_stayed_times))} min")
            print(f"  avg: {int(np.mean(high_stayed_times))} min")
        
        # Get recent examples for 2nd order
        recent_2nd = high_stayed_above.sort_values('date', ascending=False).head(5)
        print(f"\n5 Most Recent Examples (2nd order - returned to low):")
        for _, row in recent_2nd.iterrows():
            vix_str = f"{row['vix']:.2f}" if pd.notna(row['vix']) else 'N/A'
            print(f"  {row['date']} - VIX: {vix_str}")
    
    # Print same for touched LOW first
    print("\n" + "="*80)
    print("FIRST ROW (2nd scenario): Touched PREV DAY LOW First (after opening inside)")
    print("="*80)
    
    times_low = touched_low_first['time_to_low'].dropna()
    print(f"\nTotal days: {len(touched_low_first)}")
    print(f"Probability of inside: {len(touched_low_first)/len(inside_days)*100:.1f}%")
    
    # Find actual example dates for min, max, median
    min_idx_low = times_low.idxmin()
    max_idx_low = times_low.idxmax()
    median_val_low = times_low.median()
    median_idx_low = (times_low - median_val_low).abs().idxmin()
    
    min_date_low = touched_low_first.loc[min_idx_low, 'date']
    max_date_low = touched_low_first.loc[max_idx_low, 'date']
    median_date_low = touched_low_first.loc[median_idx_low, 'date']
    
    print(f"\nTime to hit LOW (1st order):")
    print(f"  min: {int(times_low.min())} on {min_date_low}")
    print(f"  max: {int(times_low.max())} on {max_date_low}")
    print(f"  median: {int(median_val_low)} on {median_date_low}")
    print(f"  avg: {int(times_low.mean())} min")
    
    median_vix_low = touched_low_first['vix'].median()
    print(f"\nMedian VIX: {median_vix_low:.2f}")
    
    recent_low = touched_low_first.sort_values('date', ascending=False).head(5)
    print(f"\n5 Most Recent Examples:")
    for _, row in recent_low.iterrows():
        vix_str = f"{row['vix']:.2f}" if pd.notna(row['vix']) else 'N/A'
        print(f"  {row['date']} - VIX: {vix_str}")
    
    print(f"\n2nd Order Move (after touching low first):")
    print(f"  Touched prev high without going ≥10% below prev low: {len(low_stayed_below)} ({len(low_stayed_below)/len(touched_low_first)*100:.1f}%)")
    print(f"  Went ≥10% below prev low: {len(low_then_high)} ({len(low_then_high)/len(touched_low_first)*100:.1f}%)")
    
    if len(low_stayed_below) > 0:
        low_stayed_times = []
        for idx, row in low_stayed_below.iterrows():
            if pd.notna(row['time_to_high']) and pd.notna(row['time_to_low']):
                time_diff = row['time_to_high'] - row['time_to_low']
                low_stayed_times.append(time_diff)
        
        if low_stayed_times:
            print(f"\nTime from LOW to HIGH (2nd order - returned to high):")
            print(f"  min: {int(min(low_stayed_times))} min")
            print(f"  max: {int(max(low_stayed_times))} min")
            print(f"  median: {int(np.median(low_stayed_times))} min")
            print(f"  avg: {int(np.mean(low_stayed_times))} min")
        
        recent_2nd_low = low_stayed_below.sort_values('date', ascending=False).head(5)
        print(f"\n5 Most Recent Examples (2nd order - returned to high):")
        for _, row in recent_2nd_low.iterrows():
            vix_str = f"{row['vix']:.2f}" if pd.notna(row['vix']) else 'N/A'
            print(f"  {row['date']} - VIX: {vix_str}")
    
    return {
        'touched_high_first': {
            'count': len(touched_high_first),
            'prob_of_inside': f"{len(touched_high_first)/len(inside_days)*100:.1f}%",
            'median_vix': f"{median_vix:.2f}",
            'recent_examples': recent['date'].tolist(),
            'time_to_1st_order': {
                'min': int(times_high.min()),
                'min_date': str(min_date),
                'max': int(times_high.max()),
                'max_date': str(max_date),
                'median': int(median_val),
                'median_date': str(median_date),
                'avg': int(times_high.mean())
            },
            '2nd_order_returned_low': {
                'count': len(high_stayed_above),
                'prob': f"{len(high_stayed_above)/len(touched_high_first)*100:.1f}%",
                'recent_examples': high_stayed_above.sort_values('date', ascending=False).head(5)['date'].tolist() if len(high_stayed_above) > 0 else []
            },
            '2nd_order_went_over_high': {
                'count': len(high_then_low),
                'prob': f"{len(high_then_low)/len(touched_high_first)*100:.1f}%"
            }
        },
        'touched_low_first': {
            'count': len(touched_low_first),
            'prob_of_inside': f"{len(touched_low_first)/len(inside_days)*100:.1f}%",
            'median_vix': f"{median_vix_low:.2f}",
            'recent_examples': recent_low['date'].tolist(),
            'time_to_1st_order': {
                'min': int(times_low.min()),
                'min_date': str(min_date_low),
                'max': int(times_low.max()),
                'max_date': str(max_date_low),
                'median': int(median_val_low),
                'median_date': str(median_date_low),
                'avg': int(times_low.mean())
            },
            '2nd_order_returned_high': {
                'count': len(low_stayed_below),
                'prob': f"{len(low_stayed_below)/len(touched_low_first)*100:.1f}%",
                'recent_examples': low_stayed_below.sort_values('date', ascending=False).head(5)['date'].tolist() if len(low_stayed_below) > 0 else []
            },
            '2nd_order_went_below_low': {
                'count': len(low_then_high),
                'prob': f"{len(low_then_high)/len(touched_low_first)*100:.1f}%"
            }
        }
    }

if __name__ == '__main__':
    results = get_example_dates()
    print("\n✅ Analysis complete!")
