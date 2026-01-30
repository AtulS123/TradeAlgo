"""
Magnitude Analysis - Normalized Metrics
========================================

Calculate magnitude as:
1. % of price level (accounts for NIFTY growing from 8000 to 22000)
2. % of previous day's range (e.g., if prev range = 100 pts, moved 50 pts beyond = 50% of range)
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path


def calculate_normalized_magnitudes():
    """Calculate magnitude as % of price and % of prev range"""
    
    print("\n" + "="*80)
    print("NORMALIZED MAGNITUDE ANALYSIS")
    print("="*80)
    
    # Load data
    data_path = r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv'
    df = pd.read_csv(data_path)
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
    
    # INSIDE opening scenarios
    inside_days = daily_agg[daily_agg['opening_position'] == 'INSIDE'].copy()
    
    print(f"\nAnalyzing {len(inside_days)} INSIDE opening days...")
    
    # Moved Above Only
    moved_above_only = inside_days[(inside_days['day_high'] > inside_days['prev_high']) & 
                                    (inside_days['day_low'] >= inside_days['prev_low'])].copy()
    
    if len(moved_above_only) > 0:
        moved_above_only['magnitude_pts'] = moved_above_only['day_high'] - moved_above_only['prev_high']
        moved_above_only['magnitude_pct_price'] = (moved_above_only['magnitude_pts'] / moved_above_only['prev_high']) * 100
        moved_above_only['magnitude_pct_range'] = (moved_above_only['magnitude_pts'] / moved_above_only['prev_range']) * 100
        
        avg_pts = moved_above_only['magnitude_pts'].mean()
        avg_pct_price = moved_above_only['magnitude_pct_price'].mean()
        avg_pct_range = moved_above_only['magnitude_pct_range'].mean()
        
        print(f"\n📈 MOVED ABOVE ONLY ({len(moved_above_only)} days):")
        print(f"   Avg magnitude: {avg_pts:.1f} points")
        print(f"   Avg % of price: {avg_pct_price:.2f}%")
        print(f"   Avg % of prev range: {avg_pct_range:.1f}%")
        
        results['moved_above_only'] = {
            'count': len(moved_above_only),
            'probability': (len(moved_above_only) / len(inside_days)) * 100,
            'magnitude_pts': avg_pts,
            'magnitude_pct_price': avg_pct_price,
            'magnitude_pct_range': avg_pct_range
        }
    
    # Moved Below Only
    moved_below_only = inside_days[(inside_days['day_low'] < inside_days['prev_low']) & 
                                    (inside_days['day_high'] <= inside_days['prev_high'])].copy()
    
    if len(moved_below_only) > 0:
        moved_below_only['magnitude_pts'] = moved_below_only['prev_low'] - moved_below_only['day_low']
        moved_below_only['magnitude_pct_price'] = (moved_below_only['magnitude_pts'] / moved_below_only['prev_low']) * 100
        moved_below_only['magnitude_pct_range'] = (moved_below_only['magnitude_pts'] / moved_below_only['prev_range']) * 100
        
        avg_pts = moved_below_only['magnitude_pts'].mean()
        avg_pct_price = moved_below_only['magnitude_pct_price'].mean()
        avg_pct_range = moved_below_only['magnitude_pct_range'].mean()
        
        print(f"\n📉 MOVED BELOW ONLY ({len(moved_below_only)} days):")
        print(f"   Avg magnitude: {avg_pts:.1f} points")
        print(f"   Avg % of price: {avg_pct_price:.2f}%")
        print(f"   Avg % of prev range: {avg_pct_range:.1f}%")
        
        results['moved_below_only'] = {
            'count': len(moved_below_only),
            'probability': (len(moved_below_only) / len(inside_days)) * 100,
            'magnitude_pts': avg_pts,
            'magnitude_pct_price': avg_pct_price,
            'magnitude_pct_range': avg_pct_range
        }
    
    # Moved Both
    moved_both = inside_days[(inside_days['day_high'] > inside_days['prev_high']) & 
                             (inside_days['day_low'] < inside_days['prev_low'])].copy()
    
    if len(moved_both) > 0:
        moved_both['magnitude_above_pts'] = moved_both['day_high'] - moved_both['prev_high']
        moved_both['magnitude_below_pts'] = moved_both['prev_low'] - moved_both['day_low']
        moved_both['magnitude_total_pts'] = moved_both['magnitude_above_pts'] + moved_both['magnitude_below_pts']
        moved_both['magnitude_pct_price'] = (moved_both['magnitude_total_pts'] / moved_both['day_open']) * 100
        moved_both['magnitude_pct_range'] = (moved_both['magnitude_total_pts'] / moved_both['prev_range']) * 100
        
        avg_pts = moved_both['magnitude_total_pts'].mean()
        avg_pct_price = moved_both['magnitude_pct_price'].mean()
        avg_pct_range = moved_both['magnitude_pct_range'].mean()
        
        print(f"\n↕️  MOVED BOTH DIRECTIONS ({len(moved_both)} days):")
        print(f"   Avg total magnitude: {avg_pts:.1f} points")
        print(f"   Avg % of price: {avg_pct_price:.2f}%")
        print(f"   Avg % of prev range: {avg_pct_range:.1f}%")
        
        results['moved_both'] = {
            'count': len(moved_both),
            'probability': (len(moved_both) / len(inside_days)) * 100,
            'magnitude_pts': avg_pts,
            'magnitude_pct_price': avg_pct_price,
            'magnitude_pct_range': avg_pct_range
        }
    
    # Stayed Inside
    stayed_inside = inside_days[(inside_days['day_high'] <= inside_days['prev_high']) & 
                                 (inside_days['day_low'] >= inside_days['prev_low'])].copy()
    
    results['stayed_inside'] = {
        'count': len(stayed_inside),
        'probability': (len(stayed_inside) / len(inside_days)) * 100,
        'magnitude_pts': 0,
        'magnitude_pct_price': 0,
        'magnitude_pct_range': 0
    }
    
    print(f"\n📊 STAYED INSIDE ({len(stayed_inside)} days): No magnitude")
    
    # Save results
    output_path = Path('research_lab/results/probability_grid')
    json_path = output_path / 'normalized_magnitudes.json'
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Saved: {json_path}")
    
    # Verification
    total_prob = sum([results[k]['probability'] for k in results.keys()])
    print(f"\n✓ Total probability: {total_prob:.1f}% (should be 100%)")
    
    return results


if __name__ == '__main__':
    calculate_normalized_magnitudes()
    print("\n✅ Normalized magnitude analysis complete!")
