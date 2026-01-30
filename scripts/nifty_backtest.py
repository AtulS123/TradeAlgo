import pandas as pd
import numpy as np
import os

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

    # Parse date and time
    # The csv has 'date' column like '2015-01-09 09:15:00'
    df['datetime'] = pd.to_datetime(df['date'])
    df.set_index('datetime', inplace=True)
    
    # Drop the original date column if it exists, to avoid confusion
    if 'date' in df.columns:
        df.drop(columns=['date'], inplace=True)

    # Resample to 5-minute candles
    # Aggregation rules: Open=first, High=max, Low=min, Close=last, Volume=sum
    ohlc_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }
    
    df_5min = df.resample('5min').agg(ohlc_dict)
    
    # Drop rows with NaN values (which might happen if there are gaps)
    df_5min.dropna(inplace=True)

    # Filter for market hours (09:15 to 15:30)
    # We want to include 09:15 and exclude anything after 15:30.
    # Note: The label for 15:25 candle covers 15:25-15:30. The 15:30 candle covers 15:30-15:35 which is usually post-market or not traded.
    # Let's strictly keep candles where the time part is >= 09:15 and <= 15:25 (start time)
    # Or simply filter by time.
    
    df_5min['time'] = df_5min.index.time
    market_start = pd.to_datetime("09:15:00").time()
    market_end = pd.to_datetime("15:25:00").time() # Last candle starts at 15:25 and ends at 15:30
    
    df_5min = df_5min[(df_5min['time'] >= market_start) & (df_5min['time'] <= market_end)].copy()
    
    # Drop the temporary time column
    df_5min.drop(columns=['time'], inplace=True)
    
    print(f"Data loaded and resampled. Shape: {df_5min.shape}")
    return df_5min

def calculate_daily_stats(df_5min):
    """
    Calculates Previous Day Range (PDR) stats based on candle bodies (Open/Close).
    """
    # Create a column for just the date
    df_5min['date_only'] = df_5min.index.date
    
    daily_stats = []
    
    # Group by date
    grouped = df_5min.groupby('date_only')
    
    for date, group in grouped:
        # Calculate PrevDay_Max and PrevDay_Min using only Open and Close
        # We flatten Open and Close columns to find global max/min for that day's bodies
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
    
    # Calculate previous day values (shift by 1)
    stats_df['prev_day_max'] = stats_df['day_max'].shift(1)
    stats_df['prev_day_min'] = stats_df['day_min'].shift(1)
    
    # Drop the first row as it won't have previous day data
    stats_df.dropna(inplace=True)
    
    # Calculate Range Height and Buffer
    stats_df['range_height'] = stats_df['prev_day_max'] - stats_df['prev_day_min']
    stats_df['buffer'] = stats_df['range_height'] * 0.05
    
    # Calculate Support and Resistance
    stats_df['resistance'] = stats_df['prev_day_max'] + stats_df['buffer']
    stats_df['support'] = stats_df['prev_day_min'] - stats_df['buffer']
    
    return stats_df

def classify_day(open_price, close_price, support, resistance):
    """
    Classifies the start and end of the day based on zones.
    """
    # Classify Start
    if open_price < support:
        start_state = 'Below'
    elif open_price > resistance:
        start_state = 'Above'
    else:
        start_state = 'Inside'
        
    # Classify End
    if close_price < support:
        end_state = 'Below'
    elif close_price > resistance:
        end_state = 'Above'
    else:
        end_state = 'Inside'
        
    return start_state, end_state

