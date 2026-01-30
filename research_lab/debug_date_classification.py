import pandas as pd
import json
from datetime import datetime

# Config
target_date_str = '2025-07-07'
json_path = r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\final_corrected_stats.json'
csv_path = r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv'

# Load JSON
with open(json_path, 'r') as f:
    stats = json.load(f)

# Find Date in JSON
found_buckets = []
def search_json(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            search_json(v, path + " -> " + k)
    elif isinstance(node, list):
        if target_date_str in node:
            # Check if this list is a "dates" list inside a bucket/row
            # The path usually ends with "-> dates". We want the parent bucket name.
            found_buckets.append(path)

# Redirect Output
with open('debug_date_log.txt', 'w') as log:
    def lprint(msg):
        print(msg)
        log.write(msg + "\n")

    search_json(stats)

    lprint(f"--- Search Result for {target_date_str} ---")
    if found_buckets:
        lprint("Found in buckets:")
        for b in found_buckets:
            lprint(b)
    else:
        lprint("Date NOT found in any outcome bucket dates list.")

    # Load Data for Calculations
    df_5min = pd.read_csv(csv_path)
    df_5min['datetime'] = pd.to_datetime(df_5min['date'])
    df_5min['date_only'] = df_5min['datetime'].dt.date
    df_5min['minutes_since_915'] = (df_5min['datetime'].dt.hour * 60 + df_5min['datetime'].dt.minute) - (9 * 60 + 15)

    # Get Target Date Data
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    day_data = df_5min[df_5min['date_only'] == target_date].sort_values('datetime')

    if len(day_data) == 0:
        lprint("\nNO DATA for target date in CSV.")
        exit()

    # Get Prev Day Data
    unique_dates = sorted(df_5min['date_only'].unique())
    try:
        idx = unique_dates.index(target_date)
        if idx == 0:
            lprint("Target date is first day, no prev data.")
            exit()
        prev_date = unique_dates[idx-1]
        prev_data = df_5min[df_5min['date_only'] == prev_date]
        
        prev_high = prev_data['high'].max()
        prev_low = prev_data['low'].min()
        prev_mid = (prev_high + prev_low) / 2
        prev_range = prev_high - prev_low
        
        lprint(f"\n--- Statistics for {target_date_str} ---")
        lprint(f"Prev Date: {prev_date}")
        lprint(f"Prev High: {prev_high}")
        lprint(f"Prev Low:  {prev_low}")
        lprint(f"Prev Range: {prev_range}")
        lprint(f"10% Extension Threshold ABOVE: {prev_high + 0.1 * prev_range}")
        lprint(f"10% Extension Threshold BELOW: {prev_low - 0.1 * prev_range}")
        
        # Day Stats
        day_open = day_data.iloc[0]['open'] # Day Open
        first_candle = day_data.iloc[0]
        day_high = day_data['high'].max()
        day_low = day_data['low'].min()
        day_close = day_data.iloc[-1]['close'] # Last Close
        
        lprint(f"\nDay Open: {day_open}")
        lprint(f"First Candle (09:15) Close: {first_candle['close']}")
        lprint(f"Day High: {day_high}")
        lprint(f"Day Low:  {day_low}")
        lprint(f"Day Close: {day_close}")
        
        # Classification Logic (Current: Day Open)
        if day_open > prev_high: lprint("Opening: ABOVE")
        elif day_open < prev_low: lprint("Opening: BELOW")
        else: lprint("Opening: INSIDE")
        
        # First Touch Analysis
        touched_high = day_data[day_data['high'] >= prev_high]
        touched_low = day_data[day_data['low'] <= prev_low]
        
        t_high = touched_high.iloc[0]['minutes_since_915'] if len(touched_high) > 0 else None
        t_low = touched_low.iloc[0]['minutes_since_915'] if len(touched_low) > 0 else None
        
        lprint(f"\nTime to First Touch High: {t_high} min")
        lprint(f"Time to First Touch Low:  {t_low} min")
        
        if t_high is not None and (t_low is None or t_high < t_low):
            lprint("-> Touched HIGH First")
            # Extension Check (CLOSE based)
            thresh = prev_high + 0.1 * prev_range
            after_high = day_data[day_data['minutes_since_915'] >= t_high]
            extended = after_high[after_high['close'] >= thresh]
            if len(extended) > 0:
                lprint(f"-> Extended > 10% (Close based) at {extended.iloc[0]['minutes_since_915']} min")
            else:
                lprint("-> Did NOT extend > 10% (Close based)")
                
        elif t_low is not None:
            lprint("-> Touched LOW First")
            # Extension Check (CLOSE based)
            thresh = prev_low - 0.1 * prev_range
            after_low = day_data[day_data['minutes_since_915'] >= t_low]
            extended = after_low[after_low['close'] <= thresh]
            if len(extended) > 0:
                lprint(f"-> Extended > 10% (Close based) at {extended.iloc[0]['minutes_since_915']} min")
            else:
                lprint("-> Did NOT extend > 10% (Close based)")
                
        else:
            lprint("-> Stayed Inside Range (Scenario C)")

        # Closing Analysis Check
        lprint("\n--- Closing Analysis Check ---")
        cutoff = 45 # 10 AM
        if day_close > prev_high:
            lprint("Close > Prev High (Should be in Bottom Row)")
            if t_high is not None and t_high <= cutoff:
                lprint("-> Early Breakout (Touched < 10 AM)")
            else:
                lprint("-> Late Breakout")
        elif day_close < prev_low:
            lprint("Close < Prev Low (Should be in Bottom Row)")
        else:
            lprint("Close Inside (Not in Bottom Analysis)")

    except Exception as e:
        lprint(f"Error: {e}")
