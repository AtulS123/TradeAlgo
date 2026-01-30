import pandas as pd
from datetime import time, datetime

# Load Data
df_5min_full = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv')
df_5min_full['datetime'] = pd.to_datetime(df_5min_full['date'])
df_5min_full['date_only'] = df_5min_full['datetime'].dt.date
df_5min_full['time'] = df_5min_full['datetime'].dt.time
df_5min_full['minutes_since_915'] = (df_5min_full['datetime'].dt.hour * 60 + df_5min_full['datetime'].dt.minute) - (9 * 60 + 15)

# Calculate Daily
daily_full = df_5min_full.groupby('date_only').agg({
    'high': 'max',
    'low': 'min'
}).reset_index()
daily_full['prev_high'] = daily_full['high'].shift(1)
daily_full['prev_low'] = daily_full['low'].shift(1)

# Debug 2025-07-15
target_date_str = '2025-07-15'
# Convert string to date object
target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()

print(f"\nAnalyzing Date: {target_date}")

day_stats = daily_full[daily_full['date_only'] == target_date]
if len(day_stats) == 0:
    print("Date not found in daily stats!")
else:
    prev_high = day_stats.iloc[0]['prev_high']
    prev_low = day_stats.iloc[0]['prev_low']
    print(f"Prev High: {prev_high}")
    print(f"Prev Low: {prev_low}")

    # Get 5-min candles
    candles = df_5min_full[df_5min_full['date_only'] == target_date].sort_values('datetime')
    print("\nFirst 10 Candles:")
    print(candles[['time', 'open', 'high', 'low', 'close', 'minutes_since_915']].head(10))

    # Check for touches
    touched_high = candles[candles['high'] >= prev_high]
    if len(touched_high) > 0:
        first_touch = touched_high.iloc[0]
        print(f"\nFirst Touched High at {first_touch['time']} (Min: {first_touch['minutes_since_915']})")
        print(f"Hit Level: {prev_high}")
        with open('debug_log.txt', 'w') as f:
            f.write(f"Prev High: {prev_high}\n")
            # To get day_close, we need to add 'close' to the daily_full aggregation
            # For now, let's assume day_close is the last candle's close for the target_date
            # This part needs to be adjusted if 'day_close' is not in day_stats
            # For demonstration, let's use the last candle's close for the day
            day_close = candles.iloc[-1]['close'] # Assuming day_close is the last candle's close
            f.write(f"Day Close: {day_close}\n")
            
            if day_close > prev_high:
                f.write("Result: Day Close > Prev High (Should be in Bottom Row)\n")
            else:
                f.write("Result: Day Close <= Prev High (Should NOT be in Bottom Row)\n")
                
            first_candle = candles.iloc[0]
            f.write(f"First Candle (09:15): Open={first_candle['open']}, Close={first_candle['close']}, High={first_candle['high']}, Low={first_candle['low']}\n")
            open_inside = (first_candle['open'] < prev_high) and (first_candle['open'] > prev_low)
            close_inside = (first_candle['close'] < prev_high) and (first_candle['close'] > prev_low)
            f.write(f"Open Inside Range? {open_inside}\n")
            f.write(f"Close Inside Range? {close_inside}\n")
            
            if len(touched_high) > 0:
                f.write(f"First Touched High at {first_touch['time']} (Min: {first_touch['minutes_since_915']})\n")
            else:
                f.write("Did NOT touch Prev High\n")
    else:
        print("\nDid NOT touch Prev High")
    
    # To get day_close, we need to add 'close' to the daily_full aggregation
    # For now, let's assume day_close is the last candle's close for the target_date
    # This part needs to be adjusted if 'day_close' is not in day_stats
    # For demonstration, let's use the last candle's close for the day
    day_close = candles.iloc[-1]['close'] # Assuming day_close is the last candle's close
    print(f"Day Close: {day_close}")
    if day_close > prev_high:
        print("Result: Day Close > Prev High (Should be in Bottom Row)")
    else:
        print("Result: Day Close <= Prev High (Should NOT be in Bottom Row)")
        
    first_candle = candles.iloc[0]
    print(f"\nFirst Candle (09:15): Open={first_candle['open']}, Close={first_candle['close']}, High={first_candle['high']}, Low={first_candle['low']}")
    open_inside = (first_candle['open'] < prev_high) and (first_candle['open'] > prev_low)
    close_inside = (first_candle['close'] < prev_high) and (first_candle['close'] > prev_low)
    print(f"Open Inside Range? {open_inside}")
    print(f"Close Inside Range? {close_inside}")
