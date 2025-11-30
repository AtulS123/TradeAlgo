"""
Performance metrics calculator
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from utils.logger import logger


class PerformanceMetrics:
    """
    Calculate comprehensive performance metrics for backtesting
    """
    
    def __init__(
        self,
        equity_curve: List[float],
        trades: List[Dict],
        initial_capital: float,
        risk_free_rate: float = 0.06  # 6% risk-free rate (India)
    ):
        """
        Initialize metrics calculator
        
        Args:
            equity_curve: List of portfolio values over time
            trades: List of trade dictionaries
            initial_capital: Initial capital
            risk_free_rate: Risk-free rate for Sharpe/Sortino
        """
        self.equity_curve = pd.Series(equity_curve)
        self.trades = pd.DataFrame(trades) if trades else pd.DataFrame()
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate
        
        # Calculate returns
        self.returns = self.equity_curve.pct_change().dropna()
    
    def calculate_all(self) -> Dict:
        """Calculate all metrics"""
        metrics = {}
        
        # Return metrics
        metrics.update(self._calculate_return_metrics())
        
        # Risk metrics
        metrics.update(self._calculate_risk_metrics())
        
        # Trade statistics
        metrics.update(self._calculate_trade_statistics())
        
        # Drawdown metrics
        metrics.update(self._calculate_drawdown_metrics())
        
        # Advanced metrics
        metrics.update(self._calculate_advanced_metrics())
        
        return metrics
    
    def _calculate_return_metrics(self) -> Dict:
        """Calculate return-based metrics"""
        final_value = self.equity_curve.iloc[-1]
        total_return = ((final_value - self.initial_capital) / self.initial_capital) * 100
        
        # Annualized return (assuming 252 trading days)
        num_periods = len(self.equity_curve)
        years = num_periods / 252
        cagr = ((final_value / self.initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0
        
        return {
            'total_return_percent': total_return,
            'cagr': cagr,
            'final_value': final_value
        }
    
    def _calculate_risk_metrics(self) -> Dict:
        """Calculate risk-based metrics"""
        # Volatility (annualized)
        volatility = self.returns.std() * np.sqrt(252) * 100
        
        # Sharpe Ratio
        excess_returns = self.returns - (self.risk_free_rate / 252)
        sharpe_ratio = (excess_returns.mean() / self.returns.std()) * np.sqrt(252) if self.returns.std() > 0 else 0
        
        # Sortino Ratio (downside deviation)
        downside_returns = self.returns[self.returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
        sortino_ratio = (excess_returns.mean() / downside_std) * np.sqrt(252) if downside_std > 0 else 0
        
        return {
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio
        }
    
    def _calculate_trade_statistics(self) -> Dict:
        """Calculate trade-based statistics"""
        if self.trades.empty:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'expectancy': 0
            }
        
        # Group trades by symbol to calculate P&L
        # For simplicity, assuming each trade is independent
        # In reality, we'd need to match buy/sell pairs
        
        total_trades = len(self.trades)
        
        # Simplified P&L calculation (this is a placeholder)
        # Real implementation would match buy/sell pairs
        winning_trades = 0
        losing_trades = 0
        total_profit = 0
        total_loss = 0
        
        # For now, return basic stats
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'avg_win': total_profit / winning_trades if winning_trades > 0 else 0,
            'avg_loss': total_loss / losing_trades if losing_trades > 0 else 0,
            'profit_factor': abs(total_profit / total_loss) if total_loss != 0 else 0,
            'expectancy': (total_profit - total_loss) / total_trades if total_trades > 0 else 0
        }
    
    def _calculate_drawdown_metrics(self) -> Dict:
        """Calculate drawdown metrics"""
        # Calculate running maximum
        running_max = self.equity_curve.expanding().max()
        
        # Calculate drawdown
        drawdown = (self.equity_curve - running_max) / running_max * 100
        
        # Max drawdown
        max_drawdown = drawdown.min()
        
        # Max drawdown duration
        is_drawdown = drawdown < 0
        drawdown_periods = is_drawdown.astype(int).groupby((is_drawdown != is_drawdown.shift()).cumsum()).sum()
        max_drawdown_duration = drawdown_periods.max() if len(drawdown_periods) > 0 else 0
        
        # Recovery factor
        total_return = ((self.equity_curve.iloc[-1] - self.initial_capital) / self.initial_capital) * 100
        recovery_factor = abs(total_return / max_drawdown) if max_drawdown != 0 else 0
        
        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_duration': max_drawdown_duration,
            'recovery_factor': recovery_factor
        }
    
    def _calculate_advanced_metrics(self) -> Dict:
        """Calculate advanced metrics"""
        # Calmar Ratio (CAGR / Max Drawdown)
        num_periods = len(self.equity_curve)
        years = num_periods / 252
        final_value = self.equity_curve.iloc[-1]
        cagr = ((final_value / self.initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0
        
        running_max = self.equity_curve.expanding().max()
        drawdown = (self.equity_curve - running_max) / running_max * 100
        max_drawdown = abs(drawdown.min())
        
        calmar_ratio = cagr / max_drawdown if max_drawdown > 0 else 0
        
        # Monthly returns (simplified - assumes daily data)
        # In reality, would need actual monthly grouping
        monthly_returns = []
        
        return {
            'calmar_ratio': calmar_ratio,
            'monthly_returns': monthly_returns
        }
    
    def get_equity_curve_df(self) -> pd.DataFrame:
        """Get equity curve as DataFrame"""
        return pd.DataFrame({
            'equity': self.equity_curve,
            'returns': self.returns
        })
    
    def print_summary(self):
        """Print metrics summary"""
        metrics = self.calculate_all()
        
        print("\n" + "="*50)
        print("BACKTEST PERFORMANCE SUMMARY")
        print("="*50)
        
        print(f"\n📊 Returns:")
        print(f"  Total Return: {metrics['total_return_percent']:.2f}%")
        print(f"  CAGR: {metrics['cagr']:.2f}%")
        print(f"  Final Value: ₹{metrics['final_value']:,.2f}")
        
        print(f"\n⚠️  Risk Metrics:")
        print(f"  Volatility: {metrics['volatility']:.2f}%")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"  Sortino Ratio: {metrics['sortino_ratio']:.2f}")
        print(f"  Max Drawdown: {metrics['max_drawdown']:.2f}%")
        
        print(f"\n📈 Trade Statistics:")
        print(f"  Total Trades: {metrics['total_trades']}")
        print(f"  Win Rate: {metrics['win_rate']:.2f}%")
        print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
        
        print(f"\n🎯 Advanced Metrics:")
        print(f"  Calmar Ratio: {metrics['calmar_ratio']:.2f}")
        print(f"  Recovery Factor: {metrics['recovery_factor']:.2f}")
        
        print("="*50 + "\n")
