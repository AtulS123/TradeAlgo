"""
Enhanced Time-Based Transition Analysis
========================================

Analyzes EXACTLY when price transitions between ranges throughout the day
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
import json
from pathlib import Path
from collections import defaultdict


def analyze_intraday_transitions():
    """Analyze time-of-day for all state transitions"""
    
    print("\n" + "="*80)
    print("ENHANCED INTRADAY TRANSITION ANALYSIS")
    print("="*80)
    
    # Load data
    data_path = r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv'
    df = pd.read_csv(data_path)
    df['datetime'] = pd.to_datetime(df['date'])
    df = df.sort_values('datetime').reset_index(drop=True)
    
    # Resample to 5-min
    df.set_index('datetime', inplace=True)
    df_5min = df.resample('5T').agg({
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
        'datetime': 'first'
    }).reset_index()
    daily_agg.columns = ['date', 'day_high', 'day_low', 'day_open', 'day_start']
    daily_agg['prev_high'] = daily_agg['day_high'].shift(1)
    daily_agg['prev_low'] = daily_agg['day_low'].shift(1)
    daily_agg = daily_agg.dropna()
    
    # Classify opening positions
    def classify_open(row):
        if row['day_open'] > row['prev_high']:
            return 'ABOVE'
        elif row['day_open'] < row['prev_low']:
            return 'BELOW'
        else:
            return 'INSIDE'
    
    daily_agg['opening_position'] = daily_agg.apply(classify_open, axis=1)
    
    # Track transitions
    transition_times = {
        'inside_to_above': [],
        'inside_to_below': [],
        'above_to_inside': [],
        'below_to_inside': [],
        'inside_to_above_then_back': [],
        'inside_to_below_then_back': []
    }
    
    print("\nAnalyzing intraday transitions...")
    
    for _, day in daily_agg.iterrows():
        date = day['date']
        opening_pos = day['opening_position']
        prev_high = day['prev_high']
        prev_low = day['prev_low']
        
        # Get all candles for this day
        day_candles = df_5min[df_5min['date'] == date].copy()
        if len(day_candles) == 0:
            continue
        
        # Track state throughout the day
        current_state = opening_pos
        first_break_above = None
        first_break_below = None
        returned_from_above = None
        returned_from_below = None
        
        for idx, candle in day_candles.iterrows():
            candle_time = candle['time']
            
            # Skip first 15 minutes (opening volatility)
            if candle_time < time(9, 30):
                continue
            
            # Track transitions
            if opening_pos == 'INSIDE':
                # INSIDE → ABOVE transition
                if candle['high'] > prev_high and first_break_above is None:
                    first_break_above = candle_time
                    transition_times['inside_to_above'].append(candle_time)
                
                # INSIDE → BELOW transition
                if candle['low'] < prev_low and first_break_below is None:
                    first_break_below = candle_time
                    transition_times['inside_to_below'].append(candle_time)
                
                # Check for return after breaking above
                if first_break_above and returned_from_above is None:
                    if candle['low'] <= prev_high:
                        returned_from_above = candle_time
                        transition_times['inside_to_above_then_back'].append({
                            'break_time': first_break_above,
                            'return_time': candle_time,
                            'duration_minutes': (datetime.combine(datetime.today(), candle_time) - 
                                                datetime.combine(datetime.today(), first_break_above)).total_seconds() / 60
                        })
                
                # Check for return after breaking below
                if first_break_below and returned_from_below is None:
                    if candle['high'] >= prev_low:
                        returned_from_below = candle_time
                        transition_times['inside_to_below_then_back'].append({
                            'break_time': first_break_below,
                            'return_time': candle_time,
                            'duration_minutes': (datetime.combine(datetime.today(), candle_time) - 
                                                datetime.combine(datetime.today(), first_break_below)).total_seconds() / 60
                        })
            
            elif opening_pos == 'ABOVE':
                # ABOVE → INSIDE transition
                if candle['low'] <= prev_high and first_break_below is None:
                    first_break_below = candle_time
                    transition_times['above_to_inside'].append(candle_time)
            
            elif opening_pos == 'BELOW':
                # BELOW → INSIDE transition
                if candle['high'] >= prev_low and first_break_above is None:
                    first_break_above = candle_time
                    transition_times['below_to_inside'].append(candle_time)
    
    # Analyze timing distributions
    results = {}
    
    print("\n" + "="*80)
    print("TRANSITION TIMING ANALYSIS")
    print("="*80)
    
    # Analyze each transition type
    for trans_type, times in transition_times.items():
        if 'then_back' in trans_type:
            continue  # Handle these separately
        
        if not times:
            continue
        
        # Group by time windows (30-min buckets)
        time_dist = defaultdict(int)
        for t in times:
            hour = t.hour
            bucket = t.minute // 30
            time_key = f"{hour:02d}:{bucket*30:02d}"
            time_dist[time_key] += 1
        
        total = len(times)
        
        print(f"\n📊 {trans_type.replace('_', ' ').upper()}")
        print(f"   Total occurrences: {total}")
        print("   " + "-"*70)
        
        # Sort and display
        sorted_times = sorted(time_dist.items(), key=lambda x: -x[1])
        for time_window, count in sorted_times[:10]:  # Top 10
            pct = (count / total) * 100
            bar = '█' * int(pct / 2)
            print(f"   {time_window} - {time_window.split(':')[0]}:29  |{bar:30s} {count:4d} ({pct:5.2f}%)")
        
        results[trans_type] = {
            'total_occurrences': total,
            'distribution': dict(time_dist),
            'top_time': sorted_times[0][0] if sorted_times else None,
            'top_time_count': sorted_times[0][1] if sorted_times else 0,
            'top_time_pct': (sorted_times[0][1] / total * 100) if sorted_times else 0
        }
    
    # Analyze return times
    print("\n" + "="*80)
    print("MEAN REVERSION TIMING ANALYSIS")
    print("="*80)
    
    for return_type in ['inside_to_above_then_back', 'inside_to_below_then_back']:
        returns = transition_times[return_type]
        if not returns:
            continue
        
        print(f"\n📊 {return_type.replace('_', ' ').upper()}")
        print(f"   Total reversions: {len(returns)}")
        
        # Analyze return times
        return_time_dist = defaultdict(int)
        durations = []
        
        for ret in returns:
            return_time = ret['return_time']
            duration = ret['duration_minutes']
            durations.append(duration)
            
            hour = return_time.hour
            bucket = return_time.minute // 30
            time_key = f"{hour:02d}:{bucket*30:02d}"
            return_time_dist[time_key] += 1
        
        # Time distribution
        print("\n   When does price return to range?")
        print("   " + "-"*70)
        sorted_times = sorted(return_time_dist.items(), key=lambda x: -x[1])
        for time_window, count in sorted_times[:8]:
            pct = (count / len(returns)) * 100
            bar = '█' * int(pct / 2)
            print(f"   {time_window} - {time_window.split(':')[0]}:29  |{bar:30s} {count:4d} ({pct:5.2f}%)")
        
        # Duration analysis
        avg_duration = np.mean(durations)
        median_duration = np.median(durations)
        
        print(f"\n   ⏱️  How long until return?")
        print(f"      Average: {avg_duration:.1f} minutes ({avg_duration/60:.1f} hours)")
        print(f"      Median: {median_duration:.1f} minutes ({median_duration/60:.1f} hours)")
        
        results[return_type] = {
            'total_reversions': len(returns),
            'return_time_distribution': dict(return_time_dist),
            'avg_duration_minutes': avg_duration,
            'median_duration_minutes': median_duration
        }
    
    # Save results
    output_path = Path('research_lab/results/probability_grid')
    
    # Save JSON
    json_path = output_path / 'intraday_transition_analysis.json'
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✅ Saved: {json_path}")
    
    # Create CSV summary
    summary_data = []
    
    for trans_type, data in results.items():
        if 'then_back' in trans_type:
            summary_data.append({
                'Transition_Type': trans_type.replace('_', ' ').title(),
                'Total_Events': data.get('total_reversions', 0),
                'Most_Common_Time': list(data.get('return_time_distribution', {}).keys())[0] if data.get('return_time_distribution') else 'N/A',
                'Avg_Duration_Minutes': f"{data.get('avg_duration_minutes', 0):.1f}",
                'Median_Duration_Minutes': f"{data.get('median_duration_minutes', 0):.1f}"
            })
        else:
            summary_data.append({
                'Transition_Type': trans_type.replace('_', ' ').title(),
                'Total_Events': data.get('total_occurrences', 0),
                'Most_Common_Time': data.get('top_time', 'N/A'),
                'Top_Time_Count': data.get('top_time_count', 0),
                'Top_Time_Percentage': f"{data.get('top_time_pct', 0):.1f}%"
            })
    
    df_summary = pd.DataFrame(summary_data)
    csv_path = output_path / 'INTRADAY_TRANSITION_TIMES.csv'
    df_summary.to_csv(csv_path, index=False)
    print(f"✅ Saved: {csv_path}")
    
    return results


if __name__ == '__main__':
    analyze_intraday_transitions()
    print("\n✅ Enhanced timing analysis complete!")
