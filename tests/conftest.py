"""
Pytest configuration and shared fixtures.
"""

import pytest
import asyncio
from decimal import Decimal
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from api import BybitClient, Balance, Order, OrderSide, OrderStatus
from api.models import MarketData, GridLevel, GridLevelStatus
from utils.config import Config, TradingConfig, RiskManagementConfig, TechnicalConfig


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config():
    """Create test configuration."""
    return Config(
        trading=TradingConfig(
            symbol="BTCUSDT",
            grid_levels=5,
            price_range={"min": 40000.0, "max": 50000.0},
            tp_percentage=0.5,
            order_size=0.001,
            update_interval=1.0
        ),
        risk_management=RiskManagementConfig(
            max_positions=3,
            max_exposure=0.1,
            stop_loss_percentage=5.0,
            max_drawdown=10.0,
            min_balance=100.0
        ),
        technical=TechnicalConfig(
            retry_attempts=3,
            timeout_seconds=30,
            price_precision=2,
            quantity_precision=6
        ),
        api_key="test_api_key",
        api_secret="test_api_secret",
        testnet=True
    )


@pytest.fixture
def mock_balance():
    """Create mock balance object."""
    return Balance(
        coin="USDT",
        wallet_balance=Decimal("1000.0"),
        available_balance=Decimal("900.0"),
        locked_balance=Decimal("100.0")
    )


@pytest.fixture
def mock_market_data():
    """Create mock market data."""
    return MarketData(
        symbol="BTCUSDT",
        last_price=Decimal("45000.0"),
        bid_price=Decimal("44999.0"),
        ask_price=Decimal("45001.0"),
        volume_24h=Decimal("1000.0"),
        price_change_24h=Decimal("100.0"),
        timestamp=datetime.now()
    )


@pytest.fixture
def mock_sell_order():
    """Create mock sell order."""
    return Order(
        order_id="sell_order_123",
        symbol="BTCUSDT",
        side=OrderSide.SELL,
        order_type="Limit",
        quantity=Decimal("0.001"),
        price=Decimal("46000.0"),
        status=OrderStatus.NEW,
        created_time=datetime.now()
    )


@pytest.fixture
def mock_buy_order():
    """Create mock buy order."""
    return Order(
        order_id="buy_order_123",
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type="Limit",
        quantity=Decimal("0.001"),
        price=Decimal("46000.0"),
        status=OrderStatus.NEW,
        created_time=datetime.now()
    )


@pytest.fixture
def mock_grid_level():
    """Create mock grid level."""
    return GridLevel(
        level_id=0,
        price=Decimal("46000.0"),
        tp_price=Decimal("45700.0"),
        quantity=Decimal("0.001"),
        status=GridLevelStatus.INACTIVE
    )


@pytest.fixture
def mock_bybit_client():
    """Create mock Bybit client."""
    client = Mock(spec=BybitClient)
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.get_balance = AsyncMock()
    client.get_market_data = AsyncMock()
    client.place_order = AsyncMock()
    client.cancel_order = AsyncMock()
    client.get_order_status = AsyncMock()
    client.is_connected = True
    return client


@pytest.fixture
def filled_sell_order(mock_sell_order):
    """Create filled sell order."""
    mock_sell_order.status = OrderStatus.FILLED
    mock_sell_order.filled_quantity = Decimal("0.001")
    mock_sell_order.average_price = Decimal("46000.0")
    return mock_sell_order


@pytest.fixture
def filled_buy_order(mock_buy_order):
    """Create filled buy order."""
    mock_buy_order.status = OrderStatus.FILLED
    mock_buy_order.filled_quantity = Decimal("0.001")
    mock_buy_order.average_price = Decimal("45700.0")
    return mock_buy_order


@pytest.fixture
def sample_grid_levels():
    """Create sample grid levels for testing."""
    levels = {}
    prices = [Decimal("40000"), Decimal("42500"), Decimal("45000"), Decimal("47500"), Decimal("50000")]
    
    for i, price in enumerate(prices):
        tp_price = price - (price * Decimal("0.005"))  # 0.5% TP
        levels[i] = GridLevel(
            level_id=i,
            price=price,
            tp_price=tp_price,
            quantity=Decimal("0.001"),
            status=GridLevelStatus.INACTIVE
        )
    
    return levels


# Async test helpers
@pytest.fixture
def async_mock():
    """Create async mock helper."""
    def _async_mock(*args, **kwargs):
        mock = Mock(*args, **kwargs)
        mock.return_value = asyncio.Future()
        mock.return_value.set_result(None)
        return mock
    return _async_mock


# Test data generators
@pytest.fixture
def price_generator():
    """Generate test prices."""
    def _generate_prices(start: float, end: float, count: int):
        step = (end - start) / (count - 1)
        return [Decimal(str(start + i * step)) for i in range(count)]
    return _generate_prices


@pytest.fixture
def order_generator():
    """Generate test orders."""
    def _generate_order(
        order_id: str = "test_order",
        symbol: str = "BTCUSDT",
        side: OrderSide = OrderSide.BUY,
        quantity: Decimal = Decimal("0.001"),
        price: Decimal = Decimal("45000"),
        status: OrderStatus = OrderStatus.NEW
    ):
        return Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type="Limit",
            quantity=quantity,
            price=price,
            status=status,
            created_time=datetime.now()
        )
    return _generate_order


# Cleanup helpers
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Add any cleanup logic here if needed
    pass
