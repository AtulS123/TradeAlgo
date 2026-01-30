from typing import Optional

class FixedRiskRewardTargetMixin:
    """
    Technical Target (Fixed Reward-to-Risk)
    
    Rule: Place a Limit Sell order at Entry Price + (2.5 * Risk).
    """
    
    def init_profit_target(self, risk_reward_ratio=2.5):
        self.rr_ratio = risk_reward_ratio
        
    def get_target_price(self, entry_price: float, stop_loss_price: float, side: int) -> float:
        """
        Calculate target price based on risk.
        """
        risk = abs(entry_price - stop_loss_price)
        reward = risk * self.rr_ratio
        
        if side == 1: # Long
            return entry_price + reward
        else: # Short
            return entry_price - reward
