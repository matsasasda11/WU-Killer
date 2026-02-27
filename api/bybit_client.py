"""
Bybit API client implementation using ccxt.
"""

import asyncio
import ccxt.pro as ccxt
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from loguru import logger

from .models import Order, Position, Balance, MarketData, OrderSide, OrderType, OrderStatus
from .exceptions import (
    BybitAPIError, OrderError, InsufficientBalanceError, 
    RateLimitError, ConnectionError
)


class BybitClient:
    """
    Asynchronous Bybit API client using ccxt.
    
    Provides methods for trading operations, market data retrieval,
    and account management on Bybit exchange.
    """
    
    def __init__(
        self, 
        api_key: str, 
        api_secret: str, 
        testnet: bool = True,
        rate_limit: bool = True
    ):
        """
        Initialize Bybit client.
        
        Args:
            api_key: Bybit API key
            api_secret: Bybit API secret
            testnet: Whether to use testnet (default: True)
            rate_limit: Whether to enable rate limiting (default: True)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Initialize ccxt exchange
        self.exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': testnet,
            'rateLimit': rate_limit,
            'enableRateLimit': rate_limit,
            'options': {
                'defaultType': 'spot'  # Use spot trading
            }
        })
        
        self._connected = False
        logger.info(f"Bybit client initialized (testnet: {testnet})")
    
    async def connect(self) -> None:
        """Establish connection to Bybit API."""
        try:
            await self.exchange.load_markets()
            self._connected = True
            logger.info("Successfully connected to Bybit API")
        except Exception as e:
            logger.error(f"Failed to connect to Bybit API: {e}")
            raise ConnectionError(f"Failed to connect: {e}")
    
    async def disconnect(self) -> None:
        """Close connection to Bybit API."""
        try:
            await self.exchange.close()
            self._connected = False
            logger.info("Disconnected from Bybit API")
        except Exception as e:
            logger.warning(f"Error during disconnect: {e}")
    
    async def get_balance(self, coin: str = "USDT") -> Balance:
        """
        Get account balance for specified coin.
        
        Args:
            coin: Coin symbol (default: USDT)
            
        Returns:
            Balance object
        """
        try:
            balance_data = await self.exchange.fetch_balance()
            
            if coin not in balance_data:
                raise BybitAPIError(f"Coin {coin} not found in balance")
            
            coin_balance = balance_data[coin]
            
            return Balance(
                coin=coin,
                wallet_balance=Decimal(str(coin_balance['total'])),
                available_balance=Decimal(str(coin_balance['free'])),
                locked_balance=Decimal(str(coin_balance['used']))
            )
            
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise BybitAPIError(f"Failed to fetch balance: {e}")
    
    async def get_market_data(self, symbol: str) -> MarketData:
        """
        Get current market data for symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            MarketData object
        """
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            
            return MarketData(
                symbol=symbol,
                last_price=Decimal(str(ticker['last'])),
                bid_price=Decimal(str(ticker['bid'])),
                ask_price=Decimal(str(ticker['ask'])),
                volume_24h=Decimal(str(ticker['baseVolume'])),
                price_change_24h=Decimal(str(ticker['change'])),
                timestamp=datetime.fromtimestamp(ticker['timestamp'] / 1000)
            )
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            raise BybitAPIError(f"Failed to fetch market data: {e}")
    
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Optional[Decimal] = None
    ) -> Order:
        """
        Place a new order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side (Buy/Sell)
            order_type: Order type (Limit/Market)
            quantity: Order quantity
            price: Order price (required for limit orders)
            
        Returns:
            Order object
        """
        try:
            # Validate parameters
            if order_type == OrderType.LIMIT and price is None:
                raise OrderError("Price is required for limit orders")
            
            # Prepare order parameters
            order_params = {
                'symbol': symbol,
                'type': order_type.value.lower(),
                'side': side.value.lower(),
                'amount': float(quantity)
            }
            
            if price is not None:
                order_params['price'] = float(price)
            
            # Place order
            result = await self.exchange.create_order(**order_params)
            
            return Order(
                order_id=result['id'],
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price or Decimal('0'),
                status=OrderStatus.NEW,
                created_time=datetime.now()
            )
            
        except ccxt.InsufficientFunds as e:
            logger.error(f"Insufficient funds for order: {e}")
            raise InsufficientBalanceError(f"Insufficient funds: {e}")
        except ccxt.RateLimitExceeded as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise RateLimitError(f"Rate limit exceeded: {e}")
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise OrderError(f"Failed to place order: {e}")
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel an existing order.
        
        Args:
            order_id: Order ID to cancel
            symbol: Trading pair symbol
            
        Returns:
            True if successful
        """
        try:
            await self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Order {order_id} cancelled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            raise OrderError(f"Failed to cancel order: {e}")
    
    async def get_order_status(self, order_id: str, symbol: str) -> Order:
        """
        Get order status and details.
        
        Args:
            order_id: Order ID
            symbol: Trading pair symbol
            
        Returns:
            Order object with current status
        """
        try:
            order_data = await self.exchange.fetch_order(order_id, symbol)
            
            return Order(
                order_id=order_data['id'],
                symbol=order_data['symbol'],
                side=OrderSide(order_data['side'].title()),
                order_type=OrderType(order_data['type'].title()),
                quantity=Decimal(str(order_data['amount'])),
                price=Decimal(str(order_data['price'] or 0)),
                status=self._map_order_status(order_data['status']),
                filled_quantity=Decimal(str(order_data['filled'])),
                average_price=Decimal(str(order_data['average'] or 0)),
                created_time=datetime.fromtimestamp(order_data['timestamp'] / 1000),
                updated_time=datetime.fromtimestamp(order_data['lastTradeTimestamp'] / 1000) 
                    if order_data['lastTradeTimestamp'] else None
            )
            
        except Exception as e:
            logger.error(f"Error fetching order {order_id}: {e}")
            raise OrderError(f"Failed to fetch order: {e}")
    
    def _map_order_status(self, ccxt_status: str) -> OrderStatus:
        """Map ccxt order status to our OrderStatus enum."""
        status_mapping = {
            'open': OrderStatus.NEW,
            'closed': OrderStatus.FILLED,
            'canceled': OrderStatus.CANCELLED,
            'cancelled': OrderStatus.CANCELLED,
            'rejected': OrderStatus.REJECTED
        }
        return status_mapping.get(ccxt_status.lower(), OrderStatus.NEW)
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected
