"""
Third-Order Probability Analysis
=================================

Analyzes what happens AFTER price returns to range following a breakout.

Sequence:
1st Order: Inside → Broke Below/Above
2nd Order: After Breaking → Returned to Range (87%/85%)
3rd Order: After Returning → Stays Inside OR Breaks Out Again?
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
import json
from pathlib import Path
from collections import defaultdict


def analyze_third_order_probabilities():
    """Analyze behavior after price returns to range"""
    
    print("\n" + "="*80)
    print("THIRD-ORDER PROBABILITY ANALYSIS")
    print("What happens AFTER price returns to range following a breakout?")
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
        'open': 'first'
    }).reset_index()
    daily_agg.columns = ['date', 'day_high', 'day_low', 'day_open']
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
    
    # Track third-order probabilities
    third_order = {
        'inside_below_return_then': defaultdict(int),
        'inside_above_return_then': defaultdict(int)
    }
    
    print("\nAnalyzing third-order patterns...")
    
    for _, day in daily_agg.iterrows():
        date = day['date']
        opening_pos = day['opening_position']
        prev_high = day['prev_high']
        prev_low = day['prev_low']
        
        if opening_pos != 'INSIDE':
            continue
        
        # Get all candles for this day
        day_candles = df_5min[df_5min['date'] == date].copy()
        if len(day_candles) == 0:
            continue
        
        # Track the sequence of events
        broke_below = False
        broke_above = False
        returned_from_below = False
        returned_from_above = False
        return_time_below = None
        return_time_above = None
        
        for idx, candle in day_candles.iterrows():
            # Check if broke below
            if not broke_below and candle['low'] < prev_low:
                broke_below = True
            
            # Check if broke above
            if not broke_above and candle['high'] > prev_high:
                broke_above = True
            
            # Check if returned from below
            if broke_below and not returned_from_below:
                if candle['high'] >= prev_low:
                    returned_from_below = True
                    return_time_below = candle['time']
            
            # Check if returned from above
            if broke_above and not returned_from_above:
                if candle['low'] <= prev_high:
                    returned_from_above = True
                    return_time_above = candle['time']
        
        # THIRD ORDER ANALYSIS
        # Scenario 1: Opened inside → Broke below → Returned to range → THEN WHAT?
        if broke_below and returned_from_below and not broke_above:
            # Check what happened AFTER returning to range
            candles_after_return = day_candles[day_candles['time'] > return_time_below]
            
            if len(candles_after_return) == 0:
                # Returned at end of day
                third_order['inside_below_return_then']['returned_at_eod'] += 1
            else:
                # Check subsequent behavior
                stayed_inside_after = True
                broke_below_again = False
                broke_above_after = False
                
                for idx, candle in candles_after_return.iterrows():
                    if candle['low'] < prev_low:
                        broke_below_again = True
                        stayed_inside_after = False
                    if candle['high'] > prev_high:
                        broke_above_after = True
                        stayed_inside_after = False
                
                if stayed_inside_after:
                    third_order['inside_below_return_then']['stayed_inside_rest_of_day'] += 1
                elif broke_below_again and not broke_above_after:
                    third_order['inside_below_return_then']['broke_below_again'] += 1
                elif broke_above_after and not broke_below_again:
                    third_order['inside_below_return_then']['broke_above_opposite'] += 1
                else:
                    third_order['inside_below_return_then']['broke_both_directions'] += 1
        
        # Scenario 2: Opened inside → Broke above → Returned to range → THEN WHAT?
        if broke_above and returned_from_above and not broke_below:
            # Check what happened AFTER returning to range
            candles_after_return = day_candles[day_candles['time'] > return_time_above]
            
            if len(candles_after_return) == 0:
                # Returned at end of day
                third_order['inside_above_return_then']['returned_at_eod'] += 1
            else:
                # Check subsequent behavior
                stayed_inside_after = True
                broke_above_again = False
                broke_below_after = False
                
                for idx, candle in candles_after_return.iterrows():
                    if candle['high'] > prev_high:
                        broke_above_again = True
                        stayed_inside_after = False
                    if candle['low'] < prev_low:
                        broke_below_after = True
                        stayed_inside_after = False
                
                if stayed_inside_after:
                    third_order['inside_above_return_then']['stayed_inside_rest_of_day'] += 1
                elif broke_above_again and not broke_below_after:
                    third_order['inside_above_return_then']['broke_above_again'] += 1
                elif broke_below_after and not broke_above_again:
                    third_order['inside_above_return_then']['broke_below_opposite'] += 1
                else:
                    third_order['inside_above_return_then']['broke_both_directions'] += 1
    
    # Calculate probabilities
    print("\n" + "="*80)
    print("📊 THIRD-ORDER RESULTS")
    print("="*80)
    
    results = {}
    
    # Scenario 1: Inside → Below → Returned → ?
    if third_order['inside_below_return_then']:
        total = sum(third_order['inside_below_return_then'].values())
        
        print(f"\n🔹 INSIDE → BROKE BELOW → RETURNED TO RANGE → THEN:")
        print(f"   Total cases: {total}")
        print("   " + "-"*70)
        
        probs = {}
        for outcome, count in sorted(third_order['inside_below_return_then'].items(), 
                                     key=lambda x: -x[1]):
            prob = (count / total) * 100
            probs[outcome] = prob
            outcome_display = outcome.replace('_', ' ').title()
            print(f"   {outcome_display:35s}: {count:4d} ({prob:5.2f}%)")
        
        results['inside_below_return_then'] = {
            'total_cases': total,
            'probabilities': probs
        }
    
    # Scenario 2: Inside → Above → Returned → ?
    if third_order['inside_above_return_then']:
        total = sum(third_order['inside_above_return_then'].values())
        
        print(f"\n🔹 INSIDE → BROKE ABOVE → RETURNED TO RANGE → THEN:")
        print(f"   Total cases: {total}")
        print("   " + "-"*70)
        
        probs = {}
        for outcome, count in sorted(third_order['inside_above_return_then'].items(), 
                                     key=lambda x: -x[1]):
            prob = (count / total) * 100
            probs[outcome] = prob
            outcome_display = outcome.replace('_', ' ').title()
            print(f"   {outcome_display:35s}: {count:4d} ({prob:5.2f}%)")
        
        results['inside_above_return_then'] = {
            'total_cases': total,
            'probabilities': probs
        }
    
    # Save results
    output_path = Path('research_lab/results/probability_grid')
    
    # Save JSON
    json_path = output_path / 'third_order_probabilities.json'
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Saved: {json_path}")
    
    # Create CSV
    csv_data = []
    
    for scenario, data in results.items():
        scenario_name = scenario.replace('_', ' ').title()
        for outcome, prob in data['probabilities'].items():
            csv_data.append({
                'Scenario': scenario_name,
                'Outcome': outcome.replace('_', ' ').title(),
                'Probability': f"{prob:.2f}%",
                'Total_Cases': data['total_cases']
            })
    
    df_third = pd.DataFrame(csv_data)
    csv_path = output_path / 'third_order_probabilities.csv'
    df_third.to_csv(csv_path, index=False)
    print(f"✅ Saved: {csv_path}")
    
    print("\n" + "="*80)
    print("💡 KEY INSIGHTS")
    print("="*80)
    
    # Generate insights
    if 'inside_below_return_then' in results:
        probs = results['inside_below_return_then']['probabilities']
        stayed = probs.get('stayed_inside_rest_of_day', 0)
        broke_again = probs.get('broke_below_again', 0)
        
        print(f"\n📌 After returning from below:")
        print(f"   - {stayed:.1f}% stay inside for rest of day")
        print(f"   - {broke_again:.1f}% break below again (re-test)")
    
    if 'inside_above_return_then' in results:
        probs = results['inside_above_return_then']['probabilities']
        stayed = probs.get('stayed_inside_rest_of_day', 0)
        broke_again = probs.get('broke_above_again', 0)
        
        print(f"\n📌 After returning from above:")
        print(f"   - {stayed:.1f}% stay inside for rest of day")
        print(f"   - {broke_again:.1f}% break above again (re-test)")
    
    print("\n" + "="*80)
    
    return results


if __name__ == '__main__':
    analyze_third_order_probabilities()
    print("\n✅ Third-order probability analysis complete!")
