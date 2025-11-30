"""
Standalone Kite API Authentication and Data Download
"""

import pandas as pd
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
import sqlite3
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import config

def authenticate_kite():
    """Authenticate with Kite API"""
    print("\n" + "="*70)
    print("KITE CONNECT API AUTHENTICATION")
    print("="*70 + "\n")
    
    api_key = config.kite_api_key
    api_secret = config.kite_api_secret
    
    if not api_key or not api_secret:
        print("❌ Error: KITE_API_KEY or KITE_API_SECRET not found in environment variables.")
        print("Please check your .env file.")
        return None
    
    # Initialize Kite
    kite = KiteConnect(api_key=api_key)
    
    # Get login URL
    login_url = kite.login_url()
    
    print("Step 1: Login to Kite")
    print("-" * 70)
    print(f"\nPlease open this URL in your browser:\n")
    print(f"{login_url}\n")
    print("1. Login with your Zerodha credentials")
    print("2. Authorize the application")
    print("3. You'll be redirected to a URL containing 'request_token=XXXXX'")
    print("\n" + "-" * 70)
    
    # Get request token
    print("\nStep 2: Extract Request Token")
    print("-" * 70)
    print("\nFrom the redirect URL, copy ONLY the token value:")
    print("Example URL: http://127.0.0.1:5000/callback?request_token=ABC123XYZ&action=login")
    print("             ^^^^^^^^^^^^^^^^^^^^^^^^")
    print("Copy only:   ABC123XYZ")
    print()
    request_token = input("Paste the request_token value here: ").strip()
    
    if not request_token:
        print("\nNo token provided. Exiting...")
        return None
    
    # Generate access token
    print("\nStep 3: Generating Access Token...")
    print("-" * 70)
    
    try:
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        kite.set_access_token(access_token)
        
        print(f"\n✅ Authentication successful!")
        print(f"Access Token: {access_token[:20]}...")
        
        return kite
        
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        return None


def download_data(kite):
    """Download historical data"""
    print("\n" + "="*70)
    print("DOWNLOADING HISTORICAL DATA")
    print("="*70 + "\n")
    
    # Symbols to download
    symbols = [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
        "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
        "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "SUNPHARMA"
    ]
    
    # Date range (Kite allows max 60 days for minute data)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    print(f"Symbols: {len(symbols)}")
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Granularity: 1-minute data (for intraday strategies)\n")
    
    # Create database
    os.makedirs("data_storage/database", exist_ok=True)
    conn = sqlite3.connect("data_storage/database/tradealgo.db")
    cursor = conn.cursor()
    
    # Create table
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
    
    # Download data
    successful = 0
    failed = 0
    
    for i, symbol in enumerate(symbols, 1):
        try:
            print(f"[{i}/{len(symbols)}] {symbol}...", end=' ', flush=True)
            
            # Get instruments to find token
            instruments = kite.instruments("NSE")
            instrument = next((inst for inst in instruments if inst['tradingsymbol'] == symbol), None)
            
            if not instrument:
                print(f"❌ Not found")
                failed += 1
                continue
            
            # Fetch historical data (1-minute)
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
                print(f"✅ {len(data)} bars")
                successful += 1
            else:
                print(f"⚠️  No data")
                failed += 1
                
            # Rate limiting
            import time
            time.sleep(0.35)  # ~3 requests per second
            
        except Exception as e:
            print(f"❌ {str(e)[:30]}")
            failed += 1
    
    conn.close()
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\n✅ Downloaded: {successful}/{len(symbols)}")
    print(f"❌ Failed: {failed}/{len(symbols)}")
    print(f"\n💾 Database: data_storage/database/tradealgo.db")
    print("\n✅ Ready for offline backtesting!")
    print("="*70 + "\n")


def main():
    """Main function"""
    print("\n" + "="*70)
    print("TradeAlgo - Kite Data Downloader")
    print("="*70)
    
    # Authenticate
    kite = authenticate_kite()
    
    if not kite:
        print("\n❌ Failed. Exiting...\n")
        return
    
    # Download
    download_data(kite)
    
    print("\n🎉 Done! Run backtests with real data now.\n")


if __name__ == "__main__":
    main()
