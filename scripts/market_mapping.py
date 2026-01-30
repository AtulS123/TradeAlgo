import pandas as pd
import yfinance as yf
import os
import glob
import argparse
from tqdm import tqdm

# Configuration
INDEX_DIR = r"C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive"
STOCK_DIR = r"C:\Users\atuls\Startup\TradeAlgo\kaggle_data\minute\minute"
OUTPUT_FILE = "master_mapping.csv"

def load_indices(index_dir):
    """Loads all index CSVs into a dictionary of DataFrames."""
    indices = {}
    print("Loading Indices...")
    for filepath in glob.glob(os.path.join(index_dir, "*.csv")):
        filename = os.path.basename(filepath)
        index_name = filename.replace("_minute.csv", "")
        try:
            df = pd.read_csv(filepath)
            # Standardize date column
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                # Ensure timezone naive for alignment
                if df['date'].dt.tz is not None:
                    df['date'] = df['date'].dt.tz_localize(None)
                df.set_index('date', inplace=True)
                indices[index_name] = df['close'] # We only need close price for correlation
            else:
                print(f"Warning: 'date' column not found in {filename}")
        except Exception as e:
            print(f"Error loading {filename}: {e}")
    print(f"Loaded {len(indices)} indices.")
    return indices

def get_market_cap_category(symbol):
    """Fetches market cap and returns category."""
    try:
        # Assuming NSE symbols, append .NS if not present in filename logic
        # The filenames are like '20MICRONS.csv', so symbol is '20MICRONS'
        # yfinance expects '20MICRONS.NS' for NSE
        ticker_symbol = f"{symbol}.NS"
        ticker = yf.Ticker(ticker_symbol)
        market_cap = ticker.info.get('marketCap')

        if market_cap is None:
            return "Unknown"

        # Convert to Billions (INR) - yfinance returns in actual currency units
        # Assuming INR for .NS stocks. 
        # 1 Billion = 1,000,000,000
        mcap_billions = market_cap / 1_000_000_000

        if mcap_billions >= 200:
            return "Large Cap"
        elif 50 <= mcap_billions < 200:
            return "Mid Cap"
        elif 5 <= mcap_billions < 50:
            return "Small Cap"
        else:
            return "Micro Cap" # < 5 Billion
            
    except Exception as e:
        # print(f"Error fetching market cap for {symbol}: {e}")
        return "Error"

def process_stocks(stock_dir, indices, limit=None):
    """Iterates through stocks and calculates correlation."""
    results = []
    stock_files = glob.glob(os.path.join(stock_dir, "*.csv"))
    
    if limit:
        stock_files = stock_files[:limit]
        print(f"Processing limited subset: {limit} stocks")

    print(f"Processing {len(stock_files)} stocks...")

    for filepath in tqdm(stock_files):
        symbol = os.path.basename(filepath).replace(".csv", "")
        
        try:
            df = pd.read_csv(filepath)
            if 'date' not in df.columns:
                print(f"Skipping {symbol}: No 'date' column")
                continue
                
            df['date'] = pd.to_datetime(df['date'])
            # Remove timezone info to match indices (which we made naive)
            if df['date'].dt.tz is not None:
                df['date'] = df['date'].dt.tz_localize(None)
            
            df.set_index('date', inplace=True)
            stock_close = df['close']

            max_corr = -1.0
            best_sector = "Unassigned"

            # Calculate correlation with each index
            for index_name, index_close in indices.items():
                # Align data
                aligned_data = pd.concat([stock_close, index_close], axis=1, join='inner')
                
                # Check for sufficient overlap
                if len(aligned_data) < 100: # Minimum 100 data points overlap
                    continue
                
                corr = aligned_data.iloc[:, 0].corr(aligned_data.iloc[:, 1])
                
                if corr > max_corr:
                    max_corr = corr
                    best_sector = index_name

            # Apply threshold
            if max_corr < 0.4:
                best_sector = "Unassigned"

            # Get Market Cap
            cap_category = get_market_cap_category(symbol)

            results.append({
                "Symbol": symbol,
                "Sector": best_sector,
                "Correlation": round(max_corr, 4) if max_corr != -1.0 else 0.0,
                "Cap_Category": cap_category
            })

        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            results.append({
                "Symbol": symbol,
                "Sector": "Error",
                "Correlation": 0.0,
                "Cap_Category": "Error"
            })

    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description="Market Mapping Script")
    parser.add_argument("--limit", type=int, help="Limit number of stocks to process for testing", default=None)
    args = parser.parse_args()

    indices = load_indices(INDEX_DIR)
    if not indices:
        print("No indices loaded. Exiting.")
        return

    df_results = process_stocks(STOCK_DIR, indices, limit=args.limit)
    
    df_results.to_csv(OUTPUT_FILE, index=False)
    print(f"Mapping completed. Saved to {OUTPUT_FILE}")
    print(df_results.head())

if __name__ == "__main__":
    main()
