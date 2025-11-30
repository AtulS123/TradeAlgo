"""
Download data with provided request token
"""

import pandas as pd
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
import sqlite3
import os
import time
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import config

# Configuration
REQUEST_TOKEN = "YOUR_REQUEST_TOKEN_HERE"  # You still need to paste this manually for this script

def main():
    print("\n" + "="*70)
    print("KITE DATA DOWNLOAD")
    print("="*70 + "\n")

    # Initialize Kite
    print("Authenticating...")
    try:
        kite = KiteConnect(api_key=config.kite_api_key)
        data = kite.generate_session(REQUEST_TOKEN, api_secret=config.kite_api_secret)
        access_token = data["access_token"]
        kite.set_access_token(access_token)
        print(f"✅ Authenticated! Token: {access_token[:20]}...\n")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("Please check your REQUEST_TOKEN and ensure .env has correct credentials.")
        return

    # Symbols to download
    symbols = [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
        "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
        "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "SUNPHARMA"
    ]

    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)

    print(f"📊 Configuration:")
    print(f"   Symbols: {len(symbols)}")
    print(f"   Period: {start_date.date()} to {end_date.date()}")
    print(f"   Granularity: 1-minute data\n")

    # Create database
    os.makedirs("data_storage/database", exist_ok=True)
    conn = sqlite3.connect("data_storage/database/tradealgo.db")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historical_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            datetime TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            UNIQUE(symbol, datetime)
        )
    ''')

    print("📥 Downloading data...\n")

    successful = 0
    failed = 0

    for i, symbol in enumerate(symbols, 1):
        try:
            print(f"[{i}/{len(symbols)}] {symbol}...", end=' ', flush=True)
            
            # Get instrument token
            instruments = kite.instruments("NSE")
            instrument = next((inst for inst in instruments if inst['tradingsymbol'] == symbol), None)
            
            if not instrument:
                print(f"❌ Not found")
                failed += 1
                continue
            
            # Fetch 1-minute data
            data = kite.historical_data(
                instrument_token=instrument['instrument_token'],
                from_date=start_date,
                to_date=end_date,
                interval="minute"
            )
            
            if data:
                # Save to database
                for candle in data:
                    cursor.execute('''
                        INSERT OR REPLACE INTO historical_data 
                        (symbol, datetime, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        symbol,
                        candle['date'].strftime('%Y-%m-%d %H:%M:%S'),
                        candle['open'],
                        candle['high'],
                        candle['low'],
                        candle['close'],
                        candle['volume']
                    ))
                
                conn.commit()
                print(f"✅ {len(data):,} bars")
                successful += 1
            else:
                print(f"⚠️  No data")
                failed += 1
            
            # Rate limiting
            time.sleep(0.35)
            
        except Exception as e:
            print(f"❌ {str(e)[:40]}")
            failed += 1

    conn.close()

    print("\n" + "="*70)
    print("DOWNLOAD COMPLETE")
    print("="*70)
    print(f"\n✅ Downloaded: {successful}/{len(symbols)} symbols")
    print(f"❌ Failed: {failed}/{len(symbols)}")
    print(f"\n💾 Database: data_storage/database/tradealgo.db")
    print("\n🎉 Ready for backtesting with real market data!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
