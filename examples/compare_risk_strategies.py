"""
Clean Risk Management Strategy Comparison
Separation of Concerns:
- Trading Strategy (RSI): Finds ENTRY points
- Risk Management: Determines position size and EXIT points
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
import plotly.graph_objects as go

try:
    from utils.saved_token import ACCESS_TOKEN
except:
    print("❌ No saved token found")
    exit(1)

from core.strategy_evaluator import StrategyEvaluator

KITE_API_KEY = "5f814cggb2e7m8z9"

print("\n" + "="*80)
print("RISK MANAGEMENT STRATEGY COMPARISON")
print("="*80 + "\n")

# ============================================================================
# STEP 1: FETCH DATA
# ============================================================================
print("🔐 Authenticating...")
kite = KiteConnect(api_key=KITE_API_KEY)
kite.set_access_token(ACCESS_TOKEN)

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

# Filter trading hours
df['hour'] = df.index.hour
df['minute'] = df.index.minute
df['time_decimal'] = df['hour'] + df['minute'] / 60
trading_hours_mask = (df['time_decimal'] >= 9.25) & (df['time_decimal'] <= 15.5)
df = df[trading_hours_mask].copy()

print(f"✅ Data ready: {len(df):,} bars\n")

# ============================================================================
# STEP 2: CALCULATE INDICATORS (for trading strategy)
# ============================================================================
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

# ============================================================================
# STEP 3: TRADING STRATEGY - RSI Entry Signals
# ============================================================================
def get_entry_signal(i, df):
    """
    Trading Strategy: RSI
    Returns: 'BUY', 'SELL', or None
    """
    if i < 15:
        return None
    
    current_rsi = df['rsi'].iloc[i]
    prev_rsi = df['rsi'].iloc[i-1]
    
    # BUY when RSI crosses below 30 (oversold)
    if prev_rsi >= 30 and current_rsi < 30:
        return 'BUY'
    
    # SELL when RSI crosses above 70 (overbought)
    if prev_rsi <= 70 and current_rsi > 70:
        return 'SELL'
    
    return None

# ============================================================================
# STEP 4: RISK MANAGEMENT STRATEGIES
# ============================================================================
class RiskManager:
    """Base class for risk management"""
    
    def __init__(self, capital):
        self.capital = capital
    
    def calculate_position(self, price, signal):
        """
        Calculate position size and exit levels
        Returns: (quantity, stop_loss, take_profit)
        """
        raise NotImplementedError
    
    def update_exits(self, current_price, entry_price, current_stop, current_target):
        """
        Update stop loss and take profit (for trailing stops, etc.)
        Returns: (new_stop, new_target)
        """
        return current_stop, current_target

class NoRiskManagement(RiskManager):
    """No risk management - fixed position size"""
    
    def calculate_position(self, price, signal):
        quantity = int(20000 / price)  # Fixed ₹20k position
        return quantity, None, None

class FixedPercentageRisk(RiskManager):
    """Fixed percentage risk per trade"""
    
    def __init__(self, capital, risk_pct=2.0):
        super().__init__(capital)
        self.risk_pct = risk_pct
    
    def calculate_position(self, price, signal):
        stop_loss = price * 0.98  # 2% stop
        risk_per_share = price - stop_loss
        max_risk = self.capital * (self.risk_pct / 100)
        quantity = int(max_risk / risk_per_share)
        quantity = max(quantity, int(5000 / price))  # Minimum
        take_profit = price + (2 * risk_per_share)  # 2:1 RR
        return quantity, stop_loss, take_profit

class TrailingStop(RiskManager):
    """Trailing stop that follows price"""
    
    def __init__(self, capital, trail_pct=3.0):
        super().__init__(capital)
        self.trail_pct = trail_pct
    
    def calculate_position(self, price, signal):
        stop_loss = price * (1 - self.trail_pct / 100)
        risk_per_share = price - stop_loss
        max_risk = self.capital * 0.02
        quantity = int(max_risk / risk_per_share)
        quantity = max(quantity, int(5000 / price))
        take_profit = price * 1.06  # 6% target
        return quantity, stop_loss, take_profit
    
    def update_exits(self, current_price, entry_price, current_stop, current_target):
        """Move stop up as price rises"""
        new_stop = current_price * (1 - self.trail_pct / 100)
        # Only move stop up, never down
        new_stop = max(new_stop, current_stop) if current_stop else new_stop
        return new_stop, current_target

class PercentageOfEquity(RiskManager):
    """Position size as percentage of current equity"""
    
    def __init__(self, capital, equity_pct=20.0):
        super().__init__(capital)
        self.equity_pct = equity_pct
    
    def calculate_position(self, price, signal):
        position_value = self.capital * (self.equity_pct / 100)
        quantity = int(position_value / price)
        stop_loss = price * 0.98  # 2% stop
        take_profit = price * 1.04  # 4% target
        return quantity, stop_loss, take_profit

# ============================================================================
# STEP 5: RUN BACKTESTS
# ============================================================================
risk_strategies = {
    'No Risk Management': NoRiskManagement,
    'Fixed 2% Risk': lambda cap: FixedPercentageRisk(cap, 2.0),
    'Trailing Stop (3%)': lambda cap: TrailingStop(cap, 3.0),
    'Percentage of Equity (20%)': lambda cap: PercentageOfEquity(cap, 20.0),
}

results = {}

print("🚀 Running backtests...\n")

for strategy_name, RiskClass in risk_strategies.items():
    print(f"Testing: {strategy_name}...")
    
    initial_capital = 100000
    capital = initial_capital
    position = 0
    entry_price = 0
    trades = []
    equity_curve = [initial_capital] * 15  # Initialize
    
    # Create risk manager
    risk_mgr = RiskClass(capital)
    
    # Backtest loop
    for i in range(15, len(df)):
        price = df['close'].iloc[i]
        timestamp = df.index[i]
        
        # Update risk manager's capital
        risk_mgr.capital = capital
        
        # Get trading signal
        signal = get_entry_signal(i, df)
        
        # ENTRY: Buy signal and no position
        if signal == 'BUY' and position == 0:
            quantity, stop_loss, take_profit = risk_mgr.calculate_position(price, signal)
            
            cost = quantity * price * 1.001
            if capital >= cost and quantity > 0:
                position = quantity
                entry_price = price
                capital -= cost
                
                trades.append({
                    'entry_time': timestamp,
                    'entry_price': price,
                    'quantity': quantity,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'exit_time': None,
                    'exit_price': None,
                    'exit_reason': None,
                    'pnl': None
                })
        
        # UPDATE EXITS: Trailing stops, etc.
        if position > 0 and trades and trades[-1]['exit_time'] is None:
            current_stop = trades[-1]['stop_loss']
            current_target = trades[-1]['take_profit']
            new_stop, new_target = risk_mgr.update_exits(price, entry_price, current_stop, current_target)
            trades[-1]['stop_loss'] = new_stop
            trades[-1]['take_profit'] = new_target
        
        # CHECK EXITS: Stop loss or take profit
        if position > 0 and trades and trades[-1]['exit_time'] is None:
            stop_loss = trades[-1]['stop_loss']
            take_profit = trades[-1]['take_profit']
            
            hit_stop = stop_loss and price <= stop_loss
            hit_target = take_profit and price >= take_profit
            
            if hit_stop or hit_target:
                proceeds = position * price * 0.999
                pnl = proceeds - (position * entry_price * 1.001)
                capital += proceeds
                
                trades[-1].update({
                    'exit_time': timestamp,
                    'exit_price': price,
                    'exit_reason': 'Stop Loss' if hit_stop else 'Take Profit',
                    'pnl': pnl
                })
                
                position = 0
                entry_price = 0
        
        # EXIT: Sell signal (strategy-based exit)
        if signal == 'SELL' and position > 0:
            proceeds = position * price * 0.999
            pnl = proceeds - (position * entry_price * 1.001)
            capital += proceeds
            
            if trades and trades[-1]['exit_time'] is None:
                trades[-1].update({
                    'exit_time': timestamp,
                    'exit_price': price,
                    'exit_reason': 'RSI Signal',
                    'pnl': pnl
                })
            
            position = 0
            entry_price = 0
        
        # Track equity
        portfolio_value = capital + (position * price if position > 0 else 0)
        equity_curve.append(portfolio_value)
    
    # Close any open position
    if position > 0:
        final_price = df['close'].iloc[-1]
        proceeds = position * final_price * 0.999
        pnl = proceeds - (position * entry_price * 1.001)
        capital += proceeds
        
        if trades and trades[-1]['exit_time'] is None:
            trades[-1].update({
                'exit_time': df.index[-1],
                'exit_price': final_price,
                'exit_reason': 'End of Period',
                'pnl': pnl
            })
    
    # Evaluate
    evaluator = StrategyEvaluator()
    completed_trades = [t for t in trades if t['exit_time'] is not None]
    score = evaluator.evaluate(equity_curve, completed_trades, initial_capital, 30)
    
    total_capital_return = ((capital - initial_capital) / initial_capital) * 100
    
    results[strategy_name] = {
        'score': score,
        'equity_curve': equity_curve,
        'trades': completed_trades,
        'final_value': capital,
        'total_capital_return': total_capital_return
    }
    
    print(f"  ✅ Score: {score.overall_score:.1f}/100 ({score.rating})")
    print(f"     Return (Deployed): {score.total_return:.2f}% | Return (Total): {total_capital_return:.2f}%")
    print(f"     Trades: {len(completed_trades)}")

print("\n" + "="*80)
print("CREATING DASHBOARD...")
print("="*80 + "\n")

# Save detailed data for each strategy
import json
os.makedirs('backtest_results/strategy_details', exist_ok=True)

# Convert data to JSON-serializable format
json_results = {}
for name, result in results.items():
    json_results[name] = {
        'score': {
            'overall_score': result['score'].overall_score,
            'total_return': result['score'].total_return,
            'sharpe_ratio': result['score'].sharpe_ratio,
            'sortino_ratio': result['score'].sortino_ratio,
            'max_drawdown': result['score'].max_drawdown,
            'win_rate': result['score'].win_rate,
            'profit_factor': result['score'].profit_factor,
            'avg_win': result['score'].avg_win,
            'avg_loss': result['score'].avg_loss,
            'rating': result['score'].rating
        },
        'trades': [
            {
                'entry_time': t['entry_time'].isoformat(),
                'entry_price': t['entry_price'],
                'quantity': t['quantity'],
                'exit_time': t['exit_time'].isoformat(),
                'exit_price': t['exit_price'],
                'exit_reason': t['exit_reason'],
                'pnl': t['pnl']
            } for t in result['trades']
        ],
        'equity_curve': result['equity_curve']
    }

detailed_data = {
    'df_close': df['close'].tolist(),
    'df_rsi': df['rsi'].tolist(),
    'df_index': [str(idx) for idx in df.index],
    'results': json_results,
    'initial_capital': initial_capital
}

with open('backtest_results/strategy_details/strategy_data.json', 'w') as f:
    json.dump(detailed_data, f)

print("✅ Saved detailed strategy data")

# Create HTML dashboard (same as before)
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Risk Management Strategy Comparison - TradeAlgo</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; min-height: 100vh; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 40px; text-align: center; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; font-weight: 700; }}
        .header p {{ font-size: 1.1em; opacity: 0.9; }}
        .content {{ padding: 40px; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .summary-card {{ background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); transition: transform 0.3s ease; }}
        .summary-card:hover {{ transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }}
        .summary-card h3 {{ font-size: 0.9em; color: #666; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px; }}
        .summary-card .value {{ font-size: 2em; font-weight: 700; color: #1e3c72; }}
        .comparison-table {{ width: 100%; border-collapse: collapse; margin: 30px 0; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .comparison-table thead {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
        .comparison-table th {{ padding: 20px; text-align: left; font-weight: 600; font-size: 0.95em; }}
        .comparison-table td {{ padding: 18px 20px; border-bottom: 1px solid #f0f0f0; }}
        .comparison-table tbody tr:hover {{ background: #f8f9fa; }}
        .rating-badge {{ display: inline-block; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 0.9em; }}
        .rating-S {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; }}
        .rating-A {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; }}
        .rating-B {{ background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: white; }}
        .rating-C {{ background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white; }}
        .rating-D {{ background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); color: #333; }}
        .rating-F {{ background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); color: #333; }}
        .score-bar {{ height: 8px; background: #e0e0e0; border-radius: 4px; overflow: hidden; margin-top: 8px; }}
        .score-fill {{ height: 100%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); transition: width 0.5s ease; }}
        .chart-container {{ margin: 30px 0; background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .positive {{ color: #10b981; font-weight: 600; }}
        .negative {{ color: #ef4444; font-weight: 600; }}
        .footer {{ text-align: center; padding: 30px; background: #f8f9fa; color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Risk Management Strategy Comparison</h1>
            <p>RSI Strategy on RELIANCE | {start_date.date()} to {end_date.date()}</p>
        </div>
        <div class="content">
            <div class="summary-grid">
                <div class="summary-card"><h3>Strategies Tested</h3><div class="value">{len(results)}</div></div>
                <div class="summary-card"><h3>Best Score</h3><div class="value">{max(r['score'].overall_score for r in results.values()):.1f}/100</div></div>
                <div class="summary-card"><h3>Best Return</h3><div class="value">{max(r['score'].total_return for r in results.values()):.2f}%</div></div>
                <div class="summary-card"><h3>Total Trades</h3><div class="value">{sum(len(r['trades']) for r in results.values())}</div></div>
            </div>
            <h2 style="margin: 40px 0 20px 0; color: #1e3c72;">📊 Strategy Comparison</h2>
            <table class="comparison-table">
                <thead>
                    <tr><th>Strategy</th><th>Score</th><th>Rating</th><th>Return</th><th>Sharpe</th><th>Max DD</th><th>Win Rate</th><th>Trades</th></tr>
                </thead>
                <tbody>
"""

