"""
Save and reuse Kite access token
"""

import os
from datetime import datetime

# The access token generated from your request token earlier
# (This was generated when you provided: i88tTSATUp06fjtbnHF7o0lOASaIbdE4)
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN_HERE"  # We need to regenerate this

# Token storage
TOKEN_FILE = "data_storage/.kite_access_token"

def save_token(access_token):
    """Save access token with today's date"""
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, 'w') as f:
        f.write(f"{access_token}|{datetime.now().strftime('%Y-%m-%d')}")
    print(f"✅ Token saved for today")

def load_token():
    """Load token if it's from today"""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            token, date = f.read().strip().split('|')
            if date == datetime.now().strftime('%Y-%m-%d'):
                print(f"✅ Using saved token from today")
                return token
    return None

# Check if we have a token
token = load_token()
if token:
    print(f"Access token available: {token[:20]}...")
else:
    print("No valid token found. Need to authenticate.")
