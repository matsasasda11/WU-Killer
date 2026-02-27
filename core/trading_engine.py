"""
Main trading engine that orchestrates all components.
"""

import asyncio
import signal
from datetime import datetime
from typing import Optional, Dict, Any

from api import BybitClient
from strategy import GridStrategy, OrderManager, RiskManager
from strategy.grid_strategy import GridConfig
from strategy.risk_manager import RiskLimits
from core import EventHandler, PortfolioManager
from utils.config import Config, load_config, validate_config
from utils.logger import LoggerMixin, setup_logger
from utils.validators import validate_api_credentials


class TradingEngine(LoggerMixin):
    """
    Main trading engine that coordinates all components.
    
    Responsibilities:
    - Initialize and manage all components
    - Handle application lifecycle
    - Coordinate between components
    - Provide unified API for external control
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize trading engine.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        # Load configuration
        self.config = load_config(config_path)
        validate_config(self.config)
        
        # Setup logging
        setup_logger(
            log_level=self.config.log_level,
            log_file=self.config.log_file,
            log_format=self.config.logging.format,
            rotation=self.config.logging.rotation,
            retention=self.config.logging.retention
        )
        
        # Initialize components
        self.client: Optional[BybitClient] = None
        self.event_handler: Optional[EventHandler] = None
        self.order_manager: Optional[OrderManager] = None
        self.risk_manager: Optional[RiskManager] = None
        self.portfolio_manager: Optional[PortfolioManager] = None
        self.grid_strategy: Optional[GridStrategy] = None
        
        # State
        self.is_running = False
        self.is_initialized = False
        self.start_time: Optional[datetime] = None
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        self.logger.info("Trading engine created")
    
    async def initialize(self) -> bool:
        """
        Initialize all components.
        
        Returns:
            True if initialization successful
        """
        try:
            self.logger.info("Initializing trading engine...")
            
            # Validate API credentials
            validate_api_credentials(self.config.api_key, self.config.api_secret)
            
            # Initialize Bybit client
            self.client = BybitClient(
                api_key=self.config.api_key,
                api_secret=self.config.api_secret,
                testnet=self.config.testnet
            )
            await self.client.connect()
            
            # Initialize event handler
            self.event_handler = EventHandler()
            
            # Initialize risk manager
            risk_limits = RiskLimits(
                max_positions=self.config.risk_management.max_positions,
                max_exposure=self.config.risk_management.max_exposure,
                stop_loss_percentage=self.config.risk_management.stop_loss_percentage,
                max_drawdown=self.config.risk_management.max_drawdown,
                min_balance=self.config.risk_management.min_balance,
                emergency_stop_loss=self.config.risk_management.emergency_stop_loss,
                max_daily_trades=self.config.risk_management.max_daily_trades
            )
            self.risk_manager = RiskManager(risk_limits)
            
            # Initialize order manager
            self.order_manager = OrderManager(
                client=self.client,
                max_retry_attempts=self.config.technical.retry_attempts,
                retry_delay=self.config.technical.rate_limit_delay,
                order_timeout=self.config.trading.order_timeout
            )
            
            # Initialize portfolio manager
            self.portfolio_manager = PortfolioManager(
                client=self.client,
                event_handler=self.event_handler
            )
            
            # Initialize grid strategy
            grid_config = GridConfig(
                symbol=self.config.trading.symbol,
                min_price=self.config.trading.price_range["min"],
                max_price=self.config.trading.price_range["max"],
                num_levels=self.config.trading.grid_levels,
                tp_percentage=self.config.trading.tp_percentage,
                order_size=self.config.trading.order_size,
                price_precision=self.config.technical.price_precision,
                quantity_precision=self.config.technical.quantity_precision
            )
            
            self.grid_strategy = GridStrategy(
                client=self.client,
                order_manager=self.order_manager,
                risk_manager=self.risk_manager,
                config=grid_config
            )
            
            self.is_initialized = True
            self.logger.info("Trading engine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize trading engine: {e}")
            await self.cleanup()
            return False
    
    async def start(self) -> None:
        """Start the trading engine."""
        if not self.is_initialized:
            success = await self.initialize()
            if not success:
                raise RuntimeError("Failed to initialize trading engine")
        
        if self.is_running:
            self.logger.warning("Trading engine is already running")
            return
        
        self.is_running = True
        self.start_time = datetime.now()
        
        self.logger.info("Starting trading engine...")
        
        try:
            # Start all components
            tasks = []
            
            # Start event handler
            if self.event_handler:
                tasks.append(self.event_handler.start())
            
            # Start portfolio manager
            if self.portfolio_manager:
                tasks.append(self.portfolio_manager.start())
            
            # Start grid strategy
            if self.grid_strategy:
                tasks.append(self.grid_strategy.start())
            
            # Wait for all components to start
            await asyncio.gather(*tasks)
            
        except Exception as e:
            self.logger.error(f"Error starting trading engine: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the trading engine."""
        if not self.is_running:
            return
        
        self.logger.info("Stopping trading engine...")
        self.is_running = False
        
        try:
            # Stop all components
            stop_tasks = []
            
            if self.grid_strategy:
                stop_tasks.append(self.grid_strategy.stop())
            
            if self.portfolio_manager:
                stop_tasks.append(self.portfolio_manager.stop())
            
            if self.event_handler:
                stop_tasks.append(self.event_handler.stop())
            
            # Wait for all components to stop
            await asyncio.gather(*stop_tasks, return_exceptions=True)
            
            # Cleanup
            await self.cleanup()
            
            self.logger.info("Trading engine stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping trading engine: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            if self.order_manager:
                await self.order_manager.cleanup()
            
            if self.client:
                await self.client.disconnect()
            
            self.logger.info("Trading engine cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current engine status.
        
        Returns:
            Dictionary with status information
        """
        status = {
            "is_running": self.is_running,
            "is_initialized": self.is_initialized,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() 
                if self.start_time else 0,
            "components": {
                "client_connected": self.client.is_connected if self.client else False,
                "event_handler_running": self.event_handler.is_running if self.event_handler else False,
                "grid_strategy_running": self.grid_strategy.is_running if self.grid_strategy else False,
                "portfolio_manager_running": self.portfolio_manager.is_running if self.portfolio_manager else False
            }
        }
        
        # Add component-specific status
        if self.grid_strategy:
            status["grid_status"] = self.grid_strategy.get_grid_status()
        
        if self.risk_manager:
            status["risk_status"] = self.risk_manager.get_risk_status()
        
        if self.portfolio_manager:
            status["portfolio_summary"] = self.portfolio_manager.get_portfolio_summary()
        
        if self.order_manager:
            status["order_statistics"] = self.order_manager.get_statistics()
        
        return status
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.grid_strategy:
            return {}
        
        return self.grid_strategy.get_performance_summary()
    
    async def emergency_stop(self, reason: str = "Manual emergency stop") -> None:
        """
        Emergency stop all trading activities.
        
        Args:
            reason: Reason for emergency stop
        """
        self.logger.warning(f"EMERGENCY STOP: {reason}")
        
        # Trigger emergency stop in risk manager
        if self.risk_manager:
            self.risk_manager.emergency_stop = True
        
        # Emit emergency stop event
        if self.event_handler:
            await self.event_handler.emit_emergency_stop(reason)
        
        # Stop the engine
        await self.stop()
    
    async def reset_emergency_stop(self) -> None:
        """Reset emergency stop (manual intervention required)."""
        if self.risk_manager:
            self.risk_manager.reset_emergency_stop()
        
        self.logger.warning("Emergency stop reset - manual intervention")
    
    def get_grid_levels_info(self) -> list:
        """Get detailed grid levels information."""
        if not self.grid_strategy:
            return []
        
        return self.grid_strategy.get_grid_levels_info()
    
    async def force_reset_grid_level(self, level_id: int) -> bool:
        """
        Force reset a specific grid level.
        
        Args:
            level_id: Grid level ID to reset
            
        Returns:
            True if successful
        """
        if not self.grid_strategy:
            return False
        
        return await self.grid_strategy.force_reset_level(level_id)
