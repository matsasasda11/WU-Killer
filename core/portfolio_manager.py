"""
Portfolio management for the trading application.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from api import BybitClient, Balance, Position
from api.models import TradingStats
from core.event_handler import EventHandler, EventType
from utils.logger import LoggerMixin, log_performance_metrics
from utils.helpers import calculate_drawdown, calculate_pnl


@dataclass
class PortfolioSnapshot:
    """Portfolio snapshot at a point in time."""
    timestamp: datetime
    total_balance: Decimal
    available_balance: Decimal
    locked_balance: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    total_value: Decimal
    positions_count: int
    
    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_balance": float(self.total_balance),
            "available_balance": float(self.available_balance),
            "locked_balance": float(self.locked_balance),
            "unrealized_pnl": float(self.unrealized_pnl),
            "realized_pnl": float(self.realized_pnl),
            "total_value": float(self.total_value),
            "positions_count": self.positions_count
        }


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics."""
    initial_balance: Decimal = Decimal('0')
    peak_balance: Decimal = Decimal('0')
    current_balance: Decimal = Decimal('0')
    total_realized_pnl: Decimal = Decimal('0')
    total_unrealized_pnl: Decimal = Decimal('0')
    max_drawdown: Decimal = Decimal('0')
    current_drawdown: Decimal = Decimal('0')
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)


