"""
Data Loader for Research Lab

Handles loading of:
1. Nifty Sector Indices (Macro Data) from Kaggle ZIPs
2. Individual Stock Data (Micro Data) from Kaggle ZIPs
3. Stock-Sector Mapping from master_mapping.csv
"""

import pandas as pd
import numpy as np
import zipfile
import os
from pathlib import Path
from typing import Dict, Optional, List
import io

class DataLoader:
    def __init__(self, base_dir: str = "kaggle_data"):
        self.base_dir = Path(base_dir)
        self.indices_dir = self.base_dir / "archive"
        self.stocks_dir = self.base_dir / "minute"
        self.mapping_file = Path("master_mapping.csv")
        
    def load_mapping(self) -> pd.DataFrame:
        """Load the master mapping file"""
        if not self.mapping_file.exists():
            raise FileNotFoundError(f"Mapping file not found: {self.mapping_file}")
        return pd.read_csv(self.mapping_file)

    def get_stock_sector_map(self) -> Dict[str, str]:
        """Return a dictionary mapping Symbol -> Sector"""
        df = self.load_mapping()
        df.columns = [c.strip() for c in df.columns]
        return dict(zip(df['Symbol'], df['Sector']))

    def get_stock_cap_map(self) -> Dict[str, str]:
        """Return a dictionary mapping Symbol -> Cap_Category"""
        df = self.load_mapping()
        df.columns = [c.strip() for c in df.columns]
        return dict(zip(df['Symbol'], df['Cap_Category']))

    def load_macro_data(self, sector_name: str) -> pd.DataFrame:
        """
        Load Sector Index data from kaggle_data/archive
        """
        # File names are like "NIFTY BANK_minute.csv"
        file_path = self.indices_dir / f"{sector_name}_minute.csv"
        
        if not file_path.exists():
            # Try finding closest match
            print(f"Warning: Exact file {file_path} not found. Searching...")
            for f in self.indices_dir.glob("*_minute.csv"):
                if sector_name in f.name:
                    file_path = f
                    break
            else:
                raise FileNotFoundError(f"Sector data for {sector_name} not found in {self.indices_dir}")

        df = pd.read_csv(file_path)
        return self._clean_data(df)

    def load_stock_data(self, symbol: str, timeframe: str = 'minute') -> pd.DataFrame:
        """
        Load minute data for a specific stock from kaggle_data/minute/minute
        """
        # Files are likely "SYMBOL.csv"
        file_path = self.stocks_dir / f"{symbol}.csv"
        print(f"DEBUG: Attempting to load stock data from: {file_path.absolute()}")
        
        if not file_path.exists():
             # Try one level up just in case
             file_path_up = self.base_dir / "minute" / f"{symbol}.csv"
             if file_path_up.exists():
                 file_path = file_path_up
             else:
                 raise FileNotFoundError(f"Stock data for {symbol} not found in {self.stocks_dir} or parent")

        df = pd.read_csv(file_path)
        df = self._clean_data(df)
        
        # Resample if needed
        if timeframe != 'minute':
            conversion = {'5m': '5T', '15m': '15T', '1h': '1H'}
            rule = conversion.get(timeframe)
            if rule:
                df = df.resample(rule).agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
                
        return df

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names and index"""
        # Standardize columns to lowercase
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Parse Date
        # Check for common date columns
        date_col = None
        for col in ['date', 'datetime', 'timestamp']:
            if col in df.columns:
                date_col = col
                break
        
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])
            df.set_index(date_col, inplace=True)
            df.sort_index(inplace=True)
            
            # Remove +05:30 offset if present to align with vectorbt
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
                
        return df

if __name__ == "__main__":
    # Test
    loader = DataLoader()
    print("Mapping loaded:", len(loader.load_mapping()))
    # print("Zip contents:", loader.inspect_zip_contents("minute.zip"))
