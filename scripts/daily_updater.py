"""
Daily Data Updater - Automatically fetch latest market data
Run this script daily after market close (4:00 PM IST)
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
from utils.logger import setup_logger

# Access token file (will be created after first authentication)
TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_storage", ".kite_access_token")

logger = setup_logger("daily_updater")

def load_access_token():
    """Load saved access token"""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            token_data = f.read().strip().split('|')
            if len(token_data) == 2:
                token, date = token_data
                # Check if token is from today
                if date == datetime.now().strftime('%Y-%m-%d'):
                    return token
    return None


def save_access_token(token):
    """Save access token for today"""
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, 'w') as f:
        f.write(f"{token}|{datetime.now().strftime('%Y-%m-%d')}")


def authenticate():
    """Authenticate with Kite (requires manual login first time each day)"""
    # Try to load existing token
    token = load_access_token()
    if token:
        print("✅ Using saved access token from today")
        kite = KiteConnect(api_key=config.kite_api_key)
        kite.set_access_token(token)
        return kite
    
    # Need new authentication
    print("\n⚠️  No valid token found. Please authenticate:")
    print("1. Run: python scripts/download_kite_data.py")
    print("2. Complete the login process")
    print("3. The token will be saved for today")
    print("\nOr provide request token as command line argument:")
    print("   python scripts/daily_updater.py YOUR_REQUEST_TOKEN")
    
    if len(sys.argv) > 1:
        request_token = sys.argv[1]
        print(f"\n📋 Using request token: {request_token[:20]}...")
        
        kite = KiteConnect(api_key=config.kite_api_key)
        try:
            data = kite.generate_session(request_token, api_secret=config.kite_api_secret)
            access_token = data["access_token"]
            kite.set_access_token(access_token)
            save_access_token(access_token)
            print("✅ Authenticated and token saved!")
            return kite
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return None
    
    return None


def update_data(kite):
    """Download latest data for all symbols"""
    print("\n" + "="*70)
    print("DAILY DATA UPDATE")
    print("="*70 + "\n")
    
    symbols = [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
        "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
        "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "SUNPHARMA"
    ]
    
    # Fetch data for last 2 days (to ensure we don't miss anything)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2)
    
    print(f"📊 Updating data for {len(symbols)} symbols")
    print(f"   Period: {start_date.date()} to {end_date.date()}")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Connect to database
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_storage", "database", "tradealgo.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    successful = 0
    failed = 0
    total_bars = 0
    
    for i, symbol in enumerate(symbols, 1):
        try:
            print(f"[{i}/{len(symbols)}] {symbol}...", end=' ', flush=True)
            
            # Get instrument
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
                new_bars = 0
                for candle in data:
                    try:
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
                        new_bars += 1
                    except:
                        pass  # Skip duplicates
                
                conn.commit()
                total_bars += new_bars
                print(f"✅ {new_bars} new bars")
                successful += 1
            else:
                print(f"⚠️  No data")
                failed += 1
            
            time.sleep(0.35)  # Rate limiting
            
        except Exception as e:
            print(f"❌ {str(e)[:40]}")
            failed += 1
    
    conn.close()
    
    print("\n" + "="*70)
    print("UPDATE COMPLETE")
    print("="*70)
    print(f"\n✅ Updated: {successful}/{len(symbols)} symbols")
    print(f"📊 New bars: {total_bars:,}")
    print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")


def main():
    """Main function"""
    print("\n" + "="*70)
    print("TradeAlgo - Daily Data Updater")
    print("="*70)
    
    # Authenticate
    kite = authenticate()
    if not kite:
        print("\n❌ Authentication required. Exiting...")
        return
    
    # Update data
    update_data(kite)
    
    print("✅ Daily update complete!\n")


if __name__ == "__main__":
    main()
