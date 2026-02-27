"""
Order management for grid trading strategy.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from api import BybitClient, Order, OrderStatus, OrderSide, OrderType
from api.exceptions import OrderError, BybitAPIError
from utils.logger import LoggerMixin, log_trade_execution, log_error_with_context
from utils.helpers import retry_async


@dataclass
class PendingOrder:
    """Represents a pending order with retry logic."""
    order: Order
    attempts: int = 0
    max_attempts: int = 3
    next_retry: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)


class OrderManager(LoggerMixin):
    """
    Manages order placement, tracking, and lifecycle for grid trading.
    
    Handles:
    - Order placement with retry logic
    - Order status monitoring
    - Order cancellation
    - Failed order recovery
    """
    
    def __init__(
        self,
        client: BybitClient,
        max_retry_attempts: int = 3,
        retry_delay: float = 1.0,
        order_timeout: int = 300
    ):
        """
        Initialize order manager.
        
        Args:
            client: Bybit API client
            max_retry_attempts: Maximum retry attempts for failed orders
            retry_delay: Delay between retry attempts (seconds)
            order_timeout: Order timeout in seconds
        """
        self.client = client
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay = retry_delay
        self.order_timeout = order_timeout
        
        # Order tracking
        self.active_orders: Dict[str, Order] = {}
        self.pending_orders: Dict[str, PendingOrder] = {}
        self.failed_orders: Set[str] = set()
        
        # Statistics
        self.total_orders_placed = 0
        self.total_orders_filled = 0
        self.total_orders_cancelled = 0
        self.total_orders_failed = 0
        
        self.logger.info("Order manager initialized")
    
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: Decimal,
        price: Decimal,
        order_id: Optional[str] = None
    ) -> Optional[Order]:
        """
        Place a new limit order.
        
        Args:
            symbol: Trading symbol
            side: Order side (Buy/Sell)
            quantity: Order quantity
            price: Order price
            order_id: Custom order ID (optional)
            
        Returns:
            Order object if successful, None if failed
        """
        try:
            # Place order via API
            order = await retry_async(
                lambda: self.client.place_order(
                    symbol=symbol,
                    side=side,
                    order_type=OrderType.LIMIT,
                    quantity=quantity,
                    price=price
                ),
                max_attempts=self.max_retry_attempts,
                delay=self.retry_delay,
                exceptions=(BybitAPIError, OrderError)
            )
            
            # Track order
            self.active_orders[order.order_id] = order
            self.total_orders_placed += 1
            
            log_trade_execution(
                action="PLACE",
                symbol=symbol,
                side=side.value,
                quantity=float(quantity),
                price=float(price),
                order_id=order.order_id
            )
            
            self.logger.info(
                f"Order placed successfully: {order.order_id} "
                f"({side.value} {quantity} {symbol} @ {price})"
            )
            
            return order
            
        except Exception as e:
            self.total_orders_failed += 1
            log_error_with_context(
                error=e,
                context="place_order",
                symbol=symbol,
                side=side.value,
                quantity=float(quantity),
                price=float(price)
            )
            return None
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel an existing order.
        
        Args:
            order_id: Order ID to cancel
            symbol: Trading symbol
            
        Returns:
            True if successful
        """
        try:
            success = await retry_async(
                lambda: self.client.cancel_order(order_id, symbol),
                max_attempts=self.max_retry_attempts,
                delay=self.retry_delay,
                exceptions=(BybitAPIError, OrderError)
            )
            
            if success:
                # Update order status
                if order_id in self.active_orders:
                    self.active_orders[order_id].status = OrderStatus.CANCELLED
                
                self.total_orders_cancelled += 1
                
                log_trade_execution(
                    action="CANCEL",
                    symbol=symbol,
                    side="",
                    quantity=0,
                    price=0,
                    order_id=order_id
                )
                
                self.logger.info(f"Order cancelled successfully: {order_id}")
            
            return success
            
        except Exception as e:
            log_error_with_context(
                error=e,
                context="cancel_order",
                order_id=order_id,
                symbol=symbol
            )
            return False
    
    async def update_order_status(self, order_id: str, symbol: str) -> Optional[Order]:
        """
        Update order status from exchange.
        
        Args:
            order_id: Order ID
            symbol: Trading symbol
            
        Returns:
            Updated order object
        """
        try:
            updated_order = await self.client.get_order_status(order_id, symbol)
            
            # Update local tracking
            if order_id in self.active_orders:
                old_status = self.active_orders[order_id].status
                self.active_orders[order_id] = updated_order
                
                # Log status changes
                if old_status != updated_order.status:
                    self.logger.info(
                        f"Order status updated: {order_id} "
                        f"{old_status.value} -> {updated_order.status.value}"
                    )
                    
                    # Update statistics
                    if updated_order.status == OrderStatus.FILLED:
                        self.total_orders_filled += 1
                        log_trade_execution(
                            action="FILL",
                            symbol=symbol,
                            side=updated_order.side.value,
                            quantity=float(updated_order.filled_quantity),
                            price=float(updated_order.average_price or updated_order.price),
                            order_id=order_id
                        )
            
            return updated_order
            
        except Exception as e:
            log_error_with_context(
                error=e,
                context="update_order_status",
                order_id=order_id,
                symbol=symbol
            )
            return None
    
    async def update_all_orders(self, symbol: str) -> None:
        """
        Update status of all active orders.
        
        Args:
            symbol: Trading symbol
        """
        update_tasks = []
        
        for order_id in list(self.active_orders.keys()):
            order = self.active_orders[order_id]
            
            # Skip already completed orders
            if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
                continue
            
            # Check for timeout
            if self._is_order_timeout(order):
                self.logger.warning(f"Order timeout detected: {order_id}")
                await self.cancel_order(order_id, symbol)
                continue
            
            # Update status
            task = self.update_order_status(order_id, symbol)
            update_tasks.append(task)
        
        # Execute updates concurrently
        if update_tasks:
            await asyncio.gather(*update_tasks, return_exceptions=True)
    
    def get_active_orders(self, status_filter: Optional[OrderStatus] = None) -> List[Order]:
        """
        Get list of active orders.
        
        Args:
            status_filter: Filter by order status (optional)
            
        Returns:
            List of orders
        """
        orders = list(self.active_orders.values())
        
        if status_filter:
            orders = [order for order in orders if order.status == status_filter]
        
        return orders
    
    def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """
        Get order by ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order object if found
        """
        return self.active_orders.get(order_id)
    
    def remove_completed_orders(self) -> int:
        """
        Remove completed orders from tracking.
        
        Returns:
            Number of orders removed
        """
        completed_statuses = [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]
        completed_orders = []
        
        for order_id, order in self.active_orders.items():
            if order.status in completed_statuses:
                completed_orders.append(order_id)
        
        for order_id in completed_orders:
            del self.active_orders[order_id]
        
        if completed_orders:
            self.logger.info(f"Removed {len(completed_orders)} completed orders from tracking")
        
        return len(completed_orders)
    
    def _is_order_timeout(self, order: Order) -> bool:
        """Check if order has timed out."""
        if not order.created_time:
            return False
        
        timeout_time = order.created_time + timedelta(seconds=self.order_timeout)
        return datetime.now() > timeout_time
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get order management statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_placed": self.total_orders_placed,
            "total_filled": self.total_orders_filled,
            "total_cancelled": self.total_orders_cancelled,
            "total_failed": self.total_orders_failed,
            "active_orders": len(self.active_orders),
            "pending_orders": len(self.pending_orders)
        }
    
    async def cleanup(self) -> None:
        """Cleanup resources and cancel pending orders."""
        self.logger.info("Cleaning up order manager...")
        
        # Cancel all active orders
        cancel_tasks = []
        for order_id, order in self.active_orders.items():
            if order.status == OrderStatus.NEW:
                task = self.cancel_order(order_id, order.symbol)
                cancel_tasks.append(task)
        
        if cancel_tasks:
            await asyncio.gather(*cancel_tasks, return_exceptions=True)
        
        # Clear tracking
        self.active_orders.clear()
        self.pending_orders.clear()
        self.failed_orders.clear()
        
        self.logger.info("Order manager cleanup completed")