class PortfolioManager(LoggerMixin):
    """
    Manages portfolio tracking, performance metrics, and reporting.
    
    Features:
    - Real-time portfolio tracking
    - Performance metrics calculation
    - Historical snapshots
    - Risk metrics monitoring
    - Reporting and analytics
    """
    
    def __init__(
        self,
        client: BybitClient,
        event_handler: EventHandler,
        base_currency: str = "USDT",
        snapshot_interval: int = 300  # 5 minutes
    ):
        """
        Initialize portfolio manager.
        
        Args:
            client: Bybit API client
            event_handler: Event handler instance
            base_currency: Base currency for calculations
            snapshot_interval: Interval for taking snapshots (seconds)
        """
        self.client = client
        self.event_handler = event_handler
        self.base_currency = base_currency
        self.snapshot_interval = snapshot_interval
        
        # Portfolio state
        self.metrics = PortfolioMetrics()
        self.current_positions: Dict[str, Position] = {}
        self.snapshots: List[PortfolioSnapshot] = []
        self.trading_stats = TradingStats()
        
        # Tracking
        self.is_running = False
        self.last_snapshot_time = datetime.now()
        
        # Subscribe to events
        self._setup_event_subscriptions()
        
        self.logger.info("Portfolio manager initialized")
    
    def _setup_event_subscriptions(self) -> None:
        """Setup event subscriptions."""
        self.event_handler.subscribe(EventType.ORDER_FILLED, self._on_order_filled)
        self.event_handler.subscribe(EventType.GRID_CYCLE_COMPLETED, self._on_cycle_completed)
        self.event_handler.subscribe(EventType.BALANCE_UPDATE, self._on_balance_update)
    
    async def start(self) -> None:
        """Start portfolio monitoring."""
        if self.is_running:
            self.logger.warning("Portfolio manager is already running")
            return
        
        self.is_running = True
        self.logger.info("Starting portfolio manager...")
        
        try:
            # Initialize with current portfolio state
            await self._initialize_portfolio()
            
            # Main monitoring loop
            while self.is_running:
                await self._update_portfolio()
                await asyncio.sleep(60)  # Update every minute
                
        except Exception as e:
            self.logger.error(f"Error in portfolio manager: {e}")
        finally:
            self.is_running = False
            self.logger.info("Portfolio manager stopped")
    
    async def stop(self) -> None:
        """Stop portfolio monitoring."""
        self.logger.info("Stopping portfolio manager...")
        self.is_running = False
    
    async def _initialize_portfolio(self) -> None:
        """Initialize portfolio with current state."""
        try:
            # Get current balance
            balance = await self.client.get_balance(self.base_currency)
            
            # Set initial metrics
            self.metrics.initial_balance = balance.wallet_balance
            self.metrics.peak_balance = balance.wallet_balance
            self.metrics.current_balance = balance.wallet_balance
            self.metrics.start_time = datetime.now()
            
            # Take initial snapshot
            await self._take_snapshot()
            
            self.logger.info(f"Portfolio initialized with balance: {balance.wallet_balance}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize portfolio: {e}")
    
    async def _update_portfolio(self) -> None:
        """Update portfolio state and metrics."""
        try:
            # Update balance
            balance = await self.client.get_balance(self.base_currency)
            await self._update_balance(balance)
            
            # Take snapshot if needed
            if self._should_take_snapshot():
                await self._take_snapshot()
            
            # Update metrics
            self._update_metrics()
            
            # Log performance periodically
            if datetime.now().minute % 15 == 0:  # Every 15 minutes
                self._log_performance()
            
        except Exception as e:
            self.logger.error(f"Error updating portfolio: {e}")
    
    async def _update_balance(self, balance: Balance) -> None:
        """Update balance information."""
        self.metrics.current_balance = balance.available_balance
        self.metrics.last_update = datetime.now()
        
        # Update peak balance
        if balance.available_balance > self.metrics.peak_balance:
            self.metrics.peak_balance = balance.available_balance
        
        # Calculate current drawdown
        self.metrics.current_drawdown = calculate_drawdown(
            self.metrics.peak_balance,
            balance.available_balance
        )
        
        # Update max drawdown
        if self.metrics.current_drawdown > self.metrics.max_drawdown:
            self.metrics.max_drawdown = self.metrics.current_drawdown
    
    def _should_take_snapshot(self) -> bool:
        """Check if a new snapshot should be taken."""
        time_since_last = datetime.now() - self.last_snapshot_time
        return time_since_last.total_seconds() >= self.snapshot_interval
    
    async def _take_snapshot(self) -> None:
        """Take a portfolio snapshot."""
        try:
            balance = await self.client.get_balance(self.base_currency)
            
            # Calculate total unrealized PnL from positions
            total_unrealized_pnl = sum(
                pos.unrealized_pnl for pos in self.current_positions.values()
            )
            
            snapshot = PortfolioSnapshot(
                timestamp=datetime.now(),
                total_balance=balance.wallet_balance,
                available_balance=balance.available_balance,
                locked_balance=balance.locked_balance,
                unrealized_pnl=total_unrealized_pnl,
                realized_pnl=self.metrics.total_realized_pnl,
                total_value=balance.wallet_balance + total_unrealized_pnl,
                positions_count=len(self.current_positions)
            )
            
            self.snapshots.append(snapshot)
            self.last_snapshot_time = datetime.now()
            
            # Limit snapshot history
            max_snapshots = 1000
            if len(self.snapshots) > max_snapshots:
                self.snapshots = self.snapshots[-max_snapshots:]
            
            self.logger.debug(f"Portfolio snapshot taken: {snapshot.total_value}")
            
        except Exception as e:
            self.logger.error(f"Error taking portfolio snapshot: {e}")
    
    def _update_metrics(self) -> None:
        """Update portfolio metrics."""
        # Calculate win rate
        if self.metrics.total_trades > 0:
            self.metrics.win_rate = (self.metrics.winning_trades / self.metrics.total_trades) * 100
        
        # Calculate profit factor
        total_wins = sum(
            pnl for pnl in [self.metrics.total_realized_pnl] if pnl > 0
        )
        total_losses = abs(sum(
            pnl for pnl in [self.metrics.total_realized_pnl] if pnl < 0
        ))
        
        if total_losses > 0:
            self.metrics.profit_factor = float(total_wins / total_losses)
    
    def _log_performance(self) -> None:
        """Log current performance metrics."""
        log_performance_metrics(
            total_trades=self.metrics.total_trades,
            profitable_trades=self.metrics.winning_trades,
            total_pnl=float(self.metrics.total_realized_pnl),
            win_rate=self.metrics.win_rate,
            max_drawdown=float(self.metrics.max_drawdown)
        )
    
    async def _on_order_filled(self, event) -> None:
        """Handle order filled event."""
        try:
            data = event.data
            self.logger.info(
                f"Order filled: {data['order_id']} - "
                f"{data['side']} {data['quantity']} {data['symbol']} @ {data['price']}"
            )
            
        except Exception as e:
            self.logger.error(f"Error handling order filled event: {e}")
    
    async def _on_cycle_completed(self, event) -> None:
        """Handle grid cycle completed event."""
        try:
            data = event.data
            profit = Decimal(str(data['profit']))
            
            # Update realized PnL
            self.metrics.total_realized_pnl += profit
            
            # Update trade statistics
            self.metrics.total_trades += 1
            if profit > 0:
                self.metrics.winning_trades += 1
            else:
                self.metrics.losing_trades += 1
            
            self.logger.info(
                f"Grid cycle completed: Level {data['level_id']}, "
                f"Profit: {profit}, Total PnL: {self.metrics.total_realized_pnl}"
            )
            
        except Exception as e:
            self.logger.error(f"Error handling cycle completed event: {e}")
    
    async def _on_balance_update(self, event) -> None:
        """Handle balance update event."""
        try:
            # Trigger portfolio update
            await self._update_portfolio()
            
        except Exception as e:
            self.logger.error(f"Error handling balance update event: {e}")
    
    def get_portfolio_summary(self) -> Dict[str, any]:
        """
        Get portfolio summary.
        
        Returns:
            Dictionary with portfolio information
        """
        return {
            "current_balance": float(self.metrics.current_balance),
            "initial_balance": float(self.metrics.initial_balance),
            "peak_balance": float(self.metrics.peak_balance),
            "total_realized_pnl": float(self.metrics.total_realized_pnl),
            "total_unrealized_pnl": float(self.metrics.total_unrealized_pnl),
            "current_drawdown": float(self.metrics.current_drawdown),
            "max_drawdown": float(self.metrics.max_drawdown),
            "total_trades": self.metrics.total_trades,
            "winning_trades": self.metrics.winning_trades,
            "losing_trades": self.metrics.losing_trades,
            "win_rate": self.metrics.win_rate,
            "profit_factor": self.metrics.profit_factor,
            "positions_count": len(self.current_positions),
            "start_time": self.metrics.start_time.isoformat(),
            "last_update": self.metrics.last_update.isoformat()
        }
    
    def get_snapshots(self, limit: Optional[int] = None) -> List[Dict[str, any]]:
        """
        Get portfolio snapshots.
        
        Args:
            limit: Maximum number of snapshots to return
            
        Returns:
            List of snapshot dictionaries
        """
        snapshots = self.snapshots
        if limit:
            snapshots = snapshots[-limit:]
        
        return [snapshot.to_dict() for snapshot in snapshots]
    
    def get_performance_chart_data(self, hours: int = 24) -> List[Dict[str, any]]:
        """
        Get performance data for charting.
        
        Args:
            hours: Number of hours of data to return
            
        Returns:
            List of data points for charting
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        chart_data = []
        for snapshot in self.snapshots:
            if snapshot.timestamp >= cutoff_time:
                chart_data.append({
                    "timestamp": snapshot.timestamp.isoformat(),
                    "total_value": float(snapshot.total_value),
                    "realized_pnl": float(snapshot.realized_pnl),
                    "unrealized_pnl": float(snapshot.unrealized_pnl)
                })
        
        return chart_data
