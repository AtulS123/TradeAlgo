"""
Quick test to verify deployed capital return calculation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.strategy_evaluator import StrategyEvaluator

# Simulate a simple scenario
initial_capital = 100000
final_capital = 102000  # Made ₹2,000 profit

# Simulate trades with deployed capital
trades = [
    {
        'quantity': 8,
        'entry_price': 2500,
        'pnl': 1000  # ₹1,000 profit on ₹20,000 deployed
    },
    {
        'quantity': 8,
        'entry_price': 2500,
        'pnl': 1000  # ₹1,000 profit on ₹20,000 deployed
    }
]

# Simple equity curve
equity_curve = [initial_capital] * 10 + [final_capital] * 10

evaluator = StrategyEvaluator()
score = evaluator.evaluate(equity_curve, trades, initial_capital, 30)

print("="*70)
print("DEPLOYED CAPITAL VS TOTAL CAPITAL RETURN COMPARISON")
print("="*70)
print(f"\nScenario:")
print(f"  Initial Capital: ₹{initial_capital:,}")
print(f"  Final Capital:   ₹{final_capital:,}")
print(f"  Total Profit:    ₹{final_capital - initial_capital:,}")
print(f"\nTrade Details:")
print(f"  Number of Trades: {len(trades)}")
print(f"  Avg Deployed per Trade: ₹{trades[0]['quantity'] * trades[0]['entry_price']:,}")
print(f"\nReturn Calculations:")
print(f"  Total Capital Return:    {((final_capital - initial_capital) / initial_capital) * 100:.2f}%")
print(f"  Deployed Capital Return: {score.total_return:.2f}%")
print(f"\nDifference: {score.total_return - ((final_capital - initial_capital) / initial_capital) * 100:.2f}%")
print("="*70)
