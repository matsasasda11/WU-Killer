"""
Data validation utilities for the grid trading application.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Union, Optional


def validate_symbol(symbol: str) -> bool:
    """
    Validate trading symbol format.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT', 'BTC/USDT')
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If symbol format is invalid
    """
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Symbol must be a non-empty string")
    
    # Remove slash if present for validation
    clean_symbol = symbol.replace('/', '')
    
    # Check format: should be alphanumeric, 6-12 characters
    if not re.match(r'^[A-Z0-9]{6,12}$', clean_symbol.upper()):
        raise ValueError(
            "Symbol must be 6-12 alphanumeric characters (e.g., BTCUSDT)"
        )
    
    return True


def validate_price(price: Union[str, float, Decimal]) -> Decimal:
    """
    Validate and convert price to Decimal.
    
    Args:
        price: Price value
        
    Returns:
        Validated price as Decimal
        
    Raises:
        ValueError: If price is invalid
    """
    try:
        decimal_price = Decimal(str(price))
    except (InvalidOperation, TypeError):
        raise ValueError(f"Invalid price format: {price}")
    
    if decimal_price <= 0:
        raise ValueError("Price must be greater than 0")
    
    if decimal_price > Decimal('1000000'):
        raise ValueError("Price is too high (max: 1,000,000)")
    
    return decimal_price


def validate_quantity(quantity: Union[str, float, Decimal]) -> Decimal:
    """
    Validate and convert quantity to Decimal.
    
    Args:
        quantity: Quantity value
        
    Returns:
        Validated quantity as Decimal
        
    Raises:
        ValueError: If quantity is invalid
    """
    try:
        decimal_quantity = Decimal(str(quantity))
    except (InvalidOperation, TypeError):
        raise ValueError(f"Invalid quantity format: {quantity}")
    
    if decimal_quantity <= 0:
        raise ValueError("Quantity must be greater than 0")
    
    if decimal_quantity > Decimal('1000000'):
        raise ValueError("Quantity is too high (max: 1,000,000)")
    
    return decimal_quantity


def validate_percentage(percentage: Union[str, float, Decimal]) -> Decimal:
    """
    Validate percentage value.
    
    Args:
        percentage: Percentage value (0-100)
        
    Returns:
        Validated percentage as Decimal
        
    Raises:
        ValueError: If percentage is invalid
    """
    try:
        decimal_percentage = Decimal(str(percentage))
    except (InvalidOperation, TypeError):
        raise ValueError(f"Invalid percentage format: {percentage}")
    
    if decimal_percentage < 0 or decimal_percentage > 100:
        raise ValueError("Percentage must be between 0 and 100")
    
    return decimal_percentage


def validate_grid_levels(levels: int) -> int:
    """
    Validate number of grid levels.
    
    Args:
        levels: Number of grid levels
        
    Returns:
        Validated levels
        
    Raises:
        ValueError: If levels is invalid
    """
    if not isinstance(levels, int):
        raise ValueError("Grid levels must be an integer")
    
    if levels < 2:
        raise ValueError("Grid levels must be at least 2")
    
    if levels > 50:
        raise ValueError("Grid levels cannot exceed 50")
    
    return levels


def validate_price_range(min_price: Union[str, float, Decimal], 
                        max_price: Union[str, float, Decimal]) -> tuple[Decimal, Decimal]:
    """
    Validate price range.
    
    Args:
        min_price: Minimum price
        max_price: Maximum price
        
    Returns:
        Tuple of (min_price, max_price) as Decimals
        
    Raises:
        ValueError: If price range is invalid
    """
    min_decimal = validate_price(min_price)
    max_decimal = validate_price(max_price)
    
    if min_decimal >= max_decimal:
        raise ValueError("Minimum price must be less than maximum price")
    
    # Check if range is reasonable (at least 1% difference)
    price_diff_percentage = ((max_decimal - min_decimal) / min_decimal) * 100
    if price_diff_percentage < 1:
        raise ValueError("Price range too narrow (minimum 1% difference required)")
    
    return min_decimal, max_decimal


def validate_api_credentials(api_key: Optional[str], 
                           api_secret: Optional[str]) -> tuple[str, str]:
    """
    Validate API credentials.
    
    Args:
        api_key: API key
        api_secret: API secret
        
    Returns:
        Tuple of (api_key, api_secret)
        
    Raises:
        ValueError: If credentials are invalid
    """
    if not api_key or not isinstance(api_key, str):
        raise ValueError("API key is required and must be a string")
    
    if not api_secret or not isinstance(api_secret, str):
        raise ValueError("API secret is required and must be a string")
    
    if len(api_key) < 10:
        raise ValueError("API key appears to be too short")
    
    if len(api_secret) < 10:
        raise ValueError("API secret appears to be too short")
    
    return api_key, api_secret


def validate_order_size(order_size: Union[str, float, Decimal],
                       min_size: Optional[Decimal] = None,
                       max_size: Optional[Decimal] = None) -> Decimal:
    """
    Validate order size.
    
    Args:
        order_size: Order size to validate
        min_size: Minimum allowed size (optional)
        max_size: Maximum allowed size (optional)
        
    Returns:
        Validated order size as Decimal
        
    Raises:
        ValueError: If order size is invalid
    """
    decimal_size = validate_quantity(order_size)
    
    if min_size and decimal_size < min_size:
        raise ValueError(f"Order size {decimal_size} is below minimum {min_size}")
    
    if max_size and decimal_size > max_size:
        raise ValueError(f"Order size {decimal_size} exceeds maximum {max_size}")
    
    return decimal_size


def validate_tp_percentage(tp_percentage: Union[str, float, Decimal]) -> Decimal:
    """
    Validate take profit percentage.
    
    Args:
        tp_percentage: Take profit percentage
        
    Returns:
        Validated TP percentage as Decimal
        
    Raises:
        ValueError: If TP percentage is invalid
    """
    decimal_tp = validate_percentage(tp_percentage)
    
    if decimal_tp < Decimal('0.1'):
        raise ValueError("Take profit percentage must be at least 0.1%")
    
    if decimal_tp > Decimal('10'):
        raise ValueError("Take profit percentage cannot exceed 10%")
    
    return decimal_tp
