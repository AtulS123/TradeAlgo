"""
Generate and save access token for today
"""

from kiteconnect import KiteConnect
from datetime import datetime
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import config

# Configuration
REQUEST_TOKEN = "YOUR_REQUEST_TOKEN_HERE"  # Paste request token here

def main():
    print("\n" + "="*70)
    print("GENERATING AND SAVING ACCESS TOKEN")
    print("="*70 + "\n")

    try:
        # Initialize Kite
        print("🔐 Generating access token...")
        kite = KiteConnect(api_key=config.kite_api_key)
        
        # Generate session
        data = kite.generate_session(REQUEST_TOKEN, api_secret=config.kite_api_secret)
        access_token = data["access_token"]
        
        print(f"✅ Access token generated!")
        print(f"   Token: {access_token[:30]}...")
        
        # Save token
        token_file = "data_storage/.kite_access_token"
        os.makedirs(os.path.dirname(token_file), exist_ok=True)
        
        with open(token_file, 'w') as f:
            f.write(f"{access_token}|{datetime.now().strftime('%Y-%m-%d')}")
        
        print(f"\n💾 Token saved to: {token_file}")
        print(f"   Valid until: Market close today (~3:30 PM)")
        print(f"   Date: {datetime.now().strftime('%Y-%m-%d')}")
        
        # Also save to a Python file for easy import
        with open("utils/saved_token.py", 'w') as f:
            f.write(f'# Auto-generated on {datetime.now()}\n')
            f.write(f'ACCESS_TOKEN = "{access_token}"\n')
            f.write(f'GENERATED_DATE = "{datetime.now().strftime("%Y-%m-%d")}"\n')
        
        print(f"\n✅ Token also saved to: utils/saved_token.py")
        print("\n" + "="*70)
        print("SUCCESS!")
        print("="*70)
        print("\nYou can now:")
        print("  1. Run unlimited backtests today")
        print("  2. Fetch any data from Kite API")
        print("  3. No more authentication needed until tomorrow!")
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please check your REQUEST_TOKEN and ensure .env has correct credentials.\n")

if __name__ == "__main__":
    main()
