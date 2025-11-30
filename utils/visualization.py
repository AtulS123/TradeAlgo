"""
Visualization utilities for charts and plots
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Optional
# import matplotlib.pyplot as plt  # Commented for demo
# import seaborn as sns  # Commented for demo


class BacktestVisualizer:
    """
    Create visualizations for backtest results
    """
    
    def __init__(self, equity_curve: List[float], trades: List[Dict], initial_capital: float):
        """
        Initialize visualizer
        
        Args:
            equity_curve: Portfolio value over time
            trades: List of trades
            initial_capital: Initial capital
        """
        self.equity_curve = pd.Series(equity_curve)
        self.trades = pd.DataFrame(trades) if trades else pd.DataFrame()
        self.initial_capital = initial_capital
    
    def plot_equity_curve(self, title: str = "Equity Curve") -> go.Figure:
        """
        Plot equity curve with drawdown
        
        Args:
            title: Chart title
            
        Returns:
            Plotly figure
        """
        # Calculate drawdown
        running_max = self.equity_curve.expanding().max()
        drawdown = (self.equity_curve - running_max) / running_max * 100
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=('Portfolio Value', 'Drawdown %'),
            row_heights=[0.7, 0.3]
        )
        
        # Equity curve
        fig.add_trace(
            go.Scatter(
                y=self.equity_curve,
                mode='lines',
                name='Portfolio Value',
                line=dict(color='#2E86AB', width=2),
                fill='tozeroy',
                fillcolor='rgba(46, 134, 171, 0.1)'
            ),
            row=1, col=1
        )
        
        # Initial capital line
        fig.add_hline(
            y=self.initial_capital,
            line_dash="dash",
            line_color="gray",
            annotation_text="Initial Capital",
            row=1, col=1
        )
        
        # Drawdown
        fig.add_trace(
            go.Scatter(
                y=drawdown,
                mode='lines',
                name='Drawdown',
                line=dict(color='#A23B72', width=2),
                fill='tozeroy',
                fillcolor='rgba(162, 59, 114, 0.2)'
            ),
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            title=title,
            showlegend=True,
            hovermode='x unified',
            template='plotly_white',
            height=600
        )
        
        fig.update_yaxes(title_text="Value (₹)", row=1, col=1)
        fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)
        fig.update_xaxes(title_text="Time", row=2, col=1)
        
        return fig
    
    def plot_returns_distribution(self) -> go.Figure:
        """
        Plot returns distribution histogram
        
        Returns:
            Plotly figure
        """
        returns = self.equity_curve.pct_change().dropna() * 100
        
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=returns,
            nbinsx=50,
            name='Returns',
            marker_color='#2E86AB',
            opacity=0.7
        ))
        
        # Add mean line
        fig.add_vline(
            x=returns.mean(),
            line_dash="dash",
            line_color="red",
            annotation_text=f"Mean: {returns.mean():.2f}%"
        )
        
        fig.update_layout(
            title="Returns Distribution",
            xaxis_title="Return (%)",
            yaxis_title="Frequency",
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    def plot_monthly_returns_heatmap(self, returns: pd.Series) -> go.Figure:
        """
        Plot monthly returns heatmap
        
        Args:
            returns: Returns series with datetime index
            
        Returns:
            Plotly figure
        """
        # This is a simplified version
        # In reality, would need proper datetime index
        
        fig = go.Figure(data=go.Heatmap(
            z=[[0]],  # Placeholder
            colorscale='RdYlGn',
            zmid=0
        ))
        
        fig.update_layout(
            title="Monthly Returns Heatmap",
            template='plotly_white'
        )
        
        return fig
    
    def plot_trade_analysis(self) -> go.Figure:
        """
        Plot trade analysis
        
        Returns:
            Plotly figure
        """
        if self.trades.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No trades to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Trade Distribution by Symbol', 'Trade Value Distribution',
                          'Trades Over Time', 'Cumulative Trades'),
            specs=[[{"type": "bar"}, {"type": "histogram"}],
                   [{"type": "scatter"}, {"type": "scatter"}]]
        )
        
        # Trade distribution by symbol
        symbol_counts = self.trades['symbol'].value_counts()
        fig.add_trace(
            go.Bar(x=symbol_counts.index, y=symbol_counts.values, name='Trades'),
            row=1, col=1
        )
        
        # Trade value distribution
        fig.add_trace(
            go.Histogram(x=self.trades['value'], nbinsx=30, name='Value'),
            row=1, col=2
        )
        
        # Trades over time
        if 'timestamp' in self.trades.columns:
            fig.add_trace(
                go.Scatter(x=self.trades['timestamp'], y=self.trades['value'],
                          mode='markers', name='Trades'),
                row=2, col=1
            )
            
            # Cumulative trades
            cumulative = pd.Series(range(1, len(self.trades) + 1))
            fig.add_trace(
                go.Scatter(x=self.trades['timestamp'], y=cumulative,
                          mode='lines', name='Cumulative'),
                row=2, col=2
            )
        
        fig.update_layout(
            title="Trade Analysis",
            showlegend=False,
            template='plotly_white',
            height=800
        )
        
        return fig
    
    def plot_price_with_signals(
        self,
        price_data: pd.DataFrame,
        symbol: str,
        buy_signals: Optional[pd.Series] = None,
        sell_signals: Optional[pd.Series] = None
    ) -> go.Figure:
        """
        Plot price chart with buy/sell signals
        
        Args:
            price_data: OHLCV DataFrame
            symbol: Symbol name
            buy_signals: Boolean series for buy signals
            sell_signals: Boolean series for sell signals
            
        Returns:
            Plotly figure
        """
        fig = go.Figure()
        
        # Candlestick chart
        fig.add_trace(go.Candlestick(
            x=price_data.index,
            open=price_data['open'],
            high=price_data['high'],
            low=price_data['low'],
            close=price_data['close'],
            name=symbol
        ))
        
        # Buy signals
        if buy_signals is not None:
            buy_points = price_data[buy_signals]
            fig.add_trace(go.Scatter(
                x=buy_points.index,
                y=buy_points['low'] * 0.98,
                mode='markers',
                name='Buy',
                marker=dict(symbol='triangle-up', size=12, color='green')
            ))
        
        # Sell signals
        if sell_signals is not None:
            sell_points = price_data[sell_signals]
            fig.add_trace(go.Scatter(
                x=sell_points.index,
                y=sell_points['high'] * 1.02,
                mode='markers',
                name='Sell',
                marker=dict(symbol='triangle-down', size=12, color='red')
            ))
        
        fig.update_layout(
            title=f"{symbol} - Price with Signals",
            yaxis_title="Price (₹)",
            xaxis_title="Date",
            template='plotly_white',
            xaxis_rangeslider_visible=False,
            height=600
        )
        
        return fig
    
    def save_all_charts(self, output_dir: str = "backtest_results"):
        """
        Save all charts to files
        
        Args:
            output_dir: Output directory
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Equity curve
        fig = self.plot_equity_curve()
        fig.write_html(f"{output_dir}/equity_curve.html")
        
        # Returns distribution
        fig = self.plot_returns_distribution()
        fig.write_html(f"{output_dir}/returns_distribution.html")
        
        # Trade analysis
        fig = self.plot_trade_analysis()
        fig.write_html(f"{output_dir}/trade_analysis.html")
        
        print(f"Charts saved to {output_dir}/")
