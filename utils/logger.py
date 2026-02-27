"""
Logging configuration and utilities.
"""

import sys
from pathlib import Path
from typing import Optional
from loguru import logger


def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    rotation: str = "1 day",
    retention: str = "30 days"
) -> None:
    """
    Setup logging configuration using loguru.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        log_format: Custom log format (optional)
        rotation: Log rotation policy (default: "1 day")
        retention: Log retention policy (default: "30 days")
    """
    # Remove default handler
    logger.remove()
    
    # Default format
    if log_format is None:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    # Add console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Add file handler if specified
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            format=log_format,
            level=log_level,
            rotation=rotation,
            retention=retention,
            compression="zip",
            backtrace=True,
            diagnose=True
        )
    
    logger.info(f"Logger initialized with level: {log_level}")


def get_logger(name: str):
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logger.bind(name=name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self):
        """Get logger instance for this class."""
        return logger.bind(name=self.__class__.__name__)


def log_trade_execution(
    action: str,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    order_id: str = None
) -> None:
    """
    Log trade execution with structured format.
    
    Args:
        action: Trade action (PLACE, FILL, CANCEL)
        symbol: Trading symbol
        side: Order side (BUY/SELL)
        quantity: Order quantity
        price: Order price
        order_id: Order ID (optional)
    """
    log_data = {
        "action": action,
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "price": price
    }
    
    if order_id:
        log_data["order_id"] = order_id
    
    logger.info(f"TRADE {action}: {side} {quantity} {symbol} @ {price}", **log_data)


def log_grid_update(
    level_id: int,
    status: str,
    price: float,
    tp_price: float
) -> None:
    """
    Log grid level updates.
    
    Args:
        level_id: Grid level ID
        status: New status
        price: Grid level price
        tp_price: Take profit price
    """
    logger.info(
        f"GRID UPDATE: Level {level_id} -> {status} (Price: {price}, TP: {tp_price})",
        level_id=level_id,
        status=status,
        price=price,
        tp_price=tp_price
    )


def log_risk_event(
    event_type: str,
    message: str,
    **kwargs
) -> None:
    """
    Log risk management events.
    
    Args:
        event_type: Type of risk event
        message: Event message
        **kwargs: Additional event data
    """
    logger.warning(f"RISK EVENT [{event_type}]: {message}", **kwargs)


def log_error_with_context(
    error: Exception,
    context: str,
    **kwargs
) -> None:
    """
    Log errors with additional context.
    
    Args:
        error: Exception object
        context: Error context description
        **kwargs: Additional context data
    """
    logger.error(
        f"ERROR in {context}: {str(error)}",
        error_type=type(error).__name__,
        context=context,
        **kwargs
    )


def log_performance_metrics(
    total_trades: int,
    profitable_trades: int,
    total_pnl: float,
    win_rate: float,
    max_drawdown: float
) -> None:
    """
    Log performance metrics.
    
    Args:
        total_trades: Total number of trades
        profitable_trades: Number of profitable trades
        total_pnl: Total profit/loss
        win_rate: Win rate percentage
        max_drawdown: Maximum drawdown
    """
    logger.info(
        f"PERFORMANCE: Trades: {total_trades}, Profitable: {profitable_trades}, "
        f"PnL: {total_pnl:.2f}, Win Rate: {win_rate:.1f}%, Max DD: {max_drawdown:.2f}%",
        total_trades=total_trades,
        profitable_trades=profitable_trades,
        total_pnl=total_pnl,
        win_rate=win_rate,
        max_drawdown=max_drawdown
    )
