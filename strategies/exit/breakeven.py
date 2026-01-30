from typing import Optional

class BreakEvenStopMixin:
    """
    Break-Even "Free Ride"
    
    Rule: Once profit reaches 1R, move your Hard Stop Loss to your Entry Price.
    """
    
    def check_breakeven(self, current_price: float, entry_price: float, stop_loss_price: float, side: int) -> Optional[float]:
        """
        Check if stop should be moved to breakeven.
        Returns new stop price (entry price) if triggered, else None.
        """
        risk = abs(entry_price - stop_loss_price)
        
        if side == 1: # Long
            current_profit = current_price - entry_price
            if current_profit >= risk:
                return entry_price
        elif side == -1: # Short
            current_profit = entry_price - current_price
            if current_profit >= risk:
                return entry_price
                
        return None
