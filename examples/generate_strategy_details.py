"""
Generate Detailed Strategy Pages from Saved Data
"""
import json
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pandas as pd

print("\n" + "="*80)
print("GENERATING DETAILED STRATEGY PAGES")
print("="*80 + "\n")

# Load saved data
with open('backtest_results/strategy_details/strategy_data.json', 'r') as f:
    data = json.load(f)

# Reconstruct dataframe
df = pd.DataFrame({
    'close': data['df_close'],
    'rsi': data['df_rsi']
})
df.index = pd.to_datetime(data['df_index'])

results = data['results']
initial_capital = data['initial_capital']

print(f"Loaded data for {len(results)} strategies\n")

for strategy_name, result in results.items():
    print(f"Generating: {strategy_name}...")
    
    score = result['score']
    trades = result['trades']
    equity_curve = result['equity_curve']
    
    # Create chart
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.25, 0.25],
        subplot_titles=('Price & Signals', 'RSI Indicator', 'Equity Curve')
    )
    
    # Price
    fig.add_trace(go.Scatter(x=list(range(len(df))), y=df['close'], name='Price', line=dict(color='#2962FF', width=2)), row=1, col=1)
    
    # Buy signals
    if trades:
        buy_idx = [df.index.get_loc(pd.to_datetime(t['entry_time'])) for t in trades]
        buy_prices = [t['entry_price'] for t in trades]
        fig.add_trace(go.Scatter(x=buy_idx, y=buy_prices, mode='markers', name='Buy', marker=dict(color='#00C853', size=12, symbol='triangle-up')), row=1, col=1)
        
        # Sell signals
        sell_idx = [df.index.get_loc(pd.to_datetime(t['exit_time'])) for t in trades]
        sell_prices = [t['exit_price'] for t in trades]
        fig.add_trace(go.Scatter(x=sell_idx, y=sell_prices, mode='markers', name='Sell', marker=dict(color='#FF1744', size=12, symbol='triangle-down')), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=list(range(len(df))), y=df['rsi'], name='RSI', line=dict(color='#9C27B0', width=2)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)
    
    # Equity
    fig.add_trace(go.Scatter(x=list(range(len(equity_curve))), y=equity_curve, name='Equity', fill='tozeroy', line=dict(color='#00BCD4', width=2)), row=3, col=1)
    
    fig.update_layout(height=900, showlegend=True, hovermode='x unified', template='plotly_white')
    chart_html = fig.to_html(include_plotlyjs='cdn', div_id='mainChart')
    
    # Trade table
    trades_html = ""
    for i, trade in enumerate(trades, 1):
        pnl_class = 'positive' if trade['pnl'] > 0 else 'negative'
        exit_reason_color = {'Stop Loss': '#FF1744', 'Take Profit': '#00E676', 'RSI Signal': '#FFC107', 'End of Period': '#9E9E9E'}.get(trade['exit_reason'], '#9E9E9E')
        
        entry_dt = pd.to_datetime(trade['entry_time'])
        exit_dt = pd.to_datetime(trade['exit_time'])
        
        trades_html += f"""
        <tr>
            <td>{i}</td>
            <td>{entry_dt.strftime('%Y-%m-%d %H:%M')}</td>
            <td>Rs{trade['entry_price']:.2f}</td>
            <td>{trade['quantity']}</td>
            <td>{exit_dt.strftime('%Y-%m-%d %H:%M')}</td>
            <td>Rs{trade['exit_price']:.2f}</td>
            <td><span style="color: {exit_reason_color}; font-weight: 600;">{trade['exit_reason']}</span></td>
            <td class="{pnl_class}">Rs{trade['pnl']:+.2f}</td>
        </tr>
        """
    
    # HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{strategy_name} - Detailed Analysis</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }}
        .container {{ max-width: 1600px; margin: 0 auto; background: white; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }}
        .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 40px; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .back-link {{ display: inline-block; margin-bottom: 20px; color: white; text-decoration: none; padding: 10px 20px; background: rgba(255,255,255,0.2); border-radius: 8px; }}
        .back-link:hover {{ background: rgba(255,255,255,0.3); }}
        .content {{ padding: 40px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .metric-card {{ background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .metric-card h3 {{ font-size: 0.85em; color: #666; margin-bottom: 10px; text-transform: uppercase; }}
        .metric-card .value {{ font-size: 1.8em; font-weight: 700; color: #1e3c72; }}
        .section {{ margin: 40px 0; }}
        .section h2 {{ color: #1e3c72; margin-bottom: 20px; font-size: 1.8em; }}
        .chart-container {{ background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .trades-table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .trades-table thead {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
        .trades-table th {{ padding: 15px; text-align: left; font-weight: 600; }}
        .trades-table td {{ padding: 12px 15px; border-bottom: 1px solid #f0f0f0; }}
        .trades-table tbody tr:hover {{ background: #f8f9fa; }}
        .positive {{ color: #10b981; font-weight: 600; }}
        .negative {{ color: #ef4444; font-weight: 600; }}
        .rating-badge {{ display: inline-block; padding: 8px 20px; border-radius: 25px; font-weight: 700; }}
        .rating-S {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; }}
        .rating-A {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; }}
        .rating-B {{ background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: white; }}
        .rating-C {{ background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white; }}
        .rating-D {{ background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); color: #333; }}
        .rating-F {{ background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); color: #333; }}
        .insight-box {{ background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%); padding: 25px; border-radius: 15px; margin: 20px 0; border-left: 5px solid #e17055; }}
        .insight-box h3 {{ color: #2d3436; margin-bottom: 15px; }}
        .insight-box ul {{ margin-left: 20px; color: #2d3436; }}
        .insight-box li {{ margin: 8px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <a href="../risk_strategy_comparison.html" class="back-link">← Back to Comparison</a>
            <h1>{strategy_name}</h1>
            <p>Detailed Trade Analysis & Performance Metrics</p>
        </div>
        <div class="content">
            <div class="section">
                <h2>Performance Overview</h2>
                <div class="metrics-grid">
                    <div class="metric-card"><h3>Overall Score</h3><div class="value">{score['overall_score']:.1f}/100</div><span class="rating-badge rating-{score['rating']}">{score['rating']}</span></div>
                    <div class="metric-card"><h3>Total Return</h3><div class="value {'positive' if score['total_return'] > 0 else 'negative'}">{score['total_return']:+.2f}%</div></div>
                    <div class="metric-card"><h3>Sharpe Ratio</h3><div class="value">{score['sharpe_ratio']:.2f}</div></div>
                    <div class="metric-card"><h3>Max Drawdown</h3><div class="value">{score['max_drawdown']:.2f}%</div></div>
                    <div class="metric-card"><h3>Win Rate</h3><div class="value">{score['win_rate']:.1f}%</div></div>
                    <div class="metric-card"><h3>Profit Factor</h3><div class="value">{score['profit_factor']:.2f}</div></div>
                    <div class="metric-card"><h3>Total Trades</h3><div class="value">{len(trades)}</div></div>
                    <div class="metric-card"><h3>Avg Win</h3><div class="value positive">Rs{score['avg_win']:.2f}</div></div>
                    <div class="metric-card"><h3>Avg Loss</h3><div class="value negative">Rs{score['avg_loss']:.2f}</div></div>
                </div>
            </div>
            
            <div class="insight-box">
                <h3>Key Insights</h3>
                <ul>
                    <li><strong>Strategy Performance:</strong> {'Strong performer' if score['overall_score'] >= 70 else 'Moderate performer' if score['overall_score'] >= 50 else 'Needs improvement'} with {score['rating']} rating</li>
                    <li><strong>Risk-Adjusted Returns:</strong> Sharpe ratio of {score['sharpe_ratio']:.2f} indicates {'excellent' if score['sharpe_ratio'] >= 2 else 'good' if score['sharpe_ratio'] >= 1 else 'moderate' if score['sharpe_ratio'] >= 0.5 else 'poor'} risk-adjusted performance</li>
                    <li><strong>Trade Consistency:</strong> {score['win_rate']:.1f}% win rate with {len([t for t in trades if t.get('pnl', 0) > 0])} winning trades out of {len(trades)} total</li>
                    <li><strong>Risk Control:</strong> Maximum drawdown of {score['max_drawdown']:.2f}% shows {'excellent' if score['max_drawdown'] < 5 else 'good' if score['max_drawdown'] < 10 else 'moderate' if score['max_drawdown'] < 20 else 'concerning'} risk management</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Price Chart with Signals</h2>
                <div class="chart-container">{chart_html}</div>
            </div>
            
            <div class="section">
                <h2>Trade-by-Trade Breakdown</h2>
                <table class="trades-table">
                    <thead><tr><th>#</th><th>Entry Time</th><th>Entry Price</th><th>Quantity</th><th>Exit Time</th><th>Exit Price</th><th>Exit Reason</th><th>P&L</th></tr></thead>
                    <tbody>{trades_html}</tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    # Save
    filename = strategy_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('%', 'pct')
    filepath = f'backtest_results/strategy_details/{filename}.html'
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"  Saved: {filepath}")

print("\n" + "="*80)
print("ALL DETAILED PAGES GENERATED!")
print("="*80 + "\n")
