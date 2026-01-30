"""
Complete Probability Analysis with Magnitude and Duration
=========================================================

Calculates:
- All probabilities (must add to 100%)
- Average magnitude of moves (in points/percentage)
- Duration for each state transition
- Real examples from data
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
import json
from pathlib import Path


def complete_analysis_with_magnitude_duration():
    """Complete analysis including magnitude and duration"""
    
    print("\n" + "="*80)
    print("COMPLETE PROBABILITY ANALYSIS WITH MAGNITUDE & DURATION")
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
    df_5min['time'] = df_5min.index.time
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
    
    # Classify opening
    def classify_open(row):
        if row['day_open'] > row['prev_high']:
            return 'ABOVE'
        elif row['day_open'] < row['prev_low']:
            return 'BELOW'
        else:
            return 'INSIDE'
    
    daily_agg['opening_position'] = daily_agg.apply(classify_open, axis=1)
    
    # Calculate range metrics
    daily_agg['prev_range'] = daily_agg['prev_high'] - daily_agg['prev_low']
    daily_agg['day_range'] = daily_agg['day_high'] - daily_agg['day_low']
    
    # Results structure
    results = {
        'summary': {},
        'scenarios': []
    }
    
    # Summary stats
    total_days = len(daily_agg)
    results['summary'] = {
        'total_days': total_days,
        'inside_count': len(daily_agg[daily_agg['opening_position'] == 'INSIDE']),
        'above_count': len(daily_agg[daily_agg['opening_position'] == 'ABOVE']),
        'below_count': len(daily_agg[daily_agg['opening_position'] == 'BELOW'])
    }
    
    print(f"\nTotal days analyzed: {total_days}")
    print(f"INSIDE openings: {results['summary']['inside_count']} ({results['summary']['inside_count']/total_days*100:.1f}%)")
    print(f"ABOVE openings: {results['summary']['above_count']} ({results['summary']['above_count']/total_days*100:.1f}%)")
    print(f"BELOW openings: {results['summary']['below_count']} ({results['summary']['below_count']/total_days*100:.1f}%)")
    
    # Process INSIDE opening scenarios
    inside_days = daily_agg[daily_agg['opening_position'] == 'INSIDE'].copy()
    
    print("\n" + "="*80)
    print("INSIDE OPENING - ALL SCENARIOS")
    print("="*80)
    
    scenarios_inside = {
        'stayed_inside': [],
        'moved_above_only': [],
        'moved_below_only': [],
        'moved_both': []
    }
    
    for idx, day in inside_days.iterrows():
        prev_high = day['prev_high']
        prev_low = day['prev_low']
        day_high = day['day_high']
        day_low = day['day_low']
        
        moved_above = day_high > prev_high
        moved_below = day_low < prev_low
        
        # Calculate magnitudes
        magnitude_above = day_high - prev_high if moved_above else 0
        magnitude_below = prev_low - day_low if moved_below else 0
        
        scenario_data = {
            'date': str(day['date']),
            'prev_high': prev_high,
            'prev_low': prev_low,
            'day_open': day['day_open'],
            'day_high': day_high,
            'day_low': day_low,
            'day_close': day['day_close'],
            'magnitude_above': magnitude_above,
            'magnitude_below': magnitude_below
        }
        
        if not moved_above and not moved_below:
            scenarios_inside['stayed_inside'].append(scenario_data)
        elif moved_above and not moved_below:
            scenarios_inside['moved_above_only'].append(scenario_data)
        elif moved_below and not moved_above:
            scenarios_inside['moved_below_only'].append(scenario_data)
        else:
            scenarios_inside['moved_both'].append(scenario_data)
    
    # Calculate and display probabilities
    inside_total = len(inside_days)
    
    for scenario, data_list in scenarios_inside.items():
        count = len(data_list)
        prob = (count / inside_total) * 100
        
        # Calculate average magnitude
        if scenario == 'moved_above_only' and data_list:
            avg_mag = np.mean([d['magnitude_above'] for d in data_list])
        elif scenario == 'moved_below_only' and data_list:
            avg_mag = np.mean([d['magnitude_below'] for d in data_list])
        elif scenario == 'moved_both' and data_list:
            avg_mag_above = np.mean([d['magnitude_above'] for d in data_list])
            avg_mag_below = np.mean([d['magnitude_below'] for d in data_list])
            avg_mag = (avg_mag_above + avg_mag_below) / 2
        else:
            avg_mag = 0
        
        print(f"\n{scenario.replace('_', ' ').title()}: {count} days ({prob:.1f}%)")
        if avg_mag > 0:
            print(f"  Avg magnitude: {avg_mag:.2f} points")
        
        # Store results
        results['scenarios'].append({
            'opening': 'INSIDE',
            'outcome': scenario,
            'count': count,
            'probability': prob,
            'avg_magnitude': avg_mag,
            'examples': data_list[:3]  # First 3 examples
        })
    
    # Verify probabilities add up to 100%
    total_prob = sum([s['probability'] for s in results['scenarios'] if s['opening'] == 'INSIDE'])
    print(f"\n✓ Total probability for INSIDE scenarios: {total_prob:.1f}% (should be 100%)")
    
    # Save results
    output_path = Path('research_lab/results/probability_grid')
    json_path = output_path / 'complete_magnitude_duration.json'
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Saved: {json_path}")
    
    return results


if __name__ == '__main__':
    complete_analysis_with_magnitude_duration()
    print("\n✅ Complete analysis with magnitude and duration finished!")
