"""
Extract Example Dates for Each Scenario
========================================
Get 3-5 example dates for each scenario to show in the table
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime

def get_example_dates():
    """Get example dates for each scenario"""
    
    print("\n" + "="*80)
    print("EXTRACTING EXAMPLE DATES FOR EACH SCENARIO")
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
    
    # Opening classification
    def classify_open(row):
        if row['day_open'] > row['prev_high']:
            return 'ABOVE'
        elif row['day_open'] < row['prev_low']:
            return 'BELOW'
        else:
            return 'INSIDE'
    
    daily['opening_position'] = daily.apply(classify_open, axis=1)
    
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
    
    examples = {}
    
    # Inside - touched high first
    inside_days = daily[daily['opening_position'] == 'INSIDE'].copy()
    touched_high_first = inside_days[
        (inside_days['time_to_high'].notna()) &
        ((inside_days['time_to_low'].isna()) | (inside_days['time_to_high'] < inside_days['time_to_low']))
    ].copy()
    
    # Get 5 random recent examples
    recent_high = touched_high_first.sort_values('date', ascending=False).head(10)
    examples['inside_touched_high_first'] = [str(d) for d in recent_high['date'].head(5).tolist()]
    
    # 2nd order - returned to low
    high_then_low = touched_high_first[touched_high_first['day_low'] <= touched_high_first['prev_low']].copy()
    recent = high_then_low.sort_values('date', ascending=False).head(5)
    examples['high_first_then_returned_low'] = [str(d) for d in recent['date'].tolist()]
    
    # Inside - touched low first
    touched_low_first = inside_days[
        (inside_days['time_to_low'].notna()) &
        ((inside_days['time_to_high'].isna()) | (inside_days['time_to_low'] < inside_days['time_to_high']))
    ].copy()
    
    recent_low = touched_low_first.sort_values('date', ascending=False).head(10)
    examples['inside_touched_low_first'] = [str(d) for d in recent_low['date'].head(5).tolist()]
    
    # 2nd order - returned to high
    low_then_high = touched_low_first[touched_low_first['day_high'] >= touched_low_first['prev_high']].copy()
    recent = low_then_high.sort_values('date', ascending=False).head(5)
    examples['low_first_then_returned_high'] = [str(d) for d in recent['date'].tolist()]
    
    # Stayed inside
    stayed_inside = inside_days[
        (inside_days['day_high'] <= inside_days['prev_high']) &
        (inside_days['day_low'] >= inside_days['prev_low'])
    ].copy()
    recent = stayed_inside.sort_values('date', ascending=False).head(5)
    examples['stayed_inside'] = [str(d) for d in recent['date'].tolist()]
    
    # Save
    output_path = Path(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid')
    json_path = output_path / 'example_dates.json'
    with open(json_path, 'w') as f:
        json.dump(examples, f, indent=2)
    
    print(f"\n✅ Saved examples to: {json_path}")
    
    # Print summary
    print(f"\nExample Dates Summary:")
    for key, dates in examples.items():
        print(f"\n{key}:")
        for date in dates:
            print(f"  - {date}")
    
    return examples

if __name__ == '__main__':
    get_example_dates()
    print("\n✅ Example dates extracted!")
