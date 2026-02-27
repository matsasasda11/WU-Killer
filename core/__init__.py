"""
Core application modules.

This package contains the main application logic including the trading engine,
portfolio management, and event handling.
"""

from .trading_engine import TradingEngine
from .portfolio_manager import PortfolioManager
from .event_handler import EventHandler

__all__ = [
    'TradingEngine',
    'PortfolioManager',
    'EventHandler'
]
