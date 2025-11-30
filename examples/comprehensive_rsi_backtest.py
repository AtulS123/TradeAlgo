"""
Comprehensive RSI backtest with detailed metrics and visualizations
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
print("COMPREHENSIVE RSI BACKTEST - RELIANCE")
print("="*70 + "\n")

# Authenticate
print("🔐 Authenticating...")
kite = KiteConnect(api_key=KITE_API_KEY)
kite.set_access_token(ACCESS_TOKEN)
print("✅ Authenticated!\n")

# Fetch data
print("📥 Fetching RELIANCE data...")
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

print(f"✅ Fetched {len(df):,} bars from {df.index[0].date()} to {df.index[-1].date()}\n")

# Calculate RSI for ALL data
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

# Filter to trading hours only (9:15 AM to 3:30 PM IST)
df['hour'] = df.index.hour
df['minute'] = df.index.minute
df['time_decimal'] = df['hour'] + df['minute'] / 60

# Keep only trading hours (9:15 to 15:30)
trading_hours_mask = (df['time_decimal'] >= 9.25) & (df['time_decimal'] <= 15.5)
df = df[trading_hours_mask].copy()

# Create a sequential index for continuous plotting
df['seq_index'] = range(len(df))

print(f"✅ Filtered to {len(df):,} bars during trading hours (9:15 AM - 3:30 PM)\n")

# Create custom x-axis labels for continuous display
df['x_label'] = df.index.strftime('%m-%d %H:%M')
df['x_pos'] = range(len(df))  # Sequential position for plotting

# Backtest with detailed tracking
print("🚀 Running backtest...\n")

initial_capital = 100000
capital = initial_capital
position = 0
entry_price = 0
trades = []
equity_curve = []
positions_held = []

# Initialize equity curve with starting capital for first 15 bars
for i in range(15):
    equity_curve.append({
        'time': df.index[i],
        'value': initial_capital,
        'position': 0
    })
    positions_held.append({
        'time': df.index[i],
        'position': 0,
        'price': df['close'].iloc[i]
    })

for i in range(15, len(df)):
    current_rsi = df['rsi'].iloc[i]
    prev_rsi = df['rsi'].iloc[i-1]
    price = df['close'].iloc[i]
    timestamp = df.index[i]
    
    # BUY SIGNAL
    if prev_rsi >= 30 and current_rsi < 30 and position == 0:
        quantity = int(20000 / price)
        cost = quantity * price * 1.001  # Include 0.1% costs
        
        if capital >= cost:
            position = quantity
            entry_price = price
            capital -= cost
            
            trades.append({
                'entry_time': timestamp,
                'entry_price': price,
                'quantity': quantity,
                'entry_rsi': current_rsi,
                'action': 'BUY',
                'exit_time': None,
                'exit_price': None,
                'exit_rsi': None,
                'pnl': None,
                'pnl_percent': None
            })
    
    # SELL SIGNAL
    elif prev_rsi <= 70 and current_rsi > 70 and position > 0:
        proceeds = position * price * 0.999  # Include 0.1% costs
        pnl = proceeds - (position * entry_price * 1.001)
        pnl_percent = (pnl / (position * entry_price)) * 100
        
        capital += proceeds
        
        # Update last trade with exit info
        trades[-1].update({
            'exit_time': timestamp,
            'exit_price': price,
            'exit_rsi': current_rsi,
            'pnl': pnl,
            'pnl_percent': pnl_percent
        })
        
        position = 0
        entry_price = 0
    
    # Track portfolio value
    portfolio_value = capital + (position * price if position > 0 else 0)
    equity_curve.append({
        'time': timestamp,
        'value': portfolio_value,
        'position': position
    })
    
    # Track positions
    positions_held.append({
        'time': timestamp,
        'position': position,
        'price': price
    })

# Close any open position at end
if position > 0:
    final_price = df['close'].iloc[-1]
    proceeds = position * final_price * 0.999
    pnl = proceeds - (position * entry_price * 1.001)
    pnl_percent = (pnl / (position * entry_price)) * 100
    
    capital += proceeds
    
    trades[-1].update({
        'exit_time': df.index[-1],
        'exit_price': final_price,
        'exit_rsi': df['rsi'].iloc[-1],
        'pnl': pnl,
        'pnl_percent': pnl_percent
    })

final_value = capital

# Calculate comprehensive metrics
equity_df = pd.DataFrame(equity_curve)
returns = equity_df['value'].pct_change().dropna()

completed_trades = [t for t in trades if t['exit_time'] is not None]
winners = [t for t in completed_trades if t['pnl'] > 0]
losers = [t for t in completed_trades if t['pnl'] <= 0]

total_return = ((final_value - initial_capital) / initial_capital) * 100
max_equity = equity_df['value'].max()
min_equity = equity_df['value'].min()
max_drawdown = ((equity_df['value'].cummax() - equity_df['value']) / equity_df['value'].cummax() * 100).max()

# Print comprehensive summary
print("="*70)
print("BACKTEST SUMMARY")
print("="*70)

print(f"\n📊 PERFORMANCE METRICS")
print(f"   Initial Capital:      ₹{initial_capital:>12,.2f}")
print(f"   Final Value:          ₹{final_value:>12,.2f}")
print(f"   Total Return:         {total_return:>12.2f}%")
print(f"   Max Portfolio Value:  ₹{max_equity:>12,.2f}")
print(f"   Min Portfolio Value:  ₹{min_equity:>12,.2f}")
print(f"   Max Drawdown:         {max_drawdown:>12.2f}%")

print(f"\n📈 TRADE STATISTICS")
print(f"   Total Trades:         {len(completed_trades):>12}")
print(f"   Winning Trades:       {len(winners):>12}")
print(f"   Losing Trades:        {len(losers):>12}")
print(f"   Win Rate:             {(len(winners)/len(completed_trades)*100) if completed_trades else 0:>12.2f}%")

if completed_trades:
    avg_win = np.mean([t['pnl'] for t in winners]) if winners else 0
    avg_loss = np.mean([t['pnl'] for t in losers]) if losers else 0
    print(f"   Average Win:          ₹{avg_win:>12,.2f}")
    print(f"   Average Loss:         ₹{avg_loss:>12,.2f}")
    print(f"   Largest Win:          ₹{max([t['pnl'] for t in completed_trades]):>12,.2f}")
    print(f"   Largest Loss:         ₹{min([t['pnl'] for t in completed_trades]):>12,.2f}")

print(f"\n📋 TRADE DETAILS")
print("-" * 70)
for i, trade in enumerate(completed_trades, 1):
    status = "✅ WIN" if trade['pnl'] > 0 else "❌ LOSS"
    print(f"{i:2}. {status} | Entry: {trade['entry_time'].strftime('%m-%d %H:%M')} @ ₹{trade['entry_price']:,.2f} | "
          f"Exit: {trade['exit_time'].strftime('%m-%d %H:%M')} @ ₹{trade['exit_price']:,.2f} | "
          f"P&L: ₹{trade['pnl']:>8,.2f} ({trade['pnl_percent']:>6.2f}%)")

print("\n" + "="*70 + "\n")

# Create comprehensive visualization
print("📊 Creating detailed charts...\n")

fig = make_subplots(
    rows=5, cols=1,
    subplot_titles=(
        'RELIANCE Price Chart with Buy/Sell Signals',
        'RSI Indicator (Complete)',
        'Portfolio Equity Curve',
        'Position Tracking',
        'Trade P&L Distribution'
    ),
    vertical_spacing=0.06,
    row_heights=[0.25, 0.15, 0.25, 0.15, 0.20]
)

# 1. TradingView-style continuous price chart
# Create color array for line segments
line_colors = ['green' if i == 0 or df['close'].iloc[i] >= df['close'].iloc[i-1] else 'red' 
               for i in range(len(df))]

# Single continuous trace with hover info - using sequential x positions
fig.add_trace(
    go.Scatter(
        x=df['x_pos'],
        y=df['close'],
        name='RELIANCE',
        mode='lines',
        line=dict(color='rgba(0,0,0,0.7)', width=1.5),
        showlegend=True,
        text=df['x_label'],
        hovertemplate='%{text}<br>Price: ₹%{y:.2f}<extra></extra>',
        connectgaps=False
    ),
    row=1, col=1
)

# Overlay with colored markers to show direction
fig.add_trace(
    go.Scatter(
        x=df['x_pos'],
        y=df['close'],
        mode='markers',
        marker=dict(
            size=2,
            color=line_colors,
            line=dict(width=0)
        ),
        showlegend=False,
        hoverinfo='skip'
    ),
    row=1, col=1
)

# Add all buy signals
buy_trades = [t for t in trades if t['action'] == 'BUY']
if buy_trades:
    buy_x_pos = [df[df.index == t['entry_time']]['x_pos'].iloc[0] if t['entry_time'] in df.index else None 
                 for t in buy_trades]
    buy_x_pos = [x for x in buy_x_pos if x is not None]
    buy_prices = [t['entry_price'] for t in buy_trades if t['entry_time'] in df.index]
    buy_rsi = [t['entry_rsi'] for t in buy_trades if t['entry_time'] in df.index]
    
    fig.add_trace(
        go.Scatter(
            x=buy_x_pos,
            y=buy_prices,
            mode='markers',
            marker=dict(symbol='triangle-up', size=12, color='green', line=dict(width=2, color='darkgreen')),
            name='Buy',
            text=[f"RSI: {rsi:.1f}" for rsi in buy_rsi],
            hovertemplate='Buy<br>Price: ₹%{y:.2f}<br>%{text}<extra></extra>'
        ),
        row=1, col=1
    )

# Add all sell signals
if completed_trades:
    sell_x_pos = [df[df.index == t['exit_time']]['x_pos'].iloc[0] if t['exit_time'] in df.index else None 
                  for t in completed_trades]
    sell_x_pos = [x for x in sell_x_pos if x is not None]
    sell_prices = [t['exit_price'] for t in completed_trades if t['exit_time'] in df.index]
    sell_rsi = [t['exit_rsi'] for t in completed_trades if t['exit_time'] in df.index]
    sell_pnl = [t['pnl'] for t in completed_trades if t['exit_time'] in df.index]
    
    fig.add_trace(
        go.Scatter(
            x=sell_x_pos,
            y=sell_prices,
            mode='markers',
            marker=dict(symbol='triangle-down', size=12, color='red', line=dict(width=2, color='darkred')),
            name='Sell',
            text=[f"RSI: {rsi:.1f}<br>P&L: ₹{pnl:.2f}" for rsi, pnl in zip(sell_rsi, sell_pnl)],
            hovertemplate='Sell<br>Price: ₹%{y:.2f}<br>%{text}<extra></extra>'
        ),
        row=1, col=1
    )

# 2. Complete RSI
fig.add_trace(
    go.Scatter(
        x=df['x_pos'],
        y=df['rsi'],
        name='RSI',
        line=dict(color='purple', width=1),
        showlegend=False,
        text=df['x_label'],
        hovertemplate='%{text}<br>RSI: %{y:.1f}<extra></extra>'
    ),
    row=2, col=1
)
fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought", row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold", row=2, col=1)
fig.add_hrect(y0=30, y1=70, fillcolor="gray", opacity=0.1, row=2, col=1)

# 3. Equity curve
fig.add_trace(
    go.Scatter(
        x=equity_df['time'].map(lambda t: df[df.index == t]['x_pos'].iloc[0] if t in df.index else None),
        y=equity_df['value'],
        name='Portfolio Value',
        fill='tozeroy',
        line=dict(color='blue', width=2)
    ),
    row=3, col=1
)
fig.add_hline(y=initial_capital, line_dash="dash", line_color="gray", annotation_text="Initial Capital", row=3, col=1)

# 4. Position tracking
positions_df = pd.DataFrame(positions_held)
positions_df['x_pos'] = positions_df['time'].map(lambda t: df[df.index == t]['x_pos'].iloc[0] if t in df.index else None)
fig.add_trace(
    go.Scatter(
        x=positions_df['x_pos'],
        y=positions_df['position'],
        name='Shares Held',
        fill='tozeroy',
        line=dict(color='orange', width=1)
    ),
    row=4, col=1
)

# 5. Trade P&L
if completed_trades:
    colors = ['green' if t['pnl'] > 0 else 'red' for t in completed_trades]
    fig.add_trace(
        go.Bar(
            x=[f"Trade {i+1}" for i in range(len(completed_trades))],
            y=[t['pnl'] for t in completed_trades],
            name='P&L',
            marker=dict(color=colors),
            text=[f"₹{t['pnl']:.2f}" for t in completed_trades],
            textposition='outside',
            showlegend=False
        ),
        row=5, col=1
    )

# Update layout
fig.update_layout(
    title=f"RSI Strategy - RELIANCE | Return: {total_return:.2f}% | Win Rate: {(len(winners)/len(completed_trades)*100) if completed_trades else 0:.1f}% | Trades: {len(completed_trades)}",
    height=1400,
    showlegend=True,
    hovermode='x unified'
)

fig.update_xaxes(title_text="Date/Time", row=5, col=1)

# Configure x-axis to show custom labels at intervals
tick_interval = max(1, len(df) // 20)  # Show ~20 labels
tickvals = list(range(0, len(df), tick_interval))
ticktext = [df['x_label'].iloc[i] for i in tickvals]

# Apply to all subplots
for row in [1, 2, 3, 4]:
    fig.update_xaxes(
        tickvals=tickvals,
        ticktext=ticktext,
        tickangle=-45,
        row=row, col=1
    )

fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
fig.update_yaxes(title_text="RSI", range=[0, 100], row=2, col=1)
fig.update_yaxes(title_text="Portfolio (₹)", row=3, col=1)
fig.update_yaxes(title_text="Shares", row=4, col=1)
fig.update_yaxes(title_text="P&L (₹)", row=5, col=1)

# Save
output_file = "backtest_results/rsi_reliance_comprehensive.html"
fig.write_html(output_file)

print(f"✅ Comprehensive chart saved to: {output_file}")
print(f"📊 Opening in browser...\n")

import webbrowser
webbrowser.open(f'file://{os.path.abspath(output_file)}')

print("="*70)
print("✅ COMPLETE!")
print("="*70 + "\n")
