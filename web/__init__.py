"""
Web GUI module for the Bybit Grid Trading Bot.

This module provides a modern web interface for monitoring and controlling
the trading bot, including real-time dashboards, configuration management,
and trading analytics.
"""

from .app import create_app
from .api import router as api_router
from .websocket import WebSocketManager

__all__ = [
    'create_app',
    'api_router',
    'WebSocketManager'
]
