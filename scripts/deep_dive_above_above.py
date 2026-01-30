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

def run_deep_dive(file_path):
    df_5min = load_and_preprocess_data(file_path)
    if df_5min is None:
        return

    daily_stats = calculate_daily_stats(df_5min)
    
    mfe_data = []
    
    df_grouped = df_5min.groupby('date_only')
    
    print(f"Analyzing {len(daily_stats)} trading days for 'Above -> Above' setup...")
    
    for date, stats in daily_stats.iterrows():
        if date not in df_grouped.groups:
            continue
            
        day_data = df_grouped.get_group(date)
        
        if day_data.empty:
            continue
            
        opening_candle = day_data.iloc[0]
        opening_close = opening_candle['close']
        opening_open = opening_candle['open']
        
        closing_candle = day_data.iloc[-1]
        closing_val = closing_candle['close']
        
        support = stats['support']
        resistance = stats['resistance']
        
        start_open_state, _ = classify_day(opening_open, closing_val, support, resistance)
        start_close_state, _ = classify_day(opening_close, closing_val, support, resistance)
        
        composite_start = f"{start_open_state}->{start_close_state}"
        
        # FILTER: Only "Above -> Above"
        if composite_start == "Above->Above":
            entry_price = opening_close
            
            # Find Max High AFTER entry (from 2nd candle onwards)
            if len(day_data) > 1:
                subsequent_data = day_data.iloc[1:]
                day_high_after_entry = subsequent_data['high'].max()
                
                max_potential_profit = day_high_after_entry - entry_price
                
                # If the market went straight down, max profit could be negative (if High < Entry)
                # But usually High >= Open, and Entry is Close of 1st candle.
                # It's possible the subsequent highs are all lower than entry.
                
                mfe_data.append({
                    'date': date,
                    'entry': entry_price,
                    'max_high': day_high_after_entry,
                    'mfe_points': max_potential_profit,
                    'mfe_percent': (max_potential_profit / entry_price) * 100
                })

    mfe_df = pd.DataFrame(mfe_data)
    
    if mfe_df.empty:
        print("No 'Above -> Above' trades found.")
        return

    print(f"\n--- Deep Dive: Above -> Above (Total Days: {len(mfe_df)}) ---")
    
    # 1. Distribution Statistics
    print("\n[MFE Distribution Stats]")
    print(mfe_df['mfe_points'].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]))
    
    # 2. Target Success Rates
    targets = [20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 150]
    print("\n[Target Success Rates]")
    print(f"{'Target (Pts)':<15} | {'Hit Count':<10} | {'Success Rate (%)':<15}")
    print("-" * 45)
    
    for target in targets:
        hit_count = (mfe_df['mfe_points'] >= target).sum()
        success_rate = (hit_count / len(mfe_df)) * 100
        print(f"{target:<15} | {hit_count:<10} | {success_rate:.2f}%")

    # 3. Net Gain Analysis (Close > Entry)
    # We need to re-fetch close data for this, but let's stick to MFE for now as requested.
    # User asked: "how many times there is a net gain" -> This implies End of Day > Entry?
    # Or "net gain... anytime in the day"? -> That is MFE > 0.
    
    positive_mfe_count = (mfe_df['mfe_points'] > 0).sum()
    print(f"\nDays with ANY positive excursion: {positive_mfe_count} ({positive_mfe_count/len(mfe_df)*100:.2f}%)")

if __name__ == "__main__":
    file_path = r"C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv"
    run_deep_dive(file_path)
