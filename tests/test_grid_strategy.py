"""
Unit tests for GridStrategy class.
"""

import pytest
import asyncio
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from strategy.grid_strategy import GridStrategy, GridConfig
from strategy.order_manager import OrderManager
from strategy.risk_manager import RiskManager, RiskLimits
from api import BybitClient, OrderSide, OrderStatus
from api.models import GridLevel, GridLevelStatus, MarketData, Order


@pytest.fixture
def mock_client():
    """Create mock Bybit client."""
    client = Mock(spec=BybitClient)
    client.get_market_data = AsyncMock()
    client.get_balance = AsyncMock()
    client.place_order = AsyncMock()
    client.cancel_order = AsyncMock()
    client.get_order_status = AsyncMock()
    return client


@pytest.fixture
def mock_order_manager():
    """Create mock order manager."""
    manager = Mock(spec=OrderManager)
    manager.place_order = AsyncMock()
    manager.cancel_order = AsyncMock()
    manager.update_all_orders = AsyncMock()
    manager.get_order_by_id = Mock()
    manager.cleanup = AsyncMock()
    return manager


@pytest.fixture
def mock_risk_manager():
    """Create mock risk manager."""
    limits = RiskLimits()
    manager = Mock(spec=RiskManager)
    manager.can_open_position = Mock(return_value=(True, "OK"))
    manager.update_balance = Mock()
    manager.check_stop_loss = Mock(return_value=False)
    manager.record_trade = Mock()
    manager.emergency_stop = False
    return manager


@pytest.fixture
def grid_config():
    """Create test grid configuration."""
    return GridConfig(
        symbol="BTCUSDT",
        min_price=Decimal("40000"),
        max_price=Decimal("50000"),
        num_levels=5,
        tp_percentage=Decimal("0.5"),
        order_size=Decimal("0.001"),
        price_precision=2,
        quantity_precision=6
    )


@pytest.fixture
def grid_strategy(mock_client, mock_order_manager, mock_risk_manager, grid_config):
    """Create GridStrategy instance for testing."""
    return GridStrategy(
        client=mock_client,
        order_manager=mock_order_manager,
        risk_manager=mock_risk_manager,
        config=grid_config
    )


