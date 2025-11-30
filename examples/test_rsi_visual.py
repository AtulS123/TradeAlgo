"""
RSI backtest with interactive visualizations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Load saved token
try:
    from utils.saved_token import ACCESS_TOKEN
except:
    print("❌ No saved token found")
    exit(1)

KITE_API_KEY = "5f814cggb2e7m8z9"

print("\n" + "="*70)
print("RSI STRATEGY BACKTEST - RELIANCE (With Visualizations)")
print("="*70 + "\n")

# Authenticate
print("🔐 Using saved access token...")
kite = KiteConnect(api_key=KITE_API_KEY)
kite.set_access_token(ACCESS_TOKEN)
print("✅ Authenticated!\n")

# Fetch data
print("📥 Fetching RELIANCE data from Kite API...")
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

instruments = kite.instruments("NSE")
reliance = next((inst for inst in instruments if inst['tradingsymbol'] == 'RELIANCE'), None)

data = kite.historical_data(
    instrument_token=reliance['instrument_token'],
    from_date=start_date,
    to_date=end_date,
    interval="5minute"
)

df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)

print(f"✅ Fetched {len(df):,} bars\n")

# Calculate RSI
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

df['rsi'] = calculate_rsi(df['close'])

# Backtest
print("🚀 Running backtest...")
capital = 100000
position = 0
trades = []
equity_curve = []

for i in range(15, len(df)):
    current_rsi = df['rsi'].iloc[i]
    prev_rsi = df['rsi'].iloc[i-1]
    price = df['close'].iloc[i]
    timestamp = df.index[i]
    
    if prev_rsi >= 30 and current_rsi < 30 and position == 0:
        quantity = int(20000 / price)
        cost = quantity * price * 1.001
        
        if capital >= cost:
            position = quantity
            capital -= cost
            trades.append({
                'time': timestamp,
                'action': 'BUY',
                'price': price,
                'quantity': quantity,
                'rsi': current_rsi
            })
    
    elif prev_rsi <= 70 and current_rsi > 70 and position > 0:
        proceeds = position * price * 0.999
        capital += proceeds
        trades.append({
            'time': timestamp,
            'action': 'SELL',
            'price': price,
            'quantity': position,
            'rsi': current_rsi
        })
        position = 0
    
    portfolio_value = capital + (position * price if position > 0 else 0)
    equity_curve.append({'time': timestamp, 'value': portfolio_value})

final_value = capital + (position * df['close'].iloc[-1] if position > 0 else 0)

# Print results
print("\n" + "="*70)
print("RESULTS")
print("="*70)
print(f"\n💰 Performance:")
print(f"   Initial Capital:  ₹{100000:,.2f}")
print(f"   Final Value:      ₹{final_value:,.2f}")
print(f"   Total Return:     {((final_value - 100000) / 100000 * 100):.2f}%")
print(f"\n📈 Trades: {len(trades)}")
print("="*70 + "\n")

# Create visualizations
print("📊 Creating interactive charts...\n")

# Create subplots
fig = make_subplots(
    rows=4, cols=1,
    subplot_titles=('RELIANCE Price with Buy/Sell Signals', 'RSI Indicator', 
                    'Portfolio Equity Curve', 'Trade Distribution'),
    vertical_spacing=0.08,
    row_heights=[0.3, 0.2, 0.3, 0.2]
)

# 1. Price chart with signals
fig.add_trace(
    go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='RELIANCE'
    ),
    row=1, col=1
)

# Add buy signals
buy_trades = [t for t in trades if t['action'] == 'BUY']
if buy_trades:
    fig.add_trace(
        go.Scatter(
            x=[t['time'] for t in buy_trades],
            y=[t['price'] for t in buy_trades],
            mode='markers',
            marker=dict(symbol='triangle-up', size=15, color='green'),
            name='Buy Signal'
        ),
        row=1, col=1
    )

# Add sell signals
sell_trades = [t for t in trades if t['action'] == 'SELL']
if sell_trades:
    fig.add_trace(
        go.Scatter(
            x=[t['time'] for t in sell_trades],
            y=[t['price'] for t in sell_trades],
            mode='markers',
            marker=dict(symbol='triangle-down', size=15, color='red'),
            name='Sell Signal'
        ),
        row=1, col=1
    )

# 2. RSI
fig.add_trace(
    go.Scatter(x=df.index, y=df['rsi'], name='RSI', line=dict(color='purple')),
    row=2, col=1
)
fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

# 3. Equity curve
equity_df = pd.DataFrame(equity_curve)
fig.add_trace(
    go.Scatter(
        x=equity_df['time'], 
        y=equity_df['value'],
        name='Portfolio Value',
        fill='tozeroy',
        line=dict(color='blue')
    ),
    row=3, col=1
)
fig.add_hline(y=100000, line_dash="dash", line_color="gray", row=3, col=1)

# 4. Trade distribution
if trades:
    trade_times = [t['time'] for t in trades]
    trade_actions = [1 if t['action'] == 'BUY' else -1 for t in trades]
    
    fig.add_trace(
        go.Bar(
            x=trade_times,
            y=trade_actions,
            name='Trades',
            marker=dict(color=['green' if a == 1 else 'red' for a in trade_actions])
        ),
        row=4, col=1
    )

# Update layout
fig.update_layout(
    title=f"RSI Strategy Backtest - RELIANCE (Real Data)<br>Return: {((final_value - 100000) / 100000 * 100):.2f}%",
    height=1200,
    showlegend=True,
    xaxis_rangeslider_visible=False
)

fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
fig.update_yaxes(title_text="RSI", row=2, col=1)
fig.update_yaxes(title_text="Portfolio Value (₹)", row=3, col=1)
fig.update_yaxes(title_text="Action", row=4, col=1)

# Save chart
output_file = "backtest_results/rsi_reliance_chart.html"
fig.write_html(output_file)

print(f"✅ Interactive chart saved to: {output_file}")
print(f"\n📊 Opening chart in browser...\n")

# Open in browser
import webbrowser
webbrowser.open(f'file://{os.path.abspath(output_file)}')

print("="*70)
print("✅ Backtest complete with visualizations!")
print("="*70 + "\n")
