"""
Grid trading strategy with individual Take Profit levels.

This module implements a modified grid trading strategy where each grid level
has its own Take Profit target. When a sell order is filled and TP is reached,
a buy order is placed at the same level to repeat the cycle.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from api import BybitClient, OrderSide, OrderStatus
from api.models import GridLevel, GridLevelStatus, MarketData
from strategy.order_manager import OrderManager
from strategy.risk_manager import RiskManager, RiskLimits
from utils.config import TradingConfig
from utils.logger import LoggerMixin, log_grid_update, log_risk_event
from utils.helpers import (
    calculate_grid_levels, calculate_tp_price, calculate_position_size,
    round_price, round_quantity, validate_grid_configuration
)
from utils.validators import validate_symbol, validate_price_range


@dataclass
class GridConfig:
    """Grid trading configuration."""
    symbol: str
    min_price: Decimal
    max_price: Decimal
    num_levels: int
    tp_percentage: Decimal
    order_size: Decimal
    price_precision: int = 2
    quantity_precision: int = 6


class GridStrategy(LoggerMixin):
    """
    Grid trading strategy with individual Take Profit levels.
    
    Strategy workflow:
    1. Initialize grid levels with individual TP targets
    2. Place sell orders at grid levels
    3. Monitor order fills and price movements
    4. When sell order fills, wait for TP to be reached
    5. When TP reached, place buy order at same level
    6. When buy order fills, place new sell order
    7. Repeat cycle
    """
    
    def __init__(
        self,
        client: BybitClient,
        order_manager: OrderManager,
        risk_manager: RiskManager,
        config: GridConfig
    ):
        """
        Initialize grid strategy.
        
        Args:
            client: Bybit API client
            order_manager: Order manager instance
            risk_manager: Risk manager instance
            config: Grid configuration
        """
        self.client = client
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.config = config
        
        # Validate configuration
        validate_symbol(config.symbol)
        validate_price_range(config.min_price, config.max_price)
        validate_grid_configuration(
            config.min_price,
            config.max_price,
            config.num_levels,
            config.tp_percentage,
            config.order_size
        )
        
        # Grid state
        self.grid_levels: Dict[int, GridLevel] = {}
        self.is_running = False
        self.last_market_price = Decimal('0')
        self.last_update = datetime.now()
        
        # Statistics
        self.total_cycles_completed = 0
        self.total_profit_realized = Decimal('0')
        
        self.logger.info(f"Grid strategy initialized for {config.symbol}")
    
    async def initialize_grid(self) -> bool:
        """
        Initialize grid levels and place initial orders.
        
        Returns:
            True if initialization successful
        """
        try:
            self.logger.info("Initializing grid levels...")
            
            # Calculate grid price levels
            price_levels = calculate_grid_levels(
                self.config.min_price,
                self.config.max_price,
                self.config.num_levels,
                spacing_mode="linear"
            )
            
            # Create grid levels with TP targets
            for i, price in enumerate(price_levels):
                tp_price = calculate_tp_price(price, self.config.tp_percentage)
                
                # Round prices to exchange precision
                rounded_price = round_price(price, self.config.price_precision)
                rounded_tp_price = round_price(tp_price, self.config.price_precision)
                rounded_quantity = round_quantity(
                    self.config.order_size, 
                    self.config.quantity_precision
                )
                
                grid_level = GridLevel(
                    level_id=i,
                    price=rounded_price,
                    tp_price=rounded_tp_price,
                    quantity=rounded_quantity,
                    status=GridLevelStatus.INACTIVE
                )
                
                self.grid_levels[i] = grid_level
                
                log_grid_update(
                    level_id=i,
                    status="CREATED",
                    price=float(rounded_price),
                    tp_price=float(rounded_tp_price)
                )
            
            self.logger.info(f"Created {len(self.grid_levels)} grid levels")
            
            # Get current market price to determine which levels to activate
            market_data = await self.client.get_market_data(self.config.symbol)
            self.last_market_price = market_data.last_price
            
            # Activate appropriate grid levels
            await self._activate_grid_levels()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize grid: {e}")
            return False
    
    async def start(self) -> None:
        """Start the grid trading strategy."""
        if self.is_running:
            self.logger.warning("Strategy is already running")
            return
        
        self.is_running = True
        self.logger.info("Starting grid trading strategy...")
        
        try:
            # Initialize grid if not already done
            if not self.grid_levels:
                success = await self.initialize_grid()
                if not success:
                    self.is_running = False
                    return
            
            # Main strategy loop
            while self.is_running:
                await self._strategy_cycle()
                await asyncio.sleep(1.0)  # Update interval
                
        except Exception as e:
            self.logger.error(f"Strategy error: {e}")
        finally:
            self.is_running = False
            self.logger.info("Grid trading strategy stopped")
    
    async def stop(self) -> None:
        """Stop the grid trading strategy."""
        self.logger.info("Stopping grid trading strategy...")
        self.is_running = False
        
        # Cancel all active orders
        await self._cancel_all_grid_orders()
        
        # Cleanup
        await self.order_manager.cleanup()
    
    async def _strategy_cycle(self) -> None:
        """Execute one cycle of the strategy."""
        try:
            # Update market data
            await self._update_market_data()
            
            # Update order statuses
            await self.order_manager.update_all_orders(self.config.symbol)
            
            # Process grid levels
            await self._process_grid_levels()
            
            # Update risk metrics
            await self._update_risk_metrics()
            
            # Check risk limits
            if self.risk_manager.emergency_stop:
                self.logger.warning("Emergency stop triggered, stopping strategy")
                await self.stop()
                return
            
            self.last_update = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error in strategy cycle: {e}")
    
    async def _update_market_data(self) -> None:
        """Update current market data."""
        try:
            market_data = await self.client.get_market_data(self.config.symbol)
            self.last_market_price = market_data.last_price
            
        except Exception as e:
            self.logger.error(f"Failed to update market data: {e}")
    
    async def _process_grid_levels(self) -> None:
        """Process all grid levels and update their states."""
        for level_id, grid_level in self.grid_levels.items():
            await self._process_single_grid_level(level_id, grid_level)
    
    async def _process_single_grid_level(self, level_id: int, grid_level: GridLevel) -> None:
        """
        Process a single grid level based on its current status.
        
        Args:
            level_id: Grid level ID
            grid_level: Grid level object
        """
        try:
            if grid_level.status == GridLevelStatus.INACTIVE:
                # Check if level should be activated
                if self._should_activate_level(grid_level):
                    await self._activate_level(level_id, grid_level)
            
            elif grid_level.status == GridLevelStatus.SELL_PENDING:
                # Check if sell order was filled
                await self._check_sell_order_fill(level_id, grid_level)
            
            elif grid_level.status == GridLevelStatus.WAITING_TP:
                # Check if TP price was reached
                await self._check_tp_reached(level_id, grid_level)
            
            elif grid_level.status == GridLevelStatus.BUY_PENDING:
                # Check if buy order was filled
                await self._check_buy_order_fill(level_id, grid_level)
                
        except Exception as e:
            self.logger.error(f"Error processing grid level {level_id}: {e}")

    def _should_activate_level(self, grid_level: GridLevel) -> bool:
        """
        Check if a grid level should be activated.

        Args:
            grid_level: Grid level to check

        Returns:
            True if level should be activated
        """
        # Activate levels above current market price for sell orders
        return self.last_market_price < grid_level.price

    async def _activate_level(self, level_id: int, grid_level: GridLevel) -> None:
        """
        Activate a grid level by placing a sell order.

        Args:
            level_id: Grid level ID
            grid_level: Grid level object
        """
        try:
            # Check risk limits
            position_value = grid_level.price * grid_level.quantity
            balance = await self.client.get_balance()

            can_open, reason = self.risk_manager.can_open_position(
                grid_level.quantity,
                position_value,
                balance.available_balance
            )

            if not can_open:
                self.logger.warning(f"Cannot activate level {level_id}: {reason}")
                return

            # Place sell order
            order = await self.order_manager.place_order(
                symbol=self.config.symbol,
                side=OrderSide.SELL,
                quantity=grid_level.quantity,
                price=grid_level.price
            )

            if order:
                grid_level.sell_order_id = order.order_id
                grid_level.status = GridLevelStatus.SELL_PENDING
                grid_level.last_updated = datetime.now()

                log_grid_update(
                    level_id=level_id,
                    status="SELL_PENDING",
                    price=float(grid_level.price),
                    tp_price=float(grid_level.tp_price)
                )

                self.logger.info(f"Activated grid level {level_id} with sell order {order.order_id}")

        except Exception as e:
            self.logger.error(f"Failed to activate level {level_id}: {e}")

    async def _check_sell_order_fill(self, level_id: int, grid_level: GridLevel) -> None:
        """
        Check if sell order was filled.

        Args:
            level_id: Grid level ID
            grid_level: Grid level object
        """
        if not grid_level.sell_order_id:
            return

        order = self.order_manager.get_order_by_id(grid_level.sell_order_id)
        if not order:
            return

        if order.status == OrderStatus.FILLED:
            # Sell order filled, start waiting for TP
            grid_level.status = GridLevelStatus.WAITING_TP
            grid_level.last_updated = datetime.now()

            log_grid_update(
                level_id=level_id,
                status="WAITING_TP",
                price=float(grid_level.price),
                tp_price=float(grid_level.tp_price)
            )

            self.logger.info(f"Sell order filled for level {level_id}, waiting for TP at {grid_level.tp_price}")

    async def _check_tp_reached(self, level_id: int, grid_level: GridLevel) -> None:
        """
        Check if Take Profit price was reached.

        Args:
            level_id: Grid level ID
            grid_level: Grid level object
        """
        # Check if current price reached TP level
        if self.last_market_price <= grid_level.tp_price:
            # TP reached, place buy order
            await self._place_buy_order(level_id, grid_level)

    async def _place_buy_order(self, level_id: int, grid_level: GridLevel) -> None:
        """
        Place buy order at grid level.

        Args:
            level_id: Grid level ID
            grid_level: Grid level object
        """
        try:
            # Place buy order at the same price level
            order = await self.order_manager.place_order(
                symbol=self.config.symbol,
                side=OrderSide.BUY,
                quantity=grid_level.quantity,
                price=grid_level.price
            )

            if order:
                grid_level.buy_order_id = order.order_id
                grid_level.status = GridLevelStatus.BUY_PENDING
                grid_level.last_updated = datetime.now()

                log_grid_update(
                    level_id=level_id,
                    status="BUY_PENDING",
                    price=float(grid_level.price),
                    tp_price=float(grid_level.tp_price)
                )

                self.logger.info(f"Placed buy order for level {level_id}: {order.order_id}")

        except Exception as e:
            self.logger.error(f"Failed to place buy order for level {level_id}: {e}")

    async def _check_buy_order_fill(self, level_id: int, grid_level: GridLevel) -> None:
        """
        Check if buy order was filled.

        Args:
            level_id: Grid level ID
            grid_level: Grid level object
        """
        if not grid_level.buy_order_id:
            return

        order = self.order_manager.get_order_by_id(grid_level.buy_order_id)
        if not order:
            return

        if order.status == OrderStatus.FILLED:
            # Buy order filled, complete the cycle
            await self._complete_cycle(level_id, grid_level)

    async def _complete_cycle(self, level_id: int, grid_level: GridLevel) -> None:
        """
        Complete a trading cycle and reset grid level.

        Args:
            level_id: Grid level ID
            grid_level: Grid level object
        """
        try:
            # Calculate profit from this cycle
            sell_order = self.order_manager.get_order_by_id(grid_level.sell_order_id)
            buy_order = self.order_manager.get_order_by_id(grid_level.buy_order_id)

            if sell_order and buy_order:
                # Calculate profit (sell price - buy price) * quantity
                cycle_profit = (sell_order.average_price - buy_order.average_price) * grid_level.quantity
                self.total_profit_realized += cycle_profit

                # Record trade for statistics
                self.risk_manager.record_trade(
                    entry_price=buy_order.average_price,
                    exit_price=sell_order.average_price,
                    quantity=grid_level.quantity,
                    side="buy"
                )

                self.logger.info(
                    f"Cycle completed for level {level_id}: "
                    f"Profit {cycle_profit:.6f}, Total profit: {self.total_profit_realized:.6f}"
                )

            # Reset grid level for next cycle
            grid_level.status = GridLevelStatus.INACTIVE
            grid_level.sell_order_id = None
            grid_level.buy_order_id = None
            grid_level.last_updated = datetime.now()

            self.total_cycles_completed += 1

            log_grid_update(
                level_id=level_id,
                status="CYCLE_COMPLETED",
                price=float(grid_level.price),
                tp_price=float(grid_level.tp_price)
            )

        except Exception as e:
            self.logger.error(f"Error completing cycle for level {level_id}: {e}")

    async def _activate_grid_levels(self) -> None:
        """Activate appropriate grid levels based on current market price."""
        activated_count = 0

        for level_id, grid_level in self.grid_levels.items():
            if self._should_activate_level(grid_level):
                await self._activate_level(level_id, grid_level)
                activated_count += 1

        self.logger.info(f"Activated {activated_count} grid levels")

    async def _cancel_all_grid_orders(self) -> None:
        """Cancel all active grid orders."""
        cancel_tasks = []

        for grid_level in self.grid_levels.values():
            if grid_level.sell_order_id:
                task = self.order_manager.cancel_order(grid_level.sell_order_id, self.config.symbol)
                cancel_tasks.append(task)

            if grid_level.buy_order_id:
                task = self.order_manager.cancel_order(grid_level.buy_order_id, self.config.symbol)
                cancel_tasks.append(task)

        if cancel_tasks:
            await asyncio.gather(*cancel_tasks, return_exceptions=True)
            self.logger.info(f"Cancelled {len(cancel_tasks)} grid orders")

    async def _update_risk_metrics(self) -> None:
        """Update risk management metrics."""
        try:
            # Get current balance
            balance = await self.client.get_balance()
            self.risk_manager.update_balance(balance)

            # Check stop loss
            if self.risk_manager.check_stop_loss(balance.available_balance):
                log_risk_event(
                    event_type="STOP_LOSS_TRIGGERED",
                    message="Stop loss triggered, stopping strategy"
                )
                await self.stop()

        except Exception as e:
            self.logger.error(f"Error updating risk metrics: {e}")

    def get_grid_status(self) -> Dict[str, any]:
        """
        Get current grid status.

        Returns:
            Dictionary with grid status information
        """
        status_counts = {}
        for status in GridLevelStatus:
            status_counts[status.value] = 0

        for grid_level in self.grid_levels.values():
            status_counts[grid_level.status.value] += 1

        return {
            "is_running": self.is_running,
            "total_levels": len(self.grid_levels),
            "last_market_price": float(self.last_market_price),
            "total_cycles_completed": self.total_cycles_completed,
            "total_profit_realized": float(self.total_profit_realized),
            "status_counts": status_counts,
            "last_update": self.last_update.isoformat(),
            "config": {
                "symbol": self.config.symbol,
                "min_price": float(self.config.min_price),
                "max_price": float(self.config.max_price),
                "num_levels": self.config.num_levels,
                "tp_percentage": float(self.config.tp_percentage),
                "order_size": float(self.config.order_size)
            }
        }

    def get_grid_levels_info(self) -> List[Dict[str, any]]:
        """
        Get detailed information about all grid levels.

        Returns:
            List of grid level information
        """
        levels_info = []

        for level_id, grid_level in self.grid_levels.items():
            level_info = {
                "level_id": level_id,
                "price": float(grid_level.price),
                "tp_price": float(grid_level.tp_price),
                "quantity": float(grid_level.quantity),
                "status": grid_level.status.value,
                "sell_order_id": grid_level.sell_order_id,
                "buy_order_id": grid_level.buy_order_id,
                "created_time": grid_level.created_time.isoformat(),
                "last_updated": grid_level.last_updated.isoformat()
            }
            levels_info.append(level_info)

        return levels_info

    async def force_reset_level(self, level_id: int) -> bool:
        """
        Force reset a grid level (emergency function).

        Args:
            level_id: Grid level ID to reset

        Returns:
            True if successful
        """
        if level_id not in self.grid_levels:
            return False

        try:
            grid_level = self.grid_levels[level_id]

            # Cancel any active orders
            if grid_level.sell_order_id:
                await self.order_manager.cancel_order(grid_level.sell_order_id, self.config.symbol)

            if grid_level.buy_order_id:
                await self.order_manager.cancel_order(grid_level.buy_order_id, self.config.symbol)

            # Reset level
            grid_level.status = GridLevelStatus.INACTIVE
            grid_level.sell_order_id = None
            grid_level.buy_order_id = None
            grid_level.last_updated = datetime.now()

            self.logger.warning(f"Force reset grid level {level_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error force resetting level {level_id}: {e}")
            return False

    def get_performance_summary(self) -> Dict[str, any]:
        """
        Get performance summary.

        Returns:
            Dictionary with performance metrics
        """
        risk_status = self.risk_manager.get_risk_status()
        trading_stats = self.risk_manager.get_trading_stats()

        return {
            "total_cycles_completed": self.total_cycles_completed,
            "total_profit_realized": float(self.total_profit_realized),
            "total_trades": trading_stats.total_trades,
            "profitable_trades": trading_stats.profitable_trades,
            "win_rate": trading_stats.win_rate,
            "total_pnl": float(trading_stats.total_pnl),
            "current_drawdown": risk_status["current_drawdown"],
            "daily_pnl": risk_status["daily_pnl"],
            "active_positions": risk_status["current_positions"],
            "emergency_stop": risk_status["emergency_stop"]
        }
