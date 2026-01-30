import logging
import os
from kiteconnect import KiteConnect

# Setup logging
logging.basicConfig(level=logging.INFO)

# Credentials
API_KEY = "5f814cggb2e7m8z9"
API_SECRET = "l7tc02thzpmeack5ge4xbwl3dboalz4m"
REQUEST_TOKEN = "dVcdjxsTS1K1jrMawCFlhklmQokXVca0"

def main():
    try:
        # Initialize KiteConnect
        kite = KiteConnect(api_key=API_KEY)

        # Generate Session
        print("Generating session...")
        data = kite.generate_session(REQUEST_TOKEN, api_secret=API_SECRET)
        access_token = data["access_token"]
        
        print(f"Access Token: {access_token}")

        # Save access token
        with open("access_token.txt", "w") as f:
            f.write(access_token)
        print("Access token saved to 'access_token.txt'")

        # Test Fetch
        print("Fetching LTP for NSE:NIFTY 50...")
        ltp = kite.ltp("NSE:NIFTY 50")
        
        if "NSE:NIFTY 50" in ltp:
            print(f"Connection Successful! Nifty is at: {ltp['NSE:NIFTY 50']['last_price']}")
        else:
            print("Connection successful but failed to fetch LTP for NSE:NIFTY 50")
            print(f"LTP Response: {ltp}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
