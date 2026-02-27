"""
Helper functions for the grid trading application.
"""

import asyncio
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from typing import List, Union, Optional, Tuple
from datetime import datetime, timedelta


def safe_decimal(value: Union[str, float, int, Decimal]) -> Decimal:
    """
    Safely convert value to Decimal.
    
    Args:
        value: Value to convert
        
    Returns:
        Decimal value or Decimal('0') if conversion fails
    """
    try:
        return Decimal(str(value))
    except (ValueError, TypeError, InvalidOperation):
        return Decimal('0')


def format_decimal(value: Decimal, precision: int = 8) -> str:
    """
    Format Decimal value with specified precision.
    
    Args:
        value: Decimal value to format
        precision: Number of decimal places
        
    Returns:
        Formatted string
    """
    if precision == 0:
        return str(int(value))
    
    format_str = f"{{:.{precision}f}}"
    return format_str.format(value).rstrip('0').rstrip('.')


def round_price(price: Decimal, precision: int = 2, round_up: bool = False) -> Decimal:
    """
    Round price to specified precision.
    
    Args:
        price: Price to round
        precision: Number of decimal places
        round_up: Whether to round up (default: round down)
        
    Returns:
        Rounded price
    """
    multiplier = Decimal('10') ** precision
    rounding = ROUND_UP if round_up else ROUND_DOWN
    return (price * multiplier).quantize(Decimal('1'), rounding=rounding) / multiplier


def round_quantity(quantity: Decimal, precision: int = 6) -> Decimal:
    """
    Round quantity to specified precision (always round down).
    
    Args:
        quantity: Quantity to round
        precision: Number of decimal places
        
    Returns:
        Rounded quantity
    """
    return round_price(quantity, precision, round_up=False)


def calculate_grid_levels(
    min_price: Decimal,
    max_price: Decimal,
    num_levels: int,
    spacing_mode: str = "linear"
) -> List[Decimal]:
    """
    Calculate grid price levels.
    
    Args:
        min_price: Minimum price
        max_price: Maximum price
        num_levels: Number of grid levels
        spacing_mode: Spacing mode ("linear" or "logarithmic")
        
    Returns:
        List of price levels
    """
    if num_levels < 2:
        raise ValueError("Number of levels must be at least 2")
    
    levels = []
    
    if spacing_mode == "linear":
        # Linear spacing
        step = (max_price - min_price) / (num_levels - 1)
        for i in range(num_levels):
            level_price = min_price + (step * i)
            levels.append(level_price)
    
    elif spacing_mode == "logarithmic":
        # Logarithmic spacing
        import math
        log_min = math.log(float(min_price))
        log_max = math.log(float(max_price))
        log_step = (log_max - log_min) / (num_levels - 1)
        
        for i in range(num_levels):
            log_price = log_min + (log_step * i)
            level_price = Decimal(str(math.exp(log_price)))
            levels.append(level_price)
    
    else:
        raise ValueError("Spacing mode must be 'linear' or 'logarithmic'")
    
    return levels


def calculate_tp_price(grid_price: Decimal, tp_percentage: Decimal) -> Decimal:
    """
    Calculate take profit price for a grid level.
    
    Args:
        grid_price: Grid level price
        tp_percentage: Take profit percentage
        
    Returns:
        Take profit price
    """
    tp_amount = grid_price * (tp_percentage / Decimal('100'))
    return grid_price - tp_amount  # TP is below grid price for sell orders


def calculate_position_size(
    balance: Decimal,
    price: Decimal,
    risk_percentage: Decimal,
    max_positions: int
) -> Decimal:
    """
    Calculate position size based on risk management rules.
    
    Args:
        balance: Available balance
        price: Entry price
        risk_percentage: Risk percentage per position
        max_positions: Maximum number of positions
        
    Returns:
        Position size
    """
    # Calculate risk amount per position
    risk_per_position = balance * (risk_percentage / Decimal('100'))
    
    # Divide by max positions to ensure we don't over-allocate
    risk_per_position = risk_per_position / max_positions
    
    # Calculate quantity
    quantity = risk_per_position / price
    
    return quantity


