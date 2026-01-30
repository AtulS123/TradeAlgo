"""
Calculate detailed gap scenario breakdowns to fill x% values
"""

import pandas as pd
import numpy as np

# Load data
daily = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\daily_classification.csv')
daily['date'] = pd.to_datetime(daily['date'])

# Calculate prev day mid
daily['prev_mid'] = (daily['prev_high'] + daily['prev_low']) / 2

print("="*80)
print("GAP UP SCENARIO BREAKDOWN (Opens ABOVE prev high)")
print("="*80)

gap_up = daily[daily['opening_position'] == 'ABOVE']
total_gap_up = len(gap_up)

print(f"\nTotal gap up days: {total_gap_up}")

# Did it touch prev day high within the day?
touched_high = gap_up[gap_up['day_low'] <= gap_up['prev_high']]
not_touched_high = gap_up[gap_up['day_low'] > gap_up['prev_high']]

print(f"\nTouched prev day high (gap fill): {len(touched_high)} ({len(touched_high)/total_gap_up*100:.1f}%)")
print(f"Did NOT touch prev day high: {len(not_touched_high)} ({len(not_touched_high)/total_gap_up*100:.1f}%)")

# Of those that touched, how far did they go?
print(f"\n--- Of the {len(touched_high)} that filled the gap ---")
stayed_above_low = touched_high[touched_high['day_low'] >= touched_high['prev_low']]
went_to_mid = touched_high[(touched_high['day_low'] < touched_high['prev_mid']) & (touched_high['day_low'] >= touched_high['prev_low'])]
went_below_low = touched_high[touched_high['day_low'] < touched_high['prev_low']]

print(f"Stayed above prev low: {len(stayed_above_low)} ({len(stayed_above_low)/total_gap_up*100:.1f}%)")
print(f"Went to range mid: {len(went_to_mid)} ({len(went_to_mid)/total_gap_up*100:.1f}%)")  
print(f"Went below prev low: {len(went_below_low)} ({len(went_below_low)/total_gap_up*100:.1f}%)")

print("\n" + "="*80)
print("GAP DOWN SCENARIO BREAKDOWN (Opens BELOW prev low)")
print("="*80)

gap_down = daily[daily['opening_position'] == 'BELOW']
total_gap_down = len(gap_down)

print(f"\nTotal gap down days: {total_gap_down}")

# Did it touch prev day low within the day?
touched_low = gap_down[gap_down['day_high'] >= gap_down['prev_low']]
not_touched_low = gap_down[gap_down['day_high'] < gap_down['prev_low']]

print(f"\nTouched prev day low (gap fill): {len(touched_low)} ({len(touched_low)/total_gap_down*100:.1f}%)")
print(f"Did NOT touch prev day low: {len(not_touched_low)} ({len(not_touched_low)/total_gap_down*100:.1f}%)")

# Of those that touched, how far did they go?
print(f"\n--- Of the {len(touched_low)} that filled the gap ---")
stayed_below_high = touched_low[touched_low['day_high'] <= touched_low['prev_high']]
went_to_mid = touched_low[(touched_low['day_high'] > touched_low['prev_mid']) & (touched_low['day_high'] <= touched_low['prev_high'])]
went_above_high = touched_low[touched_low['day_high'] > touched_low['prev_high']]

print(f"Stayed below prev high: {len(stayed_below_high)} ({len(stayed_below_high)/total_gap_down*100:.1f}%)")
print(f"Went to range mid: {len(went_to_mid)} ({len(went_to_mid)/total_gap_down*100:.1f}%)")
print(f"Went above prev high: {len(went_above_high)} ({len(went_above_high)/total_gap_down*100:.1f}%)")

print("\n✅ Analysis complete!")
