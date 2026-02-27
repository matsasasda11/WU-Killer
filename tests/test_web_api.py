"""
Unit tests for Web API endpoints.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from web.app import create_app
from core.trading_engine import TradingEngine


@pytest.fixture
def mock_trading_engine():
    """Create mock trading engine."""
    engine = Mock(spec=TradingEngine)
    engine.is_running = False
    engine.is_initialized = True
    engine.get_status.return_value = {
        "is_running": False,
        "is_initialized": True,
        "uptime_seconds": 0,
        "components": {
            "client_connected": True,
            "event_handler_running": False,
            "grid_strategy_running": False,
            "portfolio_manager_running": False
        }
    }
    engine.get_performance_summary.return_value = {
        "total_pnl": 0.0,
        "daily_pnl": 0.0,
        "win_rate": 0.0,
        "total_trades": 0
    }
    engine.get_grid_levels_info.return_value = []
    engine.start = AsyncMock()
    engine.stop = AsyncMock()
    engine.emergency_stop = AsyncMock()
    engine.reset_emergency_stop = AsyncMock()
    engine.force_reset_grid_level = AsyncMock(return_value=True)
    return engine


@pytest.fixture
def test_client(mock_trading_engine):
    """Create test client with mocked trading engine."""
    app = create_app()
    
    # Mock the trading engine in app state
    with patch('web.app.get_trading_engine', return_value=mock_trading_engine):
        with TestClient(app) as client:
            yield client


class TestWebAPI:
    """Test cases for Web API endpoints."""
    
    def test_health_check(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_get_status(self, test_client):
        """Test status endpoint."""
        response = test_client.get("/api/v1/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "is_running" in data
        assert "is_initialized" in data
        assert "uptime_seconds" in data
        assert "components" in data
    
    def test_get_performance(self, test_client):
        """Test performance endpoint."""
        response = test_client.get("/api/v1/performance")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_pnl" in data
        assert "daily_pnl" in data
        assert "win_rate" in data
        assert "total_trades" in data
    
    def test_get_grid_levels(self, test_client):
        """Test grid levels endpoint."""
        response = test_client.get("/api/v1/grid-levels")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_start_bot(self, test_client, mock_trading_engine):
        """Test start bot endpoint."""
        response = test_client.post("/api/v1/start")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "starting"
    
    def test_start_bot_already_running(self, test_client, mock_trading_engine):
        """Test start bot when already running."""
        mock_trading_engine.is_running = True
        
        response = test_client.post("/api/v1/start")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "already running" in data["detail"]
    
    def test_stop_bot(self, test_client, mock_trading_engine):
        """Test stop bot endpoint."""
        response = test_client.post("/api/v1/stop")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "stopped"
        
        # Verify stop was called
        mock_trading_engine.stop.assert_called_once()
    
    def test_emergency_stop(self, test_client, mock_trading_engine):
        """Test emergency stop endpoint."""
        response = test_client.post("/api/v1/emergency-stop")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "reason" in data
        
        # Verify emergency stop was called
        mock_trading_engine.emergency_stop.assert_called_once()
    
    def test_reset_emergency_stop(self, test_client, mock_trading_engine):
        """Test reset emergency stop endpoint."""
        response = test_client.post("/api/v1/reset-emergency")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        
        # Verify reset was called
        mock_trading_engine.reset_emergency_stop.assert_called_once()
    
    @patch('web.api.load_config')
    def test_get_config(self, mock_load_config, test_client):
        """Test get configuration endpoint."""
        mock_config = Mock()
        mock_config.dict.return_value = {
            "trading": {
                "symbol": "BTCUSDT",
                "grid_levels": 10
            },
            "risk_management": {
                "max_positions": 5
            }
        }
        mock_load_config.return_value = mock_config
        
        response = test_client.get("/api/v1/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "trading" in data
        assert "risk_management" in data
    
    @patch('web.api.save_config')
    @patch('web.api.load_config')
    def test_update_grid_config(self, mock_load_config, mock_save_config, test_client, mock_trading_engine):
        """Test update grid configuration endpoint."""
        # Mock current config
        mock_config = Mock()
        mock_config.trading = Mock()
        mock_load_config.return_value = mock_config
        
        grid_config = {
            "symbol": "ETHUSDT",
            "min_price": 2000.0,
            "max_price": 3000.0,
            "num_levels": 15,
            "tp_percentage": 0.5,
            "order_size": 0.01
        }
        
        response = test_client.put("/api/v1/config/grid", json=grid_config)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        
        # Verify save_config was called
        mock_save_config.assert_called_once()
    
    def test_update_grid_config_bot_running(self, test_client, mock_trading_engine):
        """Test update grid config when bot is running."""
        mock_trading_engine.is_running = True
        
        grid_config = {
            "symbol": "ETHUSDT",
            "min_price": 2000.0,
            "max_price": 3000.0,
            "num_levels": 15,
            "tp_percentage": 0.5,
            "order_size": 0.01
        }
        
        response = test_client.put("/api/v1/config/grid", json=grid_config)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "running" in data["detail"]
    
    def test_update_grid_config_invalid_range(self, test_client, mock_trading_engine):
        """Test update grid config with invalid price range."""
        grid_config = {
            "symbol": "ETHUSDT",
            "min_price": 3000.0,  # Higher than max
            "max_price": 2000.0,
            "num_levels": 15,
            "tp_percentage": 0.5,
            "order_size": 0.01
        }
        
        response = test_client.put("/api/v1/config/grid", json=grid_config)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "minimum price" in data["detail"].lower()
    
    @patch('web.api.save_config')
    @patch('web.api.load_config')
    def test_update_risk_config(self, mock_load_config, mock_save_config, test_client, mock_trading_engine):
        """Test update risk configuration endpoint."""
        # Mock current config
        mock_config = Mock()
        mock_config.risk_management = Mock()
        mock_load_config.return_value = mock_config
        
        risk_config = {
            "max_positions": 10,
            "max_exposure": 0.2,
            "stop_loss_percentage": 5.0,
            "max_drawdown": 10.0,
            "min_balance": 1000.0,
            "emergency_stop_loss": 15.0
        }
        
        response = test_client.put("/api/v1/config/risk", json=risk_config)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        
        # Verify save_config was called
        mock_save_config.assert_called_once()
    
    def test_reset_grid_level(self, test_client, mock_trading_engine):
        """Test reset grid level endpoint."""
        level_id = 3
        
        response = test_client.post(f"/api/v1/grid/reset-level/{level_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert str(level_id) in data["message"]
        
        # Verify force_reset_grid_level was called
        mock_trading_engine.force_reset_grid_level.assert_called_once_with(level_id)
    
    def test_reset_grid_level_not_found(self, test_client, mock_trading_engine):
        """Test reset grid level when level not found."""
        mock_trading_engine.force_reset_grid_level.return_value = False
        level_id = 999
        
        response = test_client.post(f"/api/v1/grid/reset-level/{level_id}")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]
    
    @patch('web.api.Path')
    def test_get_logs(self, mock_path, test_client):
        """Test get logs endpoint."""
        # Mock log file
        mock_log_file = Mock()
        mock_log_file.exists.return_value = True
        mock_path.return_value = mock_log_file
        
        # Mock file content
        log_lines = [
            "2024-01-15 10:30:45 | INFO | Test log line 1\n",
            "2024-01-15 10:30:46 | ERROR | Test error line\n",
            "2024-01-15 10:30:47 | INFO | Test log line 2\n"
        ]
        
        with patch('builtins.open', mock_open(read_data=''.join(log_lines))):
            response = test_client.get("/api/v1/logs?lines=100")
            assert response.status_code == 200
            
            data = response.json()
            assert "logs" in data
            assert "total_lines" in data
            assert "returned_lines" in data
            assert len(data["logs"]) == 3
    
    @patch('web.api.Path')
    def test_get_logs_file_not_found(self, mock_path, test_client):
        """Test get logs when file doesn't exist."""
        mock_log_file = Mock()
        mock_log_file.exists.return_value = False
        mock_path.return_value = mock_log_file
        
        response = test_client.get("/api/v1/logs")
        assert response.status_code == 200
        
        data = response.json()
        assert "logs" in data
        assert "message" in data
        assert data["logs"] == []
        assert "No log file found" in data["message"]
    
    def test_no_trading_engine(self, test_client):
        """Test endpoints when trading engine is not available."""
        with patch('web.app.get_trading_engine', return_value=None):
            response = test_client.get("/api/v1/status")
            assert response.status_code == 503
            
            data = response.json()
            assert "detail" in data
            assert "not available" in data["detail"]


def mock_open(read_data=''):
    """Mock open function for file operations."""
    from unittest.mock import mock_open as _mock_open
    return _mock_open(read_data=read_data)