def calculate_pnl(
    entry_price: Decimal,
    exit_price: Decimal,
    quantity: Decimal,
    side: str
) -> Decimal:
    """
    Calculate profit/loss for a trade.
    
    Args:
        entry_price: Entry price
        exit_price: Exit price
        quantity: Trade quantity
        side: Trade side ("buy" or "sell")
        
    Returns:
        PnL amount
    """
    if side.lower() == "buy":
        # Long position: profit when exit > entry
        pnl = (exit_price - entry_price) * quantity
    else:
        # Short position: profit when exit < entry
        pnl = (entry_price - exit_price) * quantity
    
    return pnl


def is_price_within_range(
    price: Decimal,
    min_price: Decimal,
    max_price: Decimal,
    tolerance: Decimal = Decimal('0.001')
) -> bool:
    """
    Check if price is within specified range with tolerance.
    
    Args:
        price: Price to check
        min_price: Minimum price
        max_price: Maximum price
        tolerance: Tolerance percentage (default: 0.1%)
        
    Returns:
        True if price is within range
    """
    tolerance_amount = price * tolerance
    return (min_price - tolerance_amount) <= price <= (max_price + tolerance_amount)


def calculate_drawdown(peak_value: Decimal, current_value: Decimal) -> Decimal:
    """
    Calculate drawdown percentage.
    
    Args:
        peak_value: Peak portfolio value
        current_value: Current portfolio value
        
    Returns:
        Drawdown percentage
    """
    if peak_value <= 0:
        return Decimal('0')
    
    drawdown = ((peak_value - current_value) / peak_value) * Decimal('100')
    return max(drawdown, Decimal('0'))


def time_until_next_update(update_interval: float) -> float:
    """
    Calculate time until next update cycle.
    
    Args:
        update_interval: Update interval in seconds
        
    Returns:
        Time to wait in seconds
    """
    now = datetime.now()
    next_update = now + timedelta(seconds=update_interval)
    return (next_update - now).total_seconds()


async def retry_async(
    func,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple = (Exception,)
):
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        backoff_factor: Backoff multiplier
        exceptions: Exceptions to catch and retry
        
    Returns:
        Function result
        
    Raises:
        Last exception if all attempts fail
    """
    last_exception = None
    current_delay = delay
    
    for attempt in range(max_attempts):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:
                await asyncio.sleep(current_delay)
                current_delay *= backoff_factor
            else:
                raise last_exception


def validate_grid_configuration(
    min_price: Decimal,
    max_price: Decimal,
    num_levels: int,
    tp_percentage: Decimal,
    order_size: Decimal
) -> bool:
    """
    Validate grid configuration parameters.
    
    Args:
        min_price: Minimum grid price
        max_price: Maximum grid price
        num_levels: Number of grid levels
        tp_percentage: Take profit percentage
        order_size: Order size
        
    Returns:
        True if configuration is valid
        
    Raises:
        ValueError: If configuration is invalid
    """
    if min_price >= max_price:
        raise ValueError("Minimum price must be less than maximum price")
    
    if num_levels < 2 or num_levels > 50:
        raise ValueError("Number of levels must be between 2 and 50")
    
    if tp_percentage <= 0 or tp_percentage > 10:
        raise ValueError("TP percentage must be between 0 and 10")
    
    if order_size <= 0:
        raise ValueError("Order size must be greater than 0")
    
    # Check if grid spacing is reasonable
    price_range = max_price - min_price
    min_spacing = price_range / (num_levels * 100)  # At least 1% of range per level
    actual_spacing = price_range / (num_levels - 1)
    
    if actual_spacing < min_spacing:
        raise ValueError("Grid levels are too close together")
    
    return True
