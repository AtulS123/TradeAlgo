"""
Order management classes
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

class OrderType(Enum):
    """Order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "SL"
    STOP_LOSS_MARKET = "SL-M"

class OrderSide(Enum):
    """Order side"""
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    """Order status"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

@dataclass
class Order:
    """
    Represents a trading order
    """
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    price: Optional[float] = None
    trigger_price: Optional[float] = None
    order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    average_price: Optional[float] = None
    timestamp: Optional[datetime] = None
    message: str = ""
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.status == OrderStatus.COMPLETE
    
    def is_pending(self) -> bool:
        """Check if order is pending"""
        return self.status in [OrderStatus.PENDING, OrderStatus.OPEN]
    
    def fill(self, quantity: int, price: float):
        """
        Fill order (partially or completely)
        
        Args:
            quantity: Quantity filled
            price: Fill price
        """
        self.filled_quantity += quantity
        
        # Update average price
        if self.average_price is None:
            self.average_price = price
        else:
            total_value = (self.average_price * (self.filled_quantity - quantity)) + (price * quantity)
            self.average_price = total_value / self.filled_quantity
        
        # Update status
        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.COMPLETE
        else:
            self.status = OrderStatus.OPEN
    
    def cancel(self):
        """Cancel the order"""
        self.status = OrderStatus.CANCELLED
    
    def reject(self, message: str):
        """
        Reject the order
        
        Args:
            message: Rejection reason
        """
        self.status = OrderStatus.REJECTED
        self.message = message


class OrderManager:
    """
    Manages orders for a trading session
    """
    
    def __init__(self):
        self.orders = []
        self.order_counter = 0
    
    def create_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        order_type: OrderType,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None
    ) -> Order:
        """
        Create a new order
        
        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Order quantity
            order_type: Order type
            price: Limit price (for LIMIT orders)
            trigger_price: Trigger price (for SL orders)
            
        Returns:
            Created order
        """
        self.order_counter += 1
        order_id = f"ORD{self.order_counter:06d}"
        
        order = Order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=price,
            trigger_price=trigger_price,
            order_id=order_id
        )
        
        self.orders.append(order)
        return order
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        for order in self.orders:
            if order.order_id == order_id:
                return order
        return None
    
    def get_pending_orders(self) -> list[Order]:
        """Get all pending orders"""
        return [o for o in self.orders if o.is_pending()]
    
    def get_filled_orders(self) -> list[Order]:
        """Get all filled orders"""
        return [o for o in self.orders if o.is_filled()]
    
    def cancel_all_pending(self):
        """Cancel all pending orders"""
        for order in self.get_pending_orders():
            order.cancel()
