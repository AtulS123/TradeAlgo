"""
Complete Analysis with VIX
===========================
Add median VIX for each scenario
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path


def analyze_with_vix():
    """Analyze scenarios with VIX data"""
    
    print("\n" + "="*80)
    print("ANALYSIS WITH VIX DATA")
    print("="*80)
    
    # Load NIFTY data
    nifty_path = r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv'
    df = pd.read_csv(nifty_path)
    df['datetime'] = pd.to_datetime(df['date'])
    df = df.sort_values('datetime').reset_index(drop=True)
    
    # Load VIX data
    try:
        vix_path = r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\India VIX_minute.csv'
        vix = pd.read_csv(vix_path)
        vix['datetime'] = pd.to_datetime(vix['date'])
        vix = vix.sort_values('datetime').reset_index(drop=True)
        vix['date'] = vix['datetime'].dt.date
        
        # Get daily VIX (open value)
        vix_daily = vix.groupby('date').agg({'open': 'first'}).reset_index()
        vix_daily.columns = ['date', 'vix']
        
        print(f"✓ Loaded VIX data: {len(vix_daily)} days")
    except Exception as e:
        print(f"⚠️  Could not load VIX: {e}")
        vix_daily = None
    
    # Resample NIFTY to 5-min
    df.set_index('datetime', inplace=True)
    df_5min = df.resample('5min').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    df_5min['date'] = df_5min.index.date
    df_5min.reset_index(inplace=True)
    
    # Get daily ranges
    daily_agg = df_5min.groupby('date').agg({
        'high': 'max',
        'low': 'min',
        'open': 'first',
        'close': 'last'
    }).reset_index()
    daily_agg.columns = ['date', 'day_high', 'day_low', 'day_open', 'day_close']
    daily_agg['prev_high'] = daily_agg['day_high'].shift(1)
    daily_agg['prev_low'] = daily_agg['day_low'].shift(1)
    daily_agg = daily_agg.dropna()
    
    # Merge with VIX
    if vix_daily is not None:
        daily_agg = daily_agg.merge(vix_daily, on='date', how='left')
    
    # Calculate ranges
    daily_agg['prev_range'] = daily_agg['prev_high'] - daily_agg['prev_low']
    
    # Classify opening
    def classify_open(row):
        if row['day_open'] > row['prev_high']:
            return 'ABOVE'
        elif row['day_open'] < row['prev_low']:
            return 'BELOW'
        else:
            return 'INSIDE'
    
    daily_agg['opening_position'] = daily_agg.apply(classify_open, axis=1)
    
    # Results
    results = {}
    
    # INSIDE scenarios
    inside_days = daily_agg[daily_agg['opening_position'] == 'INSIDE'].copy()
    
    # Moved Above Only
    moved_above = inside_days[(inside_days['day_high'] > inside_days['prev_high']) & 
                              (inside_days['day_low'] >= inside_days['prev_low'])].copy()
    
    if len(moved_above) > 0:
        moved_above['magnitude_pts'] = moved_above['day_high'] - moved_above['prev_high']
        moved_above['magnitude_pct_price'] = (moved_above['magnitude_pts'] / moved_above['prev_high']) * 100
        moved_above['magnitude_pct_range'] = (moved_above['magnitude_pts'] / moved_above['prev_range']) * 100
        
        results['inside_moved_above'] = {
            'count': len(moved_above),
            'probability': (len(moved_above) / len(inside_days)) * 100,
            'magnitude_pct_price': moved_above['magnitude_pct_price'].mean(),
            'magnitude_pct_range': moved_above['magnitude_pct_range'].mean(),
            'median_vix': moved_above['vix'].median() if 'vix' in moved_above.columns else None,
            'latest_example': moved_above.tail(1)[['date', 'prev_high', 'prev_low', 'day_open', 'day_high', 'day_low']].to_dict('records')[0] if len(moved_above) > 0 else None
        }
        print(f"\n📈 Inside → Above: VIX median = {moved_above['vix'].median():.1f}" if 'vix' in moved_above.columns else "")
    
    # Moved Below Only
    moved_below = inside_days[(inside_days['day_low'] < inside_days['prev_low']) & 
                              (inside_days['day_high'] <= inside_days['prev_high'])].copy()
    
    if len(moved_below) > 0:
        moved_below['magnitude_pts'] = moved_below['prev_low'] - moved_below['day_low']
        moved_below['magnitude_pct_price'] = (moved_below['magnitude_pts'] / moved_below['prev_low']) * 100
        moved_below['magnitude_pct_range'] = (moved_below['magnitude_pts'] / moved_below['prev_range']) * 100
        
        results['inside_moved_below'] = {
            'count': len(moved_below),
            'probability': (len(moved_below) / len(inside_days)) * 100,
            'magnitude_pct_price': moved_below['magnitude_pct_price'].mean(),
            'magnitude_pct_range': moved_below['magnitude_pct_range'].mean(),
            'median_vix': moved_below['vix'].median() if 'vix' in moved_below.columns else None,
            'latest_example': moved_below.tail(1)[['date', 'prev_high', 'prev_low', 'day_open', 'day_high', 'day_low']].to_dict('records')[0] if len(moved_below) > 0 else None
        }
        print(f"📉 Inside → Below: VIX median = {moved_below['vix'].median():.1f}" if 'vix' in moved_below.columns else "")
    
    # Stayed Inside
    stayed = inside_days[(inside_days['day_high'] <= inside_days['prev_high']) & 
                         (inside_days['day_low'] >= inside_days['prev_low'])].copy()
    
    if len(stayed) > 0:
        results['inside_stayed'] = {
            'count': len(stayed),
            'probability': (len(stayed) / len(inside_days)) * 100,
            'median_vix': stayed['vix'].median() if 'vix' in stayed.columns else None,
            'latest_example': stayed.tail(1)[['date', 'prev_high', 'prev_low', 'day_open', 'day_high', 'day_low']].to_dict('records')[0] if len(stayed) > 0 else None
        }
        print(f"📊 Inside → Stayed: VIX median = {stayed['vix'].median():.1f}" if 'vix' in stayed.columns else "")
    
    # Moved Both
    moved_both = inside_days[(inside_days['day_high'] > inside_days['prev_high']) & 
                             (inside_days['day_low'] < inside_days['prev_low'])].copy()
    
    if len(moved_both) > 0:
        results['inside_moved_both'] = {
            'count': len(moved_both),
            'probability': (len(moved_both) / len(inside_days)) * 100,
            'median_vix': moved_both['vix'].median() if 'vix' in moved_both.columns else None,
            'latest_example': moved_both.tail(1)[['date', 'prev_high', 'prev_low', 'day_open', 'day_high', 'day_low']].to_dict('records')[0] if len(moved_both) > 0 else None
        }
        print(f"↕️  Inside → Both: VIX median = {moved_both['vix'].median():.1f}" if 'vix' in moved_both.columns else "")
    
    # ABOVE scenarios
    above_days = daily_agg[daily_agg['opening_position'] == 'ABOVE'].copy()
    if len(above_days) > 0 and 'vix' in above_days.columns:
        results['above_opening'] = {
            'count': len(above_days),
            'median_vix': above_days['vix'].median()
        }
        print(f"\n📈 Gap Up Opening: VIX median = {above_days['vix'].median():.1f}")
    
    # BELOW scenarios
    below_days = daily_agg[daily_agg['opening_position'] == 'BELOW'].copy()
    if len(below_days) > 0 and 'vix' in below_days.columns:
        results['below_opening'] = {
            'count': len(below_days),
            'median_vix': below_days['vix'].median()
        }
        print(f"📉 Gap Down Opening: VIX median = {below_days['vix'].median():.1f}")
    
    # Save
    output_path = Path('research_lab/results/probability_grid')
    json_path = output_path / 'complete_with_vix.json'
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Saved: {json_path}")
    
    return results


if __name__ == '__main__':
    analyze_with_vix()
    print("\n✅ Analysis with VIX complete!")
