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

def calculate_daily_atr(df_5min, period=14):
    """
    Calculates Daily ATR based on 5-min data aggregated to Daily.
    """
    # Aggregate to Daily
    daily_ohlc = df_5min.resample('D').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }).dropna()
    
    daily_ohlc['prev_close'] = daily_ohlc['close'].shift(1)
    
    # TR Calculation
    daily_ohlc['tr1'] = daily_ohlc['high'] - daily_ohlc['low']
    daily_ohlc['tr2'] = abs(daily_ohlc['high'] - daily_ohlc['prev_close'])
    daily_ohlc['tr3'] = abs(daily_ohlc['low'] - daily_ohlc['prev_close'])
    
    daily_ohlc['tr'] = daily_ohlc[['tr1', 'tr2', 'tr3']].max(axis=1)
    
    # ATR Calculation (SMA of TR)
    daily_ohlc['atr'] = daily_ohlc['tr'].rolling(window=period).mean()
    
    return daily_ohlc[['atr']]

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

def run_atr_analysis(file_path):
    df_5min = load_and_preprocess_data(file_path)
    if df_5min is None:
        return

    # 1. Calculate Daily ATR
    daily_atr = calculate_daily_atr(df_5min)
    
    # 2. Calculate Daily Stats (Support/Resistance)
    daily_stats = calculate_daily_stats(df_5min)
    
    # Merge ATR into daily_stats
    # Note: daily_atr index is Datetime, daily_stats index is Date object.
    daily_atr.index = daily_atr.index.date
    daily_stats = daily_stats.join(daily_atr, how='inner')
    
    df_grouped = df_5min.groupby('date_only')
    
    multipliers = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    results = {m: {'hit_count': 0, 'total_trades': 0, 'avg_sl_points': []} for m in multipliers}
    
    print(f"Analyzing {len(daily_stats)} trading days for 'Above -> Above' setup with ATR SL...")
    
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
        atr = stats['atr']
        
        if pd.isna(atr):
            continue
        
        start_open_state, _ = classify_day(opening_open, closing_val, support, resistance)
        start_close_state, _ = classify_day(opening_close, closing_val, support, resistance)
        
        composite_start = f"{start_open_state}->{start_close_state}"
        
        # FILTER: Only "Above -> Above"
        if composite_start == "Above->Above":
            entry_price = opening_close
            
            # Check for SL hit for each multiplier
            for m in multipliers:
                sl_points = m * atr
                stop_loss_price = entry_price - sl_points
                
                results[m]['total_trades'] += 1
                results[m]['avg_sl_points'].append(sl_points)
                
                # Check if Low of any subsequent candle hits SL
                if len(day_data) > 1:
                    subsequent_lows = day_data.iloc[1:]['low']
                    if (subsequent_lows <= stop_loss_price).any():
                        results[m]['hit_count'] += 1

    print(f"\n--- ATR Stop Loss Analysis (Above -> Above) ---")
    print(f"{'Multiplier':<10} | {'Avg SL (Pts)':<15} | {'Hit Rate (%)':<15}")
    print("-" * 45)
    
    for m in multipliers:
        data = results[m]
        total = data['total_trades']
        if total == 0:
            continue
            
        avg_pts = np.mean(data['avg_sl_points'])
        hit_rate = (data['hit_count'] / total) * 100
        
        print(f"{m:<10} | {avg_pts:<15.2f} | {hit_rate:.2f}%")

if __name__ == "__main__":
    file_path = r"C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv"
    run_atr_analysis(file_path)
