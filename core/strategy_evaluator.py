"""
Strategy Evaluation & Scoring System
Professional multi-metric evaluation for trading strategies
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class StrategyScore:
    """Complete strategy evaluation score"""
    overall_score: float  # 0-100
    return_score: float
    risk_adjusted_score: float
    consistency_score: float
    drawdown_score: float
    win_rate_score: float
    
    # Detailed metrics
    total_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    total_trades: int
    
    # Rating
    rating: str  # S, A, B, C, D, F


class StrategyEvaluator:
    """
    Comprehensive strategy evaluation system
    Uses multiple metrics to score strategies on 0-100 scale
    """
    
    # Weights for different components (must sum to 1.0)
    WEIGHTS = {
        'return': 0.25,
        'risk_adjusted': 0.30,
        'consistency': 0.20,
        'drawdown': 0.15,
        'win_rate': 0.10
    }
    
    def __init__(self, risk_free_rate: float = 0.06):
        """
        Initialize evaluator
        
        Args:
            risk_free_rate: Annual risk-free rate (default 6% for India)
        """
        self.risk_free_rate = risk_free_rate
        
    def evaluate(
        self,
        equity_curve: List[float],
        trades: List[Dict],
        initial_capital: float,
        days: int = 30
    ) -> StrategyScore:
        """
        Comprehensive strategy evaluation
        
        Args:
            equity_curve: List of portfolio values over time
            trades: List of completed trades
            initial_capital: Starting capital
            days: Number of trading days
            
        Returns:
            StrategyScore with overall score and detailed metrics
        """
        # Calculate all metrics
        metrics = self._calculate_metrics(equity_curve, trades, initial_capital, days)
        
        # Score each component (0-100)
        return_score = self._score_returns(metrics['total_return'])
        risk_adjusted_score = self._score_risk_adjusted(metrics['sharpe_ratio'], metrics['sortino_ratio'])
        consistency_score = self._score_consistency(metrics['win_rate'], metrics['profit_factor'])
        drawdown_score = self._score_drawdown(metrics['max_drawdown'])
        win_rate_score = self._score_win_rate(metrics['win_rate'])
        
        # Calculate weighted overall score
        overall_score = (
            return_score * self.WEIGHTS['return'] +
            risk_adjusted_score * self.WEIGHTS['risk_adjusted'] +
            consistency_score * self.WEIGHTS['consistency'] +
            drawdown_score * self.WEIGHTS['drawdown'] +
            win_rate_score * self.WEIGHTS['win_rate']
        )
        
        # Determine rating
        rating = self._get_rating(overall_score)
        
        return StrategyScore(
            overall_score=overall_score,
            return_score=return_score,
            risk_adjusted_score=risk_adjusted_score,
            consistency_score=consistency_score,
            drawdown_score=drawdown_score,
            win_rate_score=win_rate_score,
            total_return=metrics['total_return'],
            sharpe_ratio=metrics['sharpe_ratio'],
            sortino_ratio=metrics['sortino_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            profit_factor=metrics['profit_factor'],
            avg_win=metrics['avg_win'],
            avg_loss=metrics['avg_loss'],
            total_trades=metrics['total_trades'],
            rating=rating
        )
    
    def _calculate_metrics(self, equity_curve, trades, initial_capital, days):
        """Calculate all performance metrics"""
        equity_series = pd.Series(equity_curve)
        returns = equity_series.pct_change().dropna()
        
        # Total return (on total capital)
        final_value = equity_curve[-1]
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        
        # Calculate deployed capital return (more meaningful)
        if trades:
            # Average capital deployed per trade
            deployed_capitals = []
            for trade in trades:
                if 'quantity' in trade and 'entry_price' in trade:
                    deployed = trade['quantity'] * trade['entry_price']
                    deployed_capitals.append(deployed)
            
            if deployed_capitals:
                avg_deployed = np.mean(deployed_capitals)
                total_pnl = sum(t.get('pnl', 0) for t in trades)
                deployed_return = (total_pnl / avg_deployed) * 100 if avg_deployed > 0 else total_return
            else:
                deployed_return = total_return
        else:
            deployed_return = total_return
        
        # Use deployed return as primary metric
        primary_return = deployed_return
        
        # Annualized return
        annualized_return = ((final_value / initial_capital) ** (252 / days) - 1) * 100
        
        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(252) * 100
        
        # Sharpe Ratio
        excess_return = annualized_return - (self.risk_free_rate * 100)
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252) * 100
        sortino_ratio = excess_return / downside_std if downside_std > 0 else 0
        
        # Maximum Drawdown
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax * 100
        max_drawdown = abs(drawdown.min())
        
        # Trade statistics
        if trades:
            winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
            losing_trades = [t for t in trades if t.get('pnl', 0) <= 0]
            
            win_rate = len(winning_trades) / len(trades) * 100
            
            total_wins = sum(t['pnl'] for t in winning_trades)
            total_losses = abs(sum(t['pnl'] for t in losing_trades))
            profit_factor = total_wins / total_losses if total_losses > 0 else 0
            
            avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        else:
            win_rate = 0
            profit_factor = 0
            avg_win = 0
            avg_loss = 0
        
        return {
            'total_return': primary_return,  # Now using deployed capital return
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_trades': len(trades)
        }
    
    def _score_returns(self, total_return: float) -> float:
        """Score based on total returns (0-100)"""
        # Excellent: >20%, Good: 10-20%, Average: 5-10%, Poor: 0-5%, Bad: <0%
        if total_return >= 20:
            return 100
        elif total_return >= 10:
            return 70 + (total_return - 10) * 3  # 70-100
        elif total_return >= 5:
            return 50 + (total_return - 5) * 4  # 50-70
        elif total_return >= 0:
            return 30 + (total_return) * 4  # 30-50
        else:
            return max(0, 30 + total_return * 3)  # 0-30
    
    def _score_risk_adjusted(self, sharpe: float, sortino: float) -> float:
        """Score based on risk-adjusted returns"""
        # Average Sharpe and Sortino
        avg_ratio = (sharpe + sortino) / 2
        
        # Excellent: >2, Good: 1-2, Average: 0.5-1, Poor: 0-0.5, Bad: <0
        if avg_ratio >= 2:
            return 100
        elif avg_ratio >= 1:
            return 70 + (avg_ratio - 1) * 30
        elif avg_ratio >= 0.5:
            return 50 + (avg_ratio - 0.5) * 40
        elif avg_ratio >= 0:
            return 30 + avg_ratio * 40
        else:
            return max(0, 30 + avg_ratio * 30)
    
    def _score_consistency(self, win_rate: float, profit_factor: float) -> float:
        """Score based on consistency metrics"""
        # Win rate component (0-50 points)
        if win_rate >= 60:
            win_score = 50
        elif win_rate >= 50:
            win_score = 35 + (win_rate - 50) * 1.5
        elif win_rate >= 40:
            win_score = 20 + (win_rate - 40) * 1.5
        else:
            win_score = max(0, win_rate * 0.5)
        
        # Profit factor component (0-50 points)
        if profit_factor >= 2:
            pf_score = 50
        elif profit_factor >= 1.5:
            pf_score = 35 + (profit_factor - 1.5) * 30
        elif profit_factor >= 1:
            pf_score = 20 + (profit_factor - 1) * 30
        else:
            pf_score = max(0, profit_factor * 20)
        
        return win_score + pf_score
    
    def _score_drawdown(self, max_drawdown: float) -> float:
        """Score based on maximum drawdown (lower is better)"""
        # Excellent: <5%, Good: 5-10%, Average: 10-20%, Poor: 20-30%, Bad: >30%
        if max_drawdown <= 5:
            return 100
        elif max_drawdown <= 10:
            return 80 - (max_drawdown - 5) * 4
        elif max_drawdown <= 20:
            return 50 - (max_drawdown - 10) * 3
        elif max_drawdown <= 30:
            return 20 - (max_drawdown - 20) * 2
        else:
            return max(0, 20 - (max_drawdown - 30))
    
    def _score_win_rate(self, win_rate: float) -> float:
        """Score based on win rate"""
        # Excellent: >60%, Good: 50-60%, Average: 40-50%, Poor: <40%
        if win_rate >= 60:
            return 100
        elif win_rate >= 50:
            return 70 + (win_rate - 50) * 3
        elif win_rate >= 40:
            return 50 + (win_rate - 40) * 2
        else:
            return max(0, win_rate * 1.25)
    
    def _get_rating(self, score: float) -> str:
        """Convert score to letter rating"""
        if score >= 90:
            return 'S'  # Superior
        elif score >= 80:
            return 'A'  # Excellent
        elif score >= 70:
            return 'B'  # Good
        elif score >= 60:
            return 'C'  # Average
        elif score >= 50:
            return 'D'  # Below Average
        else:
            return 'F'  # Fail


# Example usage
if __name__ == "__main__":
    # Sample data
    equity_curve = [100000 + i * 100 + np.random.randn() * 500 for i in range(100)]
    trades = [
        {'pnl': 500}, {'pnl': -200}, {'pnl': 800}, {'pnl': -150},
        {'pnl': 600}, {'pnl': -300}, {'pnl': 700}, {'pnl': 400}
    ]
    
    evaluator = StrategyEvaluator()
    score = evaluator.evaluate(equity_curve, trades, 100000, 30)
    
    print("="*70)
    print("STRATEGY EVALUATION SCORE")
    print("="*70)
    print(f"\nOverall Score: {score.overall_score:.1f}/100 (Rating: {score.rating})")
    print(f"\nComponent Scores:")
    print(f"  Returns:        {score.return_score:>6.1f}/100")
    print(f"  Risk-Adjusted:  {score.risk_adjusted_score:>6.1f}/100")
    print(f"  Consistency:    {score.consistency_score:>6.1f}/100")
    print(f"  Drawdown:       {score.drawdown_score:>6.1f}/100")
    print(f"  Win Rate:       {score.win_rate_score:>6.1f}/100")
    print(f"\nKey Metrics:")
    print(f"  Total Return:   {score.total_return:>6.2f}%")
    print(f"  Sharpe Ratio:   {score.sharpe_ratio:>6.2f}")
    print(f"  Max Drawdown:   {score.max_drawdown:>6.2f}%")
    print(f"  Win Rate:       {score.win_rate:>6.2f}%")