def run_backtest(file_path):
    df_5min = load_and_preprocess_data(file_path)
    if df_5min is None:
        return

    daily_stats = calculate_daily_stats(df_5min)
    
    results = []
    trades = []
    
    # Group the 5min data by date again for easy access
    df_grouped = df_5min.groupby('date_only')
    
    print(f"Analyzing {len(daily_stats)} trading days...")
    
    for date, stats in daily_stats.iterrows():
        if date not in df_grouped.groups:
            continue
            
        day_data = df_grouped.get_group(date)
        
        if day_data.empty:
            continue
            
        # Get Opening Candle (First 5-min candle)
        opening_candle = day_data.iloc[0]
        opening_close = opening_candle['close']
        opening_open = opening_candle['open']
        opening_high = opening_candle['high']
        opening_low = opening_candle['low']
        
        # Get Closing Candle (Last 5-min candle)
        closing_candle = day_data.iloc[-1]
        closing_val = closing_candle['close']
        
        support = stats['support']
        resistance = stats['resistance']
        
        # Classify Start based on Opening Candle CLOSE (as per prompt)
        # Also useful to know where it OPENED for context, but prompt emphasized Close of 1st candle.
        start_open_state, _ = classify_day(opening_open, closing_val, support, resistance)
        start_close_state, end_state = classify_day(opening_close, closing_val, support, resistance)
        
        composite_start = f"{start_open_state}->{start_close_state}"
        
        results.append({
            'date': date,
            'start_state': start_close_state, # Keep original for backward compatibility if needed
            'composite_start': composite_start,
            'end_state': end_state
        })
        
        # --- Trade Simulation ---
        entry_price = opening_close # Entry at 09:20 (Close of first candle)
        trade_type = None
        stop_loss = None
        target = None
        
        # Logic based on Close State (Original Strategy)
        if start_close_state == 'Above':
            trade_type = 'LONG'
            stop_loss = opening_low
            risk = entry_price - stop_loss
            if risk > 0:
                target = entry_price + (2 * risk)
            else:
                trade_type = None # Invalid risk
                
        elif start_close_state == 'Below':
            trade_type = 'SHORT'
            stop_loss = opening_high
            risk = stop_loss - entry_price
            if risk > 0:
                target = entry_price - (2 * risk)
            else:
                trade_type = None
        
        # --- Inside Day Mean Reversion Strategy ---
        elif start_close_state == 'Inside':
            # We don't enter at 09:20. We wait for price to hit Support or Resistance.
            # We need to iterate through candles to find the trigger.
            pass # Logic handled inside the loop below
            
        if trade_type in ['LONG', 'SHORT']:
            # Original Breakout Strategy Execution
            exit_price = None
            exit_reason = None
            
            for i in range(1, len(day_data)):
                candle = day_data.iloc[i]
                c_high = candle['high']
                c_low = candle['low']
                
                if trade_type == 'LONG':
                    if c_high >= target:
                        exit_price = target
                        exit_reason = 'TARGET'
                        break
                    elif c_low <= stop_loss:
                        exit_price = stop_loss
                        exit_reason = 'STOP_LOSS'
                        break
                elif trade_type == 'SHORT':
                    if c_low <= target:
                        exit_price = target
                        exit_reason = 'TARGET'
                        break
                    elif c_high >= stop_loss:
                        exit_price = stop_loss
                        exit_reason = 'STOP_LOSS'
                        break
            
            if exit_price is None:
                exit_price = closing_val
                exit_reason = 'EOD'
            
            pnl_points = exit_price - entry_price if trade_type == 'LONG' else entry_price - exit_price
                
            trades.append({
                'date': date,
                'composite_start': composite_start,
                'type': trade_type,
                'entry': entry_price,
                'exit': exit_price,
                'sl': stop_loss,
                'target': target,
                'reason': exit_reason,
                'pnl': pnl_points,
                'strategy': 'Breakout'
            })
            
        elif start_close_state == 'Inside':
            # Mean Reversion Execution
            mr_trade_type = None
            mr_entry = None
            mr_sl = None
            mr_target = None
            mr_exit = None
            mr_reason = None
            
            midpoint = (stats['prev_day_max'] + stats['prev_day_min']) / 2
            
            # Iterate through candles to find entry
            for i in range(1, len(day_data)):
                candle = day_data.iloc[i]
                c_high = candle['high']
                c_low = candle['low']
                c_close = candle['close']
                
                if mr_trade_type is None:
                    # Check for Entry Triggers
                    # Sell at Resistance
                    if c_high >= resistance:
                        mr_trade_type = 'SHORT'
                        mr_entry = resistance
                        mr_sl = resistance + stats['buffer']
                        mr_target = midpoint
                        # Check if this same candle hits SL or Target immediately?
                        # Let's assume we enter at the level.
                        # If High > SL, we might stop out immediately.
                        if c_high >= mr_sl:
                             mr_exit = mr_sl
                             mr_reason = 'STOP_LOSS'
                             break
                        elif c_low <= mr_target:
                             mr_exit = mr_target
                             mr_reason = 'TARGET'
                             break
                             
                    # Buy at Support
                    elif c_low <= support:
                        mr_trade_type = 'LONG'
                        mr_entry = support
                        mr_sl = support - stats['buffer']
                        mr_target = midpoint
                        
                        if c_low <= mr_sl:
                            mr_exit = mr_sl
                            mr_reason = 'STOP_LOSS'
                            break
                        elif c_high >= mr_target:
                            mr_exit = mr_target
                            mr_reason = 'TARGET'
                            break
                
                else:
                    # Manage existing trade
                    if mr_trade_type == 'LONG':
                        if c_high >= mr_target:
                            mr_exit = mr_target
                            mr_reason = 'TARGET'
                            break
                        elif c_low <= mr_sl:
                            mr_exit = mr_sl
                            mr_reason = 'STOP_LOSS'
                            break
                    elif mr_trade_type == 'SHORT':
                        if c_low <= mr_target:
                            mr_exit = mr_target
                            mr_reason = 'TARGET'
                            break
                        elif c_high >= mr_sl:
                            mr_exit = mr_sl
                            mr_reason = 'STOP_LOSS'
                            break
            
            if mr_trade_type:
                if mr_exit is None:
                    mr_exit = closing_val
                    mr_reason = 'EOD'
                
                pnl = mr_exit - mr_entry if mr_trade_type == 'LONG' else mr_entry - mr_exit
                
                trades.append({
                    'date': date,
                    'composite_start': composite_start,
                    'type': mr_trade_type,
                    'entry': mr_entry,
                    'exit': mr_exit,
                    'sl': mr_sl,
                    'target': mr_target,
                    'reason': mr_reason,
                    'pnl': pnl,
                    'strategy': 'MeanReversion'
                })

    results_df = pd.DataFrame(results)
    trades_df = pd.DataFrame(trades)
    
    # --- Output Generation ---
    output_str = ""
    
    # 1. Transition Matrix (Granular)
    transition_counts = results_df.groupby(['composite_start', 'end_state']).size().unstack(fill_value=0)
    transition_probs = transition_counts.div(transition_counts.sum(axis=1), axis=0) * 100
    
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    
    output_str += "\n--- Granular Transition Probability Matrix (%) ---\n"
    output_str += str(transition_probs.round(2)) + "\n"
    
    output_str += "\n--- Detailed Counts (Granular) ---\n"
    output_str += str(transition_counts) + "\n"
    
    # 2. Trade Performance
    if not trades_df.empty:
        total_trades = len(trades_df)
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] <= 0]
        
        win_rate = (len(wins) / total_trades) * 100
        total_pnl_points = trades_df['pnl'].sum()
        lot_size = 50
        total_pnl_inr = total_pnl_points * lot_size
        
        avg_win = wins['pnl'].mean() if not wins.empty else 0
        avg_loss = losses['pnl'].mean() if not losses.empty else 0
        
        output_str += "\n--- Strategy Performance (1 Lot Nifty) ---\n"
        output_str += f"Total Trades: {total_trades}\n"
        output_str += f"Win Rate: {win_rate:.2f}%\n"
        output_str += f"Total PnL (Points): {total_pnl_points:.2f}\n"
        output_str += f"Total PnL (INR): {total_pnl_inr:,.2f}\n"
        output_str += f"Avg Win (Pts): {avg_win:.2f}\n"
        output_str += f"Avg Loss (Pts): {avg_loss:.2f}\n"
        
        # Breakdown by Strategy
        output_str += "\n--- Performance by Strategy ---\n"
        strat_stats = trades_df.groupby('strategy')['pnl'].agg(['count', 'sum', 'mean'])
        strat_stats['win_rate'] = trades_df.groupby('strategy')['pnl'].apply(lambda x: (x > 0).mean() * 100)
        output_str += str(strat_stats.round(2)) + "\n"
        
        # Breakdown by Composite Start (All Trades)
        output_str += "\n--- Performance by Composite Start State ---\n"
        comp_stats = trades_df.groupby('composite_start')['pnl'].agg(['count', 'sum', 'mean'])
        comp_stats['win_rate'] = trades_df.groupby('composite_start')['pnl'].apply(lambda x: (x > 0).mean() * 100)
        output_str += str(comp_stats.round(2)) + "\n"
        
        # Recent Trades
        output_str += "\n--- Last 10 Trades ---\n"
        output_str += str(trades_df.tail(10)) + "\n"
        
    else:
        output_str += "\nNo trades generated.\n"
    
    output_str += f"\nTotal Days Analyzed: {len(results_df)}\n"
    
    print(output_str)
    
    with open("results.txt", "w") as f:
        f.write(output_str)

if __name__ == "__main__":
    file_path = r"C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv"
    run_backtest(file_path)
