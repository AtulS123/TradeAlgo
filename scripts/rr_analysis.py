import pandas as pd
import numpy as np

def load_and_preprocess_data(file_path):
    """
    Loads Nifty 50 minute data, resamples to 5-minute candles, and filters for market hours.
    """
    print(f"Loading data from: {file_path}")
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None

    df['datetime'] = pd.to_datetime(df['date'])
    df.set_index('datetime', inplace=True)
    
    if 'date' in df.columns:
        df.drop(columns=['date'], inplace=True)

    ohlc_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }
    
    df_5min = df.resample('5min').agg(ohlc_dict)
    df_5min.dropna(inplace=True)

    df_5min['time'] = df_5min.index.time
    market_start = pd.to_datetime("09:15:00").time()
    market_end = pd.to_datetime("15:25:00").time()
    
    df_5min = df_5min[(df_5min['time'] >= market_start) & (df_5min['time'] <= market_end)].copy()
    df_5min.drop(columns=['time'], inplace=True)
    
    return df_5min

def calculate_daily_stats(df_5min):
    """
    Calculates Previous Day Range (PDR) stats based on candle bodies (Open/Close).
    """
    df_5min['date_only'] = df_5min.index.date
    
    daily_stats = []
    grouped = df_5min.groupby('date_only')
    
    for date, group in grouped:
        opens = group['open'].values
        closes = group['close'].values
        all_body_values = np.concatenate([opens, closes])
        
        day_max = np.max(all_body_values)
        day_min = np.min(all_body_values)
        
        daily_stats.append({
            'date': date,
            'day_max': day_max,
            'day_min': day_min
        })
        
    stats_df = pd.DataFrame(daily_stats)
    stats_df.set_index('date', inplace=True)
    stats_df.sort_index(inplace=True)
    
    stats_df['prev_day_max'] = stats_df['day_max'].shift(1)
    stats_df['prev_day_min'] = stats_df['day_min'].shift(1)
    
    stats_df.dropna(inplace=True)
    
    stats_df['range_height'] = stats_df['prev_day_max'] - stats_df['prev_day_min']
    stats_df['buffer'] = stats_df['range_height'] * 0.05
    
    stats_df['resistance'] = stats_df['prev_day_max'] + stats_df['buffer']
    stats_df['support'] = stats_df['prev_day_min'] - stats_df['buffer']
    
    return stats_df

def classify_day(open_price, close_price, support, resistance):
    if open_price < support:
        start_state = 'Below'
    elif open_price > resistance:
        start_state = 'Above'
    else:
        start_state = 'Inside'
        
    if close_price < support:
        end_state = 'Below'
    elif close_price > resistance:
        end_state = 'Above'
    else:
        end_state = 'Inside'
        
    return start_state, end_state

def simulate_trade(day_data, entry_price, sl_price, target_price):
    """
    Simulates a trade from the 2nd candle onwards.
    Returns: 'TP', 'SL', or 'EOD'
    """
    if len(day_data) <= 1:
        return 'EOD'
        
    subsequent_candles = day_data.iloc[1:]
    
    for idx, row in subsequent_candles.iterrows():
        # Check High for TP and Low for SL
        # Assuming we check both in the same candle, worst case (SL first) or best case?
        # Standard conservative: Check if Low hit SL first? 
        # Actually, in a 5-min candle, we don't know the path.
        # But usually, if both are hit in same candle, it's a volatile mess.
        # Let's assume if Low <= SL, we are out.
        
        if row['low'] <= sl_price:
            return 'SL'
        if row['high'] >= target_price:
            return 'TP'
            
    return 'EOD'

def run_rr_analysis(file_path):
    df_5min = load_and_preprocess_data(file_path)
    if df_5min is None:
        return

    daily_stats = calculate_daily_stats(df_5min)
    df_grouped = df_5min.groupby('date_only')
    
    # Scenarios: Name -> (SL_Func, TP_Func)
    # SL_Func takes (entry, candle_low) -> sl_price
    # TP_Func takes (entry, risk) -> tp_price
    
    scenarios = {
        "Candle Low SL (1:2)": {
            'sl_calc': lambda entry, low: low,
            'tp_calc': lambda entry, risk: entry + (2 * risk)
        },
        "Fixed 20pt SL (1:2)": {
            'sl_calc': lambda entry, low: entry - 20,
            'tp_calc': lambda entry, risk: entry + 40
        },
        "Fixed 30pt SL (1:2)": {
            'sl_calc': lambda entry, low: entry - 30,
            'tp_calc': lambda entry, risk: entry + 60
        }
    }
    
    results = {k: {'TP': 0, 'SL': 0, 'EOD': 0, 'Total': 0} for k in scenarios.keys()}
    
    print(f"Analyzing {len(daily_stats)} trading days for 'Above -> Above' 1:2 R:R setups...")
    
    for date, stats in daily_stats.iterrows():
        if date not in df_grouped.groups:
            continue
            
        day_data = df_grouped.get_group(date)
        if day_data.empty:
            continue
            
        opening_candle = day_data.iloc[0]
        opening_close = opening_candle['close']
        opening_open = opening_candle['open']
        opening_low = opening_candle['low']
        
        closing_candle = day_data.iloc[-1]
        closing_val = closing_candle['close']
        
        support = stats['support']
        resistance = stats['resistance']
        
        start_open_state, _ = classify_day(opening_open, closing_val, support, resistance)
        start_close_state, _ = classify_day(opening_close, closing_val, support, resistance)
        
        composite_start = f"{start_open_state}->{start_close_state}"
        
        if composite_start == "Above->Above":
            entry_price = opening_close
            
            for name, funcs in scenarios.items():
                sl_price = funcs['sl_calc'](entry_price, opening_low)
                risk = entry_price - sl_price
                
                # Sanity check for Candle Low: if Close == Low (Risk=0), skip or assume min risk?
                if risk <= 0:
                    # Treat as invalid trade or skip
                    continue
                    
                target_price = funcs['tp_calc'](entry_price, risk)
                
                outcome = simulate_trade(day_data, entry_price, sl_price, target_price)
                
                results[name][outcome] += 1
                results[name]['Total'] += 1

    print(f"\n--- 1:2 Risk:Reward Analysis (Above -> Above) ---")
    print(f"{'Scenario':<25} | {'Win Rate (TP)':<15} | {'Loss Rate (SL)':<15} | {'Timeout (EOD)':<15}")
    print("-" * 80)
    
    for name, counts in results.items():
        total = counts['Total']
        if total == 0:
            continue
            
        tp_rate = (counts['TP'] / total) * 100
        sl_rate = (counts['SL'] / total) * 100
        eod_rate = (counts['EOD'] / total) * 100
        
        print(f"{name:<25} | {tp_rate:.2f}% ({counts['TP']})   | {sl_rate:.2f}% ({counts['SL']})   | {eod_rate:.2f}% ({counts['EOD']})")

if __name__ == "__main__":
    file_path = r"C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv"
    run_rr_analysis(file_path)
