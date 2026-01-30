import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def analyze_nifty_today():
    print("Fetching Nifty 50 data from Yahoo Finance (^NSEI)...")
    
    # Fetch last 5 days of 5m data to ensure we have yesterday and today
    ticker = yf.Ticker("^NSEI")
    df = ticker.history(period="5d", interval="5m")
    
    if df.empty:
        print("Error: No data fetched.")
        return

    # Reset index to get datetime column
    df.reset_index(inplace=True)
    
    # Ensure datetime is timezone-naive or converted properly
    # yfinance usually returns timezone-aware. Let's convert to local or remove tz.
    if df['Datetime'].dt.tz is not None:
        df['Datetime'] = df['Datetime'].dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
        
    df['date'] = df['Datetime'].dt.date
    df['time'] = df['Datetime'].dt.time
    
    # Filter Market Hours (09:15 to 15:30)
    market_start = pd.to_datetime("09:15:00").time()
    market_end = pd.to_datetime("15:30:00").time()
    df = df[(df['time'] >= market_start) & (df['time'] <= market_end)]
    
    # Get unique dates
    unique_dates = sorted(df['date'].unique())
    
    if len(unique_dates) < 2:
        print("Error: Not enough data (need at least Yesterday and Today).")
        print(f"Available dates: {unique_dates}")
        return
        
    today_date = unique_dates[-1]
    yesterday_date = unique_dates[-2]
    
    print(f"Yesterday: {yesterday_date}")
    print(f"Today:     {today_date}")
    
    # --- Analyze Yesterday (PDR) ---
    yesterday_df = df[df['date'] == yesterday_date]
    
    # PDR based on Body (Open/Close)
    # Note: yfinance 5m data might have slight differences from Kite, but good for approximation.
    opens = yesterday_df['Open'].values
    closes = yesterday_df['Close'].values
    all_body_values = np.concatenate([opens, closes])
    
    prev_day_max = np.max(all_body_values)
    prev_day_min = np.min(all_body_values)
    range_height = prev_day_max - prev_day_min
    buffer = range_height * 0.05
    
    resistance = prev_day_max + buffer
    support = prev_day_min - buffer
    
    print(f"\n--- Yesterday's Stats ({yesterday_date}) ---")
    print(f"Max (Body): {prev_day_max:.2f}")
    print(f"Min (Body): {prev_day_min:.2f}")
    print(f"Range:      {range_height:.2f}")
    print(f"Buffer 5%:  {buffer:.2f}")
    print(f"Resistance: {resistance:.2f}")
    print(f"Support:    {support:.2f}")
    
    # --- Analyze Today (Start State) ---
    today_df = df[df['date'] == today_date]
    
    if today_df.empty:
        print("Error: No data for today yet.")
        return
        
    # First 5-min candle
    # yfinance timestamps are start of interval. So 09:15 candle covers 09:15-09:20.
    first_candle = today_df.iloc[0]
    
    fc_time = first_candle['time']
    fc_open = first_candle['Open']
    fc_close = first_candle['Close']
    
    print(f"\n--- Today's First Candle ({today_date} @ {fc_time}) ---")
    print(f"Open:  {fc_open:.2f}")
    print(f"Close: {fc_close:.2f}")
    
    # Classify
    def classify(price, sup, res):
        if price < sup: return 'Below'
        if price > res: return 'Above'
        return 'Inside'
        
    start_open_state = classify(fc_open, support, resistance)
    start_close_state = classify(fc_close, support, resistance)
    composite_start = f"{start_open_state}->{start_close_state}"
    
    print(f"\n>>> RESULT: Today's Bucket is [{composite_start}] <<<")
    
    # Probability Lookup (Hardcoded from previous analysis for quick reference)
    probs = {
        "Above->Above": "68.89% End Above",
        "Above->Inside": "43.21% End Inside",
        "Above->Below": "100% End Below (Rare)",
        "Inside->Above": "58.97% End Above",
        "Inside->Inside": "53.41% End Inside",
        "Inside->Below": "67.83% End Below",
        "Below->Above": "100% End Above (Rare)",
        "Below->Inside": "63.41% End Inside",
        "Below->Below": "72.53% End Below"
    }
    
    prediction = probs.get(composite_start, "Unknown")
    print(f"Historical Probability: {prediction}")

if __name__ == "__main__":
    analyze_nifty_today()
