"""
Custom exceptions for Bybit API operations.
"""

from typing import Optional, Dict, Any


class BybitAPIError(Exception):
    """Base exception for Bybit API errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.response_data = response_data or {}
        
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {super().__str__()}"
        return super().__str__()


class OrderError(BybitAPIError):
    """Exception raised for order-related errors."""
    pass


class InsufficientBalanceError(BybitAPIError):
    """Exception raised when account has insufficient balance."""
    pass


class RateLimitError(BybitAPIError):
    """Exception raised when API rate limit is exceeded."""
    pass


class ConnectionError(BybitAPIError):
    """Exception raised for connection-related errors."""
    pass


class ValidationError(BybitAPIError):
    """Exception raised for data validation errors."""
    pass


class PositionError(BybitAPIError):
    """Exception raised for position-related errors."""
    pass


class MarketDataError(BybitAPIError):
    """Exception raised for market data retrieval errors."""
    pass