class TestGridStrategy:
    """Test cases for GridStrategy class."""
    
    def test_initialization(self, grid_strategy, grid_config):
        """Test strategy initialization."""
        assert grid_strategy.config == grid_config
        assert not grid_strategy.is_running
        assert len(grid_strategy.grid_levels) == 0
        assert grid_strategy.total_cycles_completed == 0
    
    @pytest.mark.asyncio
    async def test_initialize_grid(self, grid_strategy, mock_client):
        """Test grid initialization."""
        # Mock market data
        market_data = MarketData(
            symbol="BTCUSDT",
            last_price=Decimal("45000"),
            bid_price=Decimal("44999"),
            ask_price=Decimal("45001"),
            volume_24h=Decimal("1000"),
            price_change_24h=Decimal("100"),
            timestamp=datetime.now()
        )
        mock_client.get_market_data.return_value = market_data
        
        # Initialize grid
        success = await grid_strategy.initialize_grid()
        
        assert success
        assert len(grid_strategy.grid_levels) == 5
        assert grid_strategy.last_market_price == Decimal("45000")
        
        # Check grid levels
        for level_id, grid_level in grid_strategy.grid_levels.items():
            assert isinstance(grid_level, GridLevel)
            assert grid_level.level_id == level_id
            assert grid_level.price >= Decimal("40000")
            assert grid_level.price <= Decimal("50000")
            assert grid_level.tp_price < grid_level.price
            assert grid_level.quantity == Decimal("0.001")
    
    @pytest.mark.asyncio
    async def test_start_stop(self, grid_strategy, mock_client):
        """Test strategy start and stop."""
        # Mock market data
        market_data = MarketData(
            symbol="BTCUSDT",
            last_price=Decimal("45000"),
            bid_price=Decimal("44999"),
            ask_price=Decimal("45001"),
            volume_24h=Decimal("1000"),
            price_change_24h=Decimal("100"),
            timestamp=datetime.now()
        )
        mock_client.get_market_data.return_value = market_data
        
        # Start strategy (run for short time)
        start_task = asyncio.create_task(grid_strategy.start())
        await asyncio.sleep(0.1)  # Let it initialize
        
        assert grid_strategy.is_running
        
        # Stop strategy
        await grid_strategy.stop()
        
        # Wait for start task to complete
        try:
            await asyncio.wait_for(start_task, timeout=1.0)
        except asyncio.TimeoutError:
            start_task.cancel()
        
        assert not grid_strategy.is_running
    
    def test_should_activate_level(self, grid_strategy):
        """Test level activation logic."""
        grid_strategy.last_market_price = Decimal("45000")
        
        # Create test grid level
        grid_level = GridLevel(
            level_id=0,
            price=Decimal("46000"),  # Above market price
            tp_price=Decimal("45700"),
            quantity=Decimal("0.001")
        )
        
        # Should activate level above market price
        assert grid_strategy._should_activate_level(grid_level)
        
        # Level below market price should not activate
        grid_level.price = Decimal("44000")
        assert not grid_strategy._should_activate_level(grid_level)
    
    @pytest.mark.asyncio
    async def test_activate_level(self, grid_strategy, mock_order_manager, mock_client):
        """Test level activation."""
        # Setup mocks
        mock_balance = Mock()
        mock_balance.available_balance = Decimal("1000")
        mock_client.get_balance.return_value = mock_balance
        
        mock_order = Order(
            order_id="test_order_123",
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            order_type="Limit",
            quantity=Decimal("0.001"),
            price=Decimal("46000"),
            status=OrderStatus.NEW,
            created_time=datetime.now()
        )
        mock_order_manager.place_order.return_value = mock_order
        
        # Create test grid level
        grid_level = GridLevel(
            level_id=0,
            price=Decimal("46000"),
            tp_price=Decimal("45700"),
            quantity=Decimal("0.001")
        )
        grid_strategy.grid_levels[0] = grid_level
        
        # Activate level
        await grid_strategy._activate_level(0, grid_level)
        
        # Verify order was placed
        mock_order_manager.place_order.assert_called_once_with(
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            quantity=Decimal("0.001"),
            price=Decimal("46000")
        )
        
        # Verify level status updated
        assert grid_level.status == GridLevelStatus.SELL_PENDING
        assert grid_level.sell_order_id == "test_order_123"
    
    @pytest.mark.asyncio
    async def test_check_sell_order_fill(self, grid_strategy, mock_order_manager):
        """Test sell order fill detection."""
        # Create test grid level with sell order
        grid_level = GridLevel(
            level_id=0,
            price=Decimal("46000"),
            tp_price=Decimal("45700"),
            quantity=Decimal("0.001"),
            status=GridLevelStatus.SELL_PENDING,
            sell_order_id="test_order_123"
        )
        grid_strategy.grid_levels[0] = grid_level
        
        # Mock filled order
        filled_order = Order(
            order_id="test_order_123",
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            order_type="Limit",
            quantity=Decimal("0.001"),
            price=Decimal("46000"),
            status=OrderStatus.FILLED,
            filled_quantity=Decimal("0.001"),
            average_price=Decimal("46000"),
            created_time=datetime.now()
        )
        mock_order_manager.get_order_by_id.return_value = filled_order
        
        # Check sell order fill
        await grid_strategy._check_sell_order_fill(0, grid_level)
        
        # Verify status updated
        assert grid_level.status == GridLevelStatus.WAITING_TP
    
    @pytest.mark.asyncio
    async def test_check_tp_reached(self, grid_strategy, mock_order_manager):
        """Test TP reached detection."""
        # Setup grid level waiting for TP
        grid_level = GridLevel(
            level_id=0,
            price=Decimal("46000"),
            tp_price=Decimal("45700"),
            quantity=Decimal("0.001"),
            status=GridLevelStatus.WAITING_TP
        )
        grid_strategy.grid_levels[0] = grid_level
        
        # Mock buy order placement
        mock_order = Order(
            order_id="buy_order_123",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type="Limit",
            quantity=Decimal("0.001"),
            price=Decimal("46000"),
            status=OrderStatus.NEW,
            created_time=datetime.now()
        )
        mock_order_manager.place_order.return_value = mock_order
        
        # Set market price to TP level
        grid_strategy.last_market_price = Decimal("45700")
        
        # Check TP reached
        await grid_strategy._check_tp_reached(0, grid_level)
        
        # Verify buy order was placed
        mock_order_manager.place_order.assert_called_once_with(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=Decimal("0.001"),
            price=Decimal("46000")
        )
        
        # Verify status updated
        assert grid_level.status == GridLevelStatus.BUY_PENDING
        assert grid_level.buy_order_id == "buy_order_123"
    
    @pytest.mark.asyncio
    async def test_complete_cycle(self, grid_strategy, mock_order_manager, mock_risk_manager):
        """Test cycle completion."""
        # Setup grid level with both orders filled
        grid_level = GridLevel(
            level_id=0,
            price=Decimal("46000"),
            tp_price=Decimal("45700"),
            quantity=Decimal("0.001"),
            status=GridLevelStatus.BUY_PENDING,
            sell_order_id="sell_order_123",
            buy_order_id="buy_order_123"
        )
        grid_strategy.grid_levels[0] = grid_level
        
        # Mock orders
        sell_order = Order(
            order_id="sell_order_123",
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            order_type="Limit",
            quantity=Decimal("0.001"),
            price=Decimal("46000"),
            status=OrderStatus.FILLED,
            average_price=Decimal("46000"),
            created_time=datetime.now()
        )
        
        buy_order = Order(
            order_id="buy_order_123",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type="Limit",
            quantity=Decimal("0.001"),
            price=Decimal("46000"),
            status=OrderStatus.FILLED,
            average_price=Decimal("45700"),
            created_time=datetime.now()
        )
        
        def get_order_side_effect(order_id):
            if order_id == "sell_order_123":
                return sell_order
            elif order_id == "buy_order_123":
                return buy_order
            return None
        
        mock_order_manager.get_order_by_id.side_effect = get_order_side_effect
        
        # Complete cycle
        await grid_strategy._complete_cycle(0, grid_level)
        
        # Verify profit calculation and recording
        expected_profit = (Decimal("46000") - Decimal("45700")) * Decimal("0.001")
        assert grid_strategy.total_profit_realized == expected_profit
        assert grid_strategy.total_cycles_completed == 1
        
        # Verify trade recorded
        mock_risk_manager.record_trade.assert_called_once()
        
        # Verify level reset
        assert grid_level.status == GridLevelStatus.INACTIVE
        assert grid_level.sell_order_id is None
        assert grid_level.buy_order_id is None
    
    def test_get_grid_status(self, grid_strategy):
        """Test grid status retrieval."""
        grid_strategy.is_running = True
        grid_strategy.last_market_price = Decimal("45000")
        grid_strategy.total_cycles_completed = 5
        grid_strategy.total_profit_realized = Decimal("0.01")
        
        status = grid_strategy.get_grid_status()
        
        assert status["is_running"] is True
        assert status["last_market_price"] == 45000.0
        assert status["total_cycles_completed"] == 5
        assert status["total_profit_realized"] == 0.01
        assert "config" in status
        assert "status_counts" in status
    
    @pytest.mark.asyncio
    async def test_force_reset_level(self, grid_strategy, mock_order_manager):
        """Test force reset of grid level."""
        # Create test grid level
        grid_level = GridLevel(
            level_id=0,
            price=Decimal("46000"),
            tp_price=Decimal("45700"),
            quantity=Decimal("0.001"),
            status=GridLevelStatus.SELL_PENDING,
            sell_order_id="test_order_123"
        )
        grid_strategy.grid_levels[0] = grid_level
        
        # Mock successful cancellation
        mock_order_manager.cancel_order.return_value = True
        
        # Force reset
        success = await grid_strategy.force_reset_level(0)
        
        assert success
        assert grid_level.status == GridLevelStatus.INACTIVE
        assert grid_level.sell_order_id is None
        
        # Verify order was cancelled
        mock_order_manager.cancel_order.assert_called_once_with(
            "test_order_123", "BTCUSDT"
        )
