import yfinance as yf
import numpy as np
import pandas as pd

def get_levels():
    ticker = yf.Ticker("^NSEI")
    df = ticker.history(period="5d", interval="5m")
    
    # Localize/Remove TZ
    if df.index.tz is not None:
        df.index = df.index.tz_convert('Asia/Kolkata').tz_localize(None)
        
    df['date'] = df.index.date
    
    unique_dates = sorted(df['date'].unique())
    yesterday_date = unique_dates[-2]
    today_date = unique_dates[-1]
    
    yesterday_df = df[df['date'] == yesterday_date]
    
    opens = yesterday_df['Open'].values
    closes = yesterday_df['Close'].values
    all_body_values = np.concatenate([opens, closes])
    
    prev_day_max = np.max(all_body_values)
    prev_day_min = np.min(all_body_values)
    range_height = prev_day_max - prev_day_min
    buffer = range_height * 0.05
    
    resistance = prev_day_max + buffer
    support = prev_day_min - buffer
    midpoint = (prev_day_max + prev_day_min) / 2
    
    print(f"DATE: {today_date}")
    print(f"RESISTANCE: {resistance:.2f}")
    print(f"SUPPORT: {support:.2f}")
    print(f"MIDPOINT: {midpoint:.2f}")
    print(f"BUFFER: {buffer:.2f}")

if __name__ == "__main__":
    get_levels()
