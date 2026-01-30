import os
import pandas as pd
from tqdm import tqdm
import glob

class DataMerger:
    def __init__(self, base_dir="data_archive", output_dir="data_storage"):
        self.base_dir = base_dir
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def standardize_columns(self, df):
        """Map columns to standard format."""
        # Normalize columns to uppercase
        df.columns = [c.strip().upper() for c in df.columns]
        
        # Mapping dictionary
        # Handle variations like 'OPEN_INT' vs 'OI', 'CONTRACTS' vs 'VOLUME'
        # Note: 'TIMESTAMP' is standard for Date usually.
        
        column_map = {
            'TIMESTAMP': 'Date',
            'DATE': 'Date', # Sometimes it might be DATE
            'EXPIRY_DT': 'ExpiryDate',
            'OPTION_TYP': 'OptionType',
            'STRIKE_PR': 'StrikePrice',
            'OPEN': 'Open',
            'HIGH': 'High',
            'LOW': 'Low',
            'CLOSE': 'Close',
            'OPEN_INT': 'OI',
            'OI': 'OI',
            'CONTRACTS': 'Volume',
            'VOLUME': 'Volume',
            'INSTRUMENT': 'Instrument',
            'SYMBOL': 'Symbol'
        }
        
        df = df.rename(columns=column_map)
        
        # Ensure we have all required columns
        required_cols = ['Date', 'ExpiryDate', 'OptionType', 'StrikePrice', 'Open', 'High', 'Low', 'Close', 'OI', 'Volume', 'Instrument', 'Symbol']
        
        # Filter for only existing required columns (some might be missing in very old files, but usually these exist)
        available_cols = [c for c in required_cols if c in df.columns]
        
        return df[available_cols]

    def process_year(self, year):
        print(f"Processing data for year {year}...")
        year_path = os.path.join(self.base_dir, str(year))
        if not os.path.exists(year_path):
            print(f"No data found for year {year}")
            return

        all_files = glob.glob(os.path.join(year_path, "**", "*.csv"), recursive=True)
        if not all_files:
            print(f"No CSV files found for year {year}")
            return

        daily_dfs = []
        for file_path in tqdm(all_files, desc=f"Reading {year}"):
            try:
                df = pd.read_csv(file_path)
                
                # Standardize first to get consistent names
                df = self.standardize_columns(df)
                
                # Filter
                if 'Instrument' in df.columns and 'Symbol' in df.columns:
                    mask = (df['Instrument'] == 'OPTIDX') & (df['Symbol'].isin(['NIFTY', 'BANKNIFTY']))
                    filtered_df = df[mask].copy()
                    
                    if not filtered_df.empty:
                        # Convert Date to datetime if needed
                        if 'Date' in filtered_df.columns:
                            filtered_df['Date'] = pd.to_datetime(filtered_df['Date'])
                        
                        daily_dfs.append(filtered_df)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

        if daily_dfs:
            print(f"Merging {len(daily_dfs)} files for {year}...")
            full_df = pd.concat(daily_dfs, ignore_index=True)
            
            # Sort
            full_df = full_df.sort_values(by=['Date', 'Symbol', 'ExpiryDate', 'StrikePrice'])
            
            # Save to Parquet
            output_path = os.path.join(self.output_dir, f"nifty_options_{year}.parquet")
            full_df.to_parquet(output_path, index=False)
            print(f"Saved {output_path}")
        else:
            print(f"No valid data found for {year}")

    def run(self):
        # Find all years in data_archive
        years = [d for d in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, d)) and d.isdigit()]
        years.sort(reverse=True)
        
        for year in years:
            self.process_year(year)

if __name__ == "__main__":
    merger = DataMerger()
    merger.run()
