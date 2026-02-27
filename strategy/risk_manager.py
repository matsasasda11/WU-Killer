"""
Risk management for grid trading strategy.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from api import Balance, Position
from api.models import TradingStats
from utils.logger import LoggerMixin, log_risk_event
from utils.helpers import calculate_drawdown, calculate_pnl


@dataclass
class RiskLimits:
    """Risk management limits configuration."""
    max_positions: int = 5
    max_exposure: Decimal = Decimal('0.1')  # 10% of balance
    stop_loss_percentage: Decimal = Decimal('5.0')
    max_drawdown: Decimal = Decimal('10.0')
    min_balance: Decimal = Decimal('100.0')
    emergency_stop_loss: Decimal = Decimal('15.0')
    max_daily_trades: int = 100
    max_daily_loss: Decimal = Decimal('1000.0')


@dataclass
class RiskMetrics:
    """Current risk metrics."""
    current_positions: int = 0
    current_exposure: Decimal = Decimal('0')
    current_drawdown: Decimal = Decimal('0')
    daily_trades: int = 0
    daily_pnl: Decimal = Decimal('0')
    peak_balance: Decimal = Decimal('0')
    current_balance: Decimal = Decimal('0')
    unrealized_pnl: Decimal = Decimal('0')
    last_reset: datetime = None


class RiskManager(LoggerMixin):
    """
    Manages risk for grid trading strategy.
    
    Monitors:
    - Position limits
    - Exposure limits
    - Drawdown limits
    - Daily trading limits
    - Emergency stop conditions
    """
    
    def __init__(self, risk_limits: RiskLimits):
        """
        Initialize risk manager.
        
        Args:
            risk_limits: Risk limits configuration
        """
        self.limits = risk_limits
        self.metrics = RiskMetrics(last_reset=datetime.now())
        self.trading_stats = TradingStats()
        
        # Emergency flags
        self.emergency_stop = False
        self.stop_loss_triggered = False
        self.max_drawdown_reached = False
        
        # Daily tracking
        self.daily_trades_count = 0
        self.daily_start_balance = Decimal('0')
        self.last_daily_reset = datetime.now().date()
        
        self.logger.info("Risk manager initialized")
    
    def can_open_position(
        self,
        position_size: Decimal,
        position_value: Decimal,
        current_balance: Decimal
    ) -> Tuple[bool, str]:
        """
        Check if new position can be opened based on risk limits.
        
        Args:
            position_size: Size of new position
            position_value: Value of new position
            current_balance: Current account balance
            
        Returns:
            Tuple of (can_open, reason)
        """
        # Check emergency stop
        if self.emergency_stop:
            return False, "Emergency stop is active"
        
        # Check position count limit
        if self.metrics.current_positions >= self.limits.max_positions:
            return False, f"Maximum positions limit reached ({self.limits.max_positions})"
        
        # Check exposure limit
        new_exposure = self.metrics.current_exposure + position_value
        max_exposure_value = current_balance * self.limits.max_exposure
        
        if new_exposure > max_exposure_value:
            return False, f"Exposure limit exceeded ({self.limits.max_exposure * 100}%)"
        
        # Check minimum balance
        if current_balance < self.limits.min_balance:
            return False, f"Balance below minimum ({self.limits.min_balance})"
        
        # Check daily trade limit
        if self.daily_trades_count >= self.limits.max_daily_trades:
            return False, f"Daily trade limit reached ({self.limits.max_daily_trades})"
        
        # Check daily loss limit
        if self.metrics.daily_pnl <= -self.limits.max_daily_loss:
            return False, f"Daily loss limit reached ({self.limits.max_daily_loss})"
        
        return True, "Position can be opened"
    
    def update_balance(self, balance: Balance) -> None:
        """
        Update current balance and check risk metrics.
        
        Args:
            balance: Current account balance
        """
        self.metrics.current_balance = balance.available_balance
        
        # Update peak balance
        if balance.available_balance > self.metrics.peak_balance:
            self.metrics.peak_balance = balance.available_balance
        
        # Calculate current drawdown
        self.metrics.current_drawdown = calculate_drawdown(
            self.metrics.peak_balance,
            balance.available_balance
        )
        
        # Check drawdown limits
        self._check_drawdown_limits()
        
        # Reset daily metrics if needed
        self._reset_daily_metrics_if_needed()
        
        # Update daily PnL
        if self.daily_start_balance > 0:
            self.metrics.daily_pnl = balance.available_balance - self.daily_start_balance
    
    def update_positions(self, positions: List[Position]) -> None:
        """
        Update position metrics.
        
        Args:
            positions: List of current positions
        """
        self.metrics.current_positions = len(positions)
        
        # Calculate total exposure and unrealized PnL
        total_exposure = Decimal('0')
        total_unrealized_pnl = Decimal('0')
        
        for position in positions:
            position_value = position.size * position.mark_price
            total_exposure += position_value
            total_unrealized_pnl += position.unrealized_pnl
        
        self.metrics.current_exposure = total_exposure
        self.metrics.unrealized_pnl = total_unrealized_pnl
    
    def record_trade(
        self,
        entry_price: Decimal,
        exit_price: Decimal,
        quantity: Decimal,
        side: str
    ) -> None:
        """
        Record a completed trade for statistics.
        
        Args:
            entry_price: Trade entry price
            exit_price: Trade exit price
            quantity: Trade quantity
            side: Trade side ("buy" or "sell")
        """
        # Calculate PnL
        pnl = calculate_pnl(entry_price, exit_price, quantity, side)
        
        # Update statistics
        self.trading_stats.total_trades += 1
        self.trading_stats.total_pnl += pnl
        
        if pnl > 0:
            self.trading_stats.profitable_trades += 1
        else:
            self.trading_stats.losing_trades += 1
        
        # Update daily counter
        self.daily_trades_count += 1
        
        # Calculate win rate
        if self.trading_stats.total_trades > 0:
            self.trading_stats.win_rate = (
                self.trading_stats.profitable_trades / self.trading_stats.total_trades
            ) * 100
        
        # Calculate average profit/loss
        if self.trading_stats.profitable_trades > 0:
            self.trading_stats.average_profit = (
                sum(p for p in [pnl] if p > 0) / self.trading_stats.profitable_trades
            )
        
        if self.trading_stats.losing_trades > 0:
            self.trading_stats.average_loss = (
                sum(p for p in [pnl] if p < 0) / self.trading_stats.losing_trades
            )
        
        self.logger.info(
            f"Trade recorded: PnL {pnl:.4f}, "
            f"Total trades: {self.trading_stats.total_trades}, "
            f"Win rate: {self.trading_stats.win_rate:.1f}%"
        )
    
    def check_stop_loss(self, current_balance: Decimal) -> bool:
        """
        Check if stop loss should be triggered.
        
        Args:
            current_balance: Current account balance
            
        Returns:
            True if stop loss should be triggered
        """
        if self.daily_start_balance <= 0:
            return False
        
        # Calculate loss percentage
        loss_amount = self.daily_start_balance - current_balance
        loss_percentage = (loss_amount / self.daily_start_balance) * 100
        
        # Check regular stop loss
        if loss_percentage >= self.limits.stop_loss_percentage:
            if not self.stop_loss_triggered:
                self.stop_loss_triggered = True
                log_risk_event(
                    event_type="STOP_LOSS",
                    message=f"Stop loss triggered at {loss_percentage:.2f}% loss",
                    loss_percentage=float(loss_percentage),
                    loss_amount=float(loss_amount)
                )
            return True
        
        # Check emergency stop loss
        if loss_percentage >= self.limits.emergency_stop_loss:
            if not self.emergency_stop:
                self.emergency_stop = True
                log_risk_event(
                    event_type="EMERGENCY_STOP",
                    message=f"Emergency stop triggered at {loss_percentage:.2f}% loss",
                    loss_percentage=float(loss_percentage),
                    loss_amount=float(loss_amount)
                )
            return True
        
        return False
    
    def _check_drawdown_limits(self) -> None:
        """Check if drawdown limits are exceeded."""
        if self.metrics.current_drawdown >= self.limits.max_drawdown:
            if not self.max_drawdown_reached:
                self.max_drawdown_reached = True
                log_risk_event(
                    event_type="MAX_DRAWDOWN",
                    message=f"Maximum drawdown reached: {self.metrics.current_drawdown:.2f}%",
                    drawdown=float(self.metrics.current_drawdown),
                    limit=float(self.limits.max_drawdown)
                )
    
    def _reset_daily_metrics_if_needed(self) -> None:
        """Reset daily metrics if new day started."""
        current_date = datetime.now().date()
        
        if current_date > self.last_daily_reset:
            self.daily_trades_count = 0
            self.daily_start_balance = self.metrics.current_balance
            self.last_daily_reset = current_date
            self.metrics.daily_pnl = Decimal('0')
            
            # Reset daily flags
            self.stop_loss_triggered = False
            
            self.logger.info("Daily metrics reset")
    
    def get_risk_status(self) -> Dict[str, any]:
        """
        Get current risk status.
        
        Returns:
            Dictionary with risk metrics and flags
        """
        return {
            "emergency_stop": self.emergency_stop,
            "stop_loss_triggered": self.stop_loss_triggered,
            "max_drawdown_reached": self.max_drawdown_reached,
            "current_positions": self.metrics.current_positions,
            "max_positions": self.limits.max_positions,
            "current_exposure": float(self.metrics.current_exposure),
            "max_exposure": float(self.limits.max_exposure),
            "current_drawdown": float(self.metrics.current_drawdown),
            "max_drawdown": float(self.limits.max_drawdown),
            "daily_trades": self.daily_trades_count,
            "max_daily_trades": self.limits.max_daily_trades,
            "daily_pnl": float(self.metrics.daily_pnl),
            "total_pnl": float(self.trading_stats.total_pnl),
            "win_rate": self.trading_stats.win_rate
        }
    
    def reset_emergency_stop(self) -> None:
        """Reset emergency stop flag (manual intervention)."""
        self.emergency_stop = False
        self.stop_loss_triggered = False
        self.max_drawdown_reached = False
        
        log_risk_event(
            event_type="RESET",
            message="Emergency stop manually reset"
        )
        
        self.logger.warning("Emergency stop manually reset")
    
    def get_trading_stats(self) -> TradingStats:
        """Get trading statistics."""
        return self.trading_stats
