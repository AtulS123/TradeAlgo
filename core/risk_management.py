"""
Risk Management Strategies for TradeAlgo
Multiple industry-standard risk management approaches
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict
import numpy as np


class RiskManagementType(Enum):
    """Types of risk management strategies"""
    FIXED_PERCENTAGE = "fixed_percentage"
    KELLY_CRITERION = "kelly_criterion"
    VOLATILITY_BASED = "volatility_based"
    ATR_BASED = "atr_based"
    RISK_REWARD_RATIO = "risk_reward_ratio"


@dataclass
class RiskParameters:
    """Risk management parameters for a trade"""
    position_size: int  # Number of shares
    stop_loss_price: Optional[float]  # Stop loss price
    take_profit_price: Optional[float]  # Take profit price
    max_loss: float  # Maximum loss in rupees
    risk_percent: float  # Risk as percentage of capital
    

class BaseRiskManager:
    """Base class for risk management strategies"""
    
    def __init__(self, capital: float, max_risk_per_trade: float = 2.0):
        """
        Initialize risk manager
        
        Args:
            capital: Total capital available
            max_risk_per_trade: Maximum risk per trade as percentage (default 2%)
        """
        self.capital = capital
        self.max_risk_per_trade = max_risk_per_trade
        
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: Optional[float] = None,
        **kwargs
    ) -> RiskParameters:
        """Calculate position size and risk parameters"""
        raise NotImplementedError


class FixedPercentageRisk(BaseRiskManager):
    """
    Fixed Percentage Risk Management
    - Risk fixed % of capital per trade (e.g., 2%)
    - Simple and conservative
    """
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: Optional[float] = None,
        **kwargs
    ) -> RiskParameters:
        """
        Calculate position size based on fixed percentage risk
        
        Args:
            entry_price: Entry price for the trade
            stop_loss_price: Stop loss price (optional)
            
        Returns:
            RiskParameters with position size and risk details
        """
        # Maximum amount to risk
        max_risk_amount = self.capital * (self.max_risk_per_trade / 100)
        
        if stop_loss_price:
            # Calculate position size based on stop loss
            risk_per_share = abs(entry_price - stop_loss_price)
            position_size = int(max_risk_amount / risk_per_share)
            
            # Ensure we don't exceed capital
            max_affordable = int(self.capital / entry_price)
            position_size = min(position_size, max_affordable)
            
        else:
            # No stop loss - use fixed percentage of capital
            position_value = self.capital * 0.2  # 20% of capital
            position_size = int(position_value / entry_price)
        
        # Calculate take profit (2:1 risk-reward ratio)
        take_profit_price = None
        if stop_loss_price:
            risk = abs(entry_price - stop_loss_price)
            take_profit_price = entry_price + (2 * risk) if entry_price > stop_loss_price else entry_price - (2 * risk)
        
        return RiskParameters(
            position_size=position_size,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            max_loss=max_risk_amount,
            risk_percent=self.max_risk_per_trade
        )


class KellyCriterionRisk(BaseRiskManager):
    """
    Kelly Criterion Risk Management
    - Optimal position sizing based on win rate and avg win/loss
    - More aggressive but mathematically optimal
    """
    
    def __init__(self, capital: float, win_rate: float = 0.5, avg_win: float = 1.0, avg_loss: float = 1.0):
        """
        Args:
            capital: Total capital
            win_rate: Historical win rate (0-1)
            avg_win: Average win amount
            avg_loss: Average loss amount
        """
        super().__init__(capital)
        self.win_rate = win_rate
        self.avg_win = avg_win
        self.avg_loss = avg_loss
        
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: Optional[float] = None,
        **kwargs
    ) -> RiskParameters:
        """Calculate position size using Kelly Criterion"""
        
        # Kelly formula: f = (p * b - q) / b
        # where p = win rate, q = loss rate, b = avg_win/avg_loss
        p = self.win_rate
        q = 1 - p
        b = self.avg_win / self.avg_loss if self.avg_loss > 0 else 1
        
        kelly_percent = (p * b - q) / b
        
        # Use fractional Kelly (0.25 to 0.5) for safety
        kelly_percent = max(0, min(kelly_percent * 0.25, 0.1))  # Cap at 10%
        
        position_value = self.capital * kelly_percent
        position_size = int(position_value / entry_price)
        
        # Calculate stop loss if not provided (2% below entry)
        if not stop_loss_price:
            stop_loss_price = entry_price * 0.98
        
        # Take profit at 2:1 ratio
        risk = abs(entry_price - stop_loss_price)
        take_profit_price = entry_price + (2 * risk)
        
        max_loss = position_size * risk
        
        return RiskParameters(
            position_size=position_size,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            max_loss=max_loss,
            risk_percent=kelly_percent * 100
        )


class VolatilityBasedRisk(BaseRiskManager):
    """
    Volatility-Based Risk Management
    - Adjust position size based on market volatility
    - Larger positions in low volatility, smaller in high volatility
    """
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: Optional[float] = None,
        volatility: float = 0.02,  # Daily volatility
        **kwargs
    ) -> RiskParameters:
        """
        Calculate position size based on volatility
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            volatility: Historical volatility (standard deviation of returns)
        """
        # Adjust risk based on volatility
        # Higher volatility = lower position size
        volatility_factor = 0.02 / max(volatility, 0.01)  # Normalize to 2% volatility
        adjusted_risk = self.max_risk_per_trade * min(volatility_factor, 2.0)
        
        max_risk_amount = self.capital * (adjusted_risk / 100)
        
        if not stop_loss_price:
            # Use volatility-based stop loss (2x daily volatility)
            stop_loss_price = entry_price * (1 - 2 * volatility)
        
        risk_per_share = abs(entry_price - stop_loss_price)
        position_size = int(max_risk_amount / risk_per_share)
        
        # Cap position size
        max_affordable = int(self.capital / entry_price)
        position_size = min(position_size, max_affordable)
        
        # Take profit at 1.5:1 ratio (more conservative in volatile markets)
        risk = abs(entry_price - stop_loss_price)
        take_profit_price = entry_price + (1.5 * risk)
        
        return RiskParameters(
            position_size=position_size,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            max_loss=max_risk_amount,
            risk_percent=adjusted_risk
        )


class ATRBasedRisk(BaseRiskManager):
    """
    ATR (Average True Range) Based Risk Management
    - Uses ATR for dynamic stop loss and position sizing
    - Industry standard for volatility-adjusted risk
    """
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: Optional[float] = None,
        atr: float = None,
        atr_multiplier: float = 2.0,
        **kwargs
    ) -> RiskParameters:
        """
        Calculate position size using ATR
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss (if None, calculated from ATR)
            atr: Average True Range value
            atr_multiplier: Multiplier for ATR stop loss (default 2.0)
        """
        if atr is None:
            atr = entry_price * 0.02  # Default 2% if ATR not provided
        
        # ATR-based stop loss
        if not stop_loss_price:
            stop_loss_price = entry_price - (atr * atr_multiplier)
        
        # Calculate position size
        max_risk_amount = self.capital * (self.max_risk_per_trade / 100)
        risk_per_share = abs(entry_price - stop_loss_price)
        position_size = int(max_risk_amount / risk_per_share)
        
        # Cap position size
        max_affordable = int(self.capital / entry_price)
        position_size = min(position_size, max_affordable)
        
        # Take profit at 3:1 ratio (ATR-based strategies can handle wider targets)
        risk = abs(entry_price - stop_loss_price)
        take_profit_price = entry_price + (3 * risk)
        
        return RiskParameters(
            position_size=position_size,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            max_loss=max_risk_amount,
            risk_percent=self.max_risk_per_trade
        )


class RiskRewardRatioManager(BaseRiskManager):
    """
    Risk-Reward Ratio Based Management
    - Ensures minimum risk-reward ratio (e.g., 1:2, 1:3)
    - Only takes trades with favorable risk-reward
    """
    
    def __init__(self, capital: float, min_risk_reward: float = 2.0, max_risk_per_trade: float = 2.0):
        """
        Args:
            capital: Total capital
            min_risk_reward: Minimum risk-reward ratio (default 2.0 = 1:2)
            max_risk_per_trade: Max risk per trade %
        """
        super().__init__(capital, max_risk_per_trade)
        self.min_risk_reward = min_risk_reward
        
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: float,
        take_profit_price: float,
        **kwargs
    ) -> Optional[RiskParameters]:
        """
        Calculate position size only if risk-reward ratio is favorable
        
        Returns:
            RiskParameters if trade meets criteria, None otherwise
        """
        # Calculate risk and reward
        risk = abs(entry_price - stop_loss_price)
        reward = abs(take_profit_price - entry_price)
        
        # Check risk-reward ratio
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        if risk_reward_ratio < self.min_risk_reward:
            # Trade doesn't meet minimum risk-reward criteria
            return None
        
        # Calculate position size
        max_risk_amount = self.capital * (self.max_risk_per_trade / 100)
        position_size = int(max_risk_amount / risk)
        
        # Cap position size
        max_affordable = int(self.capital / entry_price)
        position_size = min(position_size, max_affordable)
        
        return RiskParameters(
            position_size=position_size,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            max_loss=max_risk_amount,
            risk_percent=self.max_risk_per_trade
        )


# Factory function to create risk managers
def create_risk_manager(
    strategy_type: RiskManagementType,
    capital: float,
    **kwargs
) -> BaseRiskManager:
    """
    Create a risk manager of specified type
    
    Args:
        strategy_type: Type of risk management strategy
        capital: Total capital
        **kwargs: Additional parameters for specific strategies
        
    Returns:
        Risk manager instance
    """
    if strategy_type == RiskManagementType.FIXED_PERCENTAGE:
        return FixedPercentageRisk(capital, **kwargs)
    elif strategy_type == RiskManagementType.KELLY_CRITERION:
        return KellyCriterionRisk(capital, **kwargs)
    elif strategy_type == RiskManagementType.VOLATILITY_BASED:
        return VolatilityBasedRisk(capital, **kwargs)
    elif strategy_type == RiskManagementType.ATR_BASED:
        return ATRBasedRisk(capital, **kwargs)
    elif strategy_type == RiskManagementType.RISK_REWARD_RATIO:
        return RiskRewardRatioManager(capital, **kwargs)
    else:
        raise ValueError(f"Unknown risk management type: {strategy_type}")


# Example usage
if __name__ == "__main__":
    capital = 100000
    entry_price = 2500
    stop_loss = 2450
    
    print("="*70)
    print("RISK MANAGEMENT STRATEGIES COMPARISON")
    print("="*70)
    print(f"\nCapital: ₹{capital:,}")
    print(f"Entry Price: ₹{entry_price}")
    print(f"Stop Loss: ₹{stop_loss}\n")
    
    strategies = [
        (RiskManagementType.FIXED_PERCENTAGE, {}),
        (RiskManagementType.KELLY_CRITERION, {'win_rate': 0.6, 'avg_win': 1.5, 'avg_loss': 1.0}),
        (RiskManagementType.VOLATILITY_BASED, {'volatility': 0.025}),
        (RiskManagementType.ATR_BASED, {'atr': 50}),
        (RiskManagementType.RISK_REWARD_RATIO, {'min_risk_reward': 2.0}),
    ]
    
    for strategy_type, params in strategies:
        rm = create_risk_manager(strategy_type, capital, **params)
        
        if strategy_type == RiskManagementType.RISK_REWARD_RATIO:
            result = rm.calculate_position_size(entry_price, stop_loss, entry_price + 100)
        else:
            result = rm.calculate_position_size(entry_price, stop_loss)
        
        if result:
            print(f"\n{strategy_type.value.upper().replace('_', ' ')}")
            print("-" * 70)
            print(f"  Position Size:    {result.position_size:>6} shares")
            print(f"  Stop Loss:        ₹{result.stop_loss_price:>8,.2f}")
            print(f"  Take Profit:      ₹{result.take_profit_price:>8,.2f}" if result.take_profit_price else "  Take Profit:      Not set")
            print(f"  Max Loss:         ₹{result.max_loss:>8,.2f}")
            print(f"  Risk %:           {result.risk_percent:>8.2f}%")
