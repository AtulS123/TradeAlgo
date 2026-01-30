import pandas as pd
from datetime import date

# Load and process data
df = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv')
df['datetime'] = pd.to_datetime(df['date'])
df.set_index('datetime', inplace=True)

# Resample to 5-min
df_5min = df.resample('5min').agg({
    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'
}).dropna()
df_5min['date'] = df_5min.index.date
df_5min['time'] = df_5min.index.time
df_5min['min_since_915'] = df_5min.index.hour * 60 + df_5min.index.minute - 555
df_5min.reset_index(inplace=True)

# Analyze Jan 24, 2025
jan24 = df_5min[df_5min['date'] == date(2025, 1, 24)].copy()
jan23 = df_5min[df_5min['date'] == date(2025, 1, 23)].copy()

prev_high = jan23['high'].max()
prev_low = jan23['low'].min()
prev_mid = (prev_high + prev_low) / 2
prev_range = prev_high - prev_low

first = jan24[jan24['min_since_915'] == 0].iloc[0]
day_high = jan24['high'].max()
day_low = jan24['low'].min()
day_close = jan24['close'].iloc[-1]

print("JAN 24, 2025 DATA:")
print(f"Prev High: {prev_high:.2f}, Mid: {prev_mid:.2f}, Low: {prev_low:.2f}, Range: {prev_range:.2f}")
print(f"\nFirst 5-min candle: Open={first['open']:.2f}, High={first['high']:.2f}, Low={first['low']:.2f}, Close={first['close']:.2f}")
print(f"Day: High={day_high:.2f}, Low={day_low:.2f}, Close={day_close:.2f}")

# Classification
if first['close'] > prev_high:
    print(f"\nOPEN CLASS: ABOVE (close {first['close']:.2f} > {prev_high:.2f})")
elif first['close'] < prev_low:
    print(f"\nOPEN CLASS: BELOW (close {first['close']:.2f} < {prev_low:.2f})")
else:
    print(f"\nOPEN CLASS: INSIDE ({prev_low:.2f} < {first['close']:.2f} < {prev_high:.2f})")
    
    # Check touches
    t_high = jan24[jan24['high'] >= prev_high]
    t_low = jan24[jan24['low'] <= prev_low]
    
    if len(t_high) > 0:
        time_h = t_high.iloc[0]['min_since_915']
        print(f"  Touched HIGH at {time_h} min")
        
        # Check 10% extension
        thresh = prev_high + 0.1 * prev_range
        after = jan24[jan24['min_since_915'] >= time_h]
        ext = after[after['close'] >= thresh]
        
        if len(ext) > 0:
            time_e = ext.iloc[0]['min_since_915']
            print(f"  Extended 10% at {time_e} min (close >= {thresh:.2f})")
            
            # Check mid touch
            between = after[after['min_since_915'] <= time_e]
            mid_touch = between[between['low'] <= prev_mid]
            
            if len(mid_touch) > 0:
                print(f"  Touched mid at {mid_touch.iloc[0]['min_since_915']} min BEFORE extension")
                print(f"  CATEGORY: ROW 2 RETRACED")
            else:
                print(f"  Did NOT touch mid before extension")
                print(f"  CATEGORY: ROW 2 DIRECT")
        else:
            print(f"  No 10% extension")
            print(f"  CATEGORY: ROW 1")
    
    if len(t_low) > 0:
        time_l = t_low.iloc[0]['min_since_915']
        print(f"  Touched LOW at {time_l} min")

print(f"\nCLOSE CLASS: ", end="")
if day_close > prev_high:
    print(f"ABOVE ({day_close:.2f} > {prev_high:.2f})")
elif day_close < prev_low:
    print(f"BELOW ({day_close:.2f} < {prev_low:.2f})")
else:
    print(f"INSIDE")