for name, result in sorted(results.items(), key=lambda x: x[1]['score'].overall_score, reverse=True):
    score = result['score']
    return_class = 'positive' if score.total_return > 0 else 'negative'
    detail_filename = name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('%', 'pct')
    html_content += f"""
                    <tr>
                        <td><strong><a href="strategy_details/{detail_filename}.html" style="color: #1e3c72; text-decoration: none;">{name} →</a></strong></td>
                        <td><strong>{score.overall_score:.1f}</strong>/100<div class="score-bar"><div class="score-fill" style="width: {score.overall_score}%"></div></div></td>
                        <td><span class="rating-badge rating-{score.rating}">{score.rating}</span></td>
                        <td class="{return_class}">{score.total_return:+.2f}%</td>
                        <td>{score.sharpe_ratio:.2f}</td>
                        <td>{score.max_drawdown:.2f}%</td>
                        <td>{score.win_rate:.1f}%</td>
                        <td>{len(result['trades'])}</td>
                    </tr>
"""

html_content += """
                </tbody>
            </table>
            <div class="chart-container"><div id="equityChart"></div></div>
            <div class="chart-container"><div id="scoreChart"></div></div>
        </div>
        <div class="footer"><p>TradeAlgo Platform | Generated on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p></div>
    </div>
    <script>
        var equityData = """ + str([{'x': list(range(len(r['equity_curve']))), 'y': r['equity_curve'], 'name': n, 'type': 'scatter', 'mode': 'lines', 'line': {'width': 2}} for n, r in results.items()]).replace("'", '"') + """;
        Plotly.newPlot('equityChart', equityData, {title: 'Portfolio Equity Curves', xaxis: {title: 'Time Steps'}, yaxis: {title: 'Portfolio Value (₹)'}, hovermode: 'x unified', height: 500});
        
        var scoreData = [{x: """ + str(list(results.keys())) + """, y: """ + str([r['score'].overall_score for r in results.values()]) + """, type: 'bar', marker: {color: """ + str([r['score'].overall_score for r in results.values()]) + """, colorscale: 'Viridis'}, text: """ + str([f"{r['score'].overall_score:.1f}" for r in results.values()]) + """, textposition: 'outside'}];
        Plotly.newPlot('scoreChart', scoreData, {title: 'Overall Strategy Scores', xaxis: {title: 'Risk Management Strategy'}, yaxis: {title: 'Score (0-100)', range: [0, 110]}, height: 400});
    </script>
</body>
</html>
"""

output_file = "backtest_results/risk_strategy_comparison.html"
os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✅ Dashboard created: {output_file}")
print(f"📊 Opening in browser...\n")

import webbrowser
webbrowser.open(f'file://{os.path.abspath(output_file)}')

print("="*80)
print("✅ COMPLETE!")
print("="*80 + "\n")
