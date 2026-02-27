"""
REST API endpoints for the web GUI.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from core.trading_engine import TradingEngine
from strategy.grid_strategy import GridConfig
from utils.config import Config, load_config, save_config
from utils.logger import get_logger
from .app import get_trading_engine
from .websocket import websocket_router


router = APIRouter()
logger = get_logger("WebAPI")


# Pydantic models for API
class StatusResponse(BaseModel):
    """Status response model."""
    is_running: bool
    is_initialized: bool
    uptime_seconds: float
    components: Dict[str, bool]
    grid_status: Optional[Dict[str, Any]] = None
    risk_status: Optional[Dict[str, Any]] = None
    portfolio_summary: Optional[Dict[str, Any]] = None


class GridConfigRequest(BaseModel):
    """Grid configuration request model."""
    symbol: str = Field(..., description="Trading symbol")
    min_price: float = Field(..., gt=0, description="Minimum price")
    max_price: float = Field(..., gt=0, description="Maximum price")
    num_levels: int = Field(..., ge=2, le=50, description="Number of grid levels")
    tp_percentage: float = Field(..., gt=0, le=10, description="Take profit percentage")
    order_size: float = Field(..., gt=0, description="Order size")


class RiskConfigRequest(BaseModel):
    """Risk management configuration request model."""
    max_positions: int = Field(..., ge=1, le=20)
    max_exposure: float = Field(..., gt=0, le=1)
    stop_loss_percentage: float = Field(..., gt=0, le=50)
    max_drawdown: float = Field(..., gt=0, le=50)
    min_balance: float = Field(..., gt=0)


class OrderRequest(BaseModel):
    """Manual order request model."""
    symbol: str
    side: str  # "buy" or "sell"
    quantity: float
    price: Optional[float] = None
    order_type: str = "limit"  # "limit" or "market"


# Status endpoints
@router.get("/status", response_model=StatusResponse)
async def get_status(engine: TradingEngine = Depends(get_trading_engine)):
    """Get current bot status."""
    if not engine:
        raise HTTPException(status_code=503, detail="Trading engine not available")
    
    try:
        status = engine.get_status()
        return StatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance(engine: TradingEngine = Depends(get_trading_engine)):
    """Get performance summary."""
    if not engine:
        raise HTTPException(status_code=503, detail="Trading engine not available")
    
    try:
        return engine.get_performance_summary()
    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/grid-levels")
async def get_grid_levels(engine: TradingEngine = Depends(get_trading_engine)):
    """Get detailed grid levels information."""
    if not engine:
        raise HTTPException(status_code=503, detail="Trading engine not available")
    
    try:
        return engine.get_grid_levels_info()
    except Exception as e:
        logger.error(f"Error getting grid levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Control endpoints
@router.post("/start")
async def start_bot(
    background_tasks: BackgroundTasks,
    engine: TradingEngine = Depends(get_trading_engine)
):
    """Start the trading bot."""
    if not engine:
        raise HTTPException(status_code=503, detail="Trading engine not available")
    
    if engine.is_running:
        raise HTTPException(status_code=400, detail="Bot is already running")
    
    try:
        # Start in background
        background_tasks.add_task(engine.start)
        logger.info("Bot start initiated")
        return {"message": "Bot start initiated", "status": "starting"}
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_bot(engine: TradingEngine = Depends(get_trading_engine)):
    """Stop the trading bot."""
    if not engine:
        raise HTTPException(status_code=503, detail="Trading engine not available")
    
    try:
        await engine.stop()
        logger.info("Bot stopped")
        return {"message": "Bot stopped successfully", "status": "stopped"}
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency-stop")
async def emergency_stop(
    reason: str = "Manual emergency stop via API",
    engine: TradingEngine = Depends(get_trading_engine)
):
    """Emergency stop the trading bot."""
    if not engine:
        raise HTTPException(status_code=503, detail="Trading engine not available")
    
    try:
        await engine.emergency_stop(reason)
        logger.warning(f"Emergency stop triggered: {reason}")
        return {"message": "Emergency stop triggered", "reason": reason}
    except Exception as e:
        logger.error(f"Error during emergency stop: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-emergency")
async def reset_emergency_stop(engine: TradingEngine = Depends(get_trading_engine)):
    """Reset emergency stop."""
    if not engine:
        raise HTTPException(status_code=503, detail="Trading engine not available")
    
    try:
        await engine.reset_emergency_stop()
        logger.info("Emergency stop reset")
        return {"message": "Emergency stop reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting emergency stop: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Configuration endpoints
@router.get("/config")
async def get_config():
    """Get current configuration."""
    try:
        config = load_config()
        # Remove sensitive data
        config_dict = config.dict()
        config_dict.pop('api_key', None)
        config_dict.pop('api_secret', None)
        return config_dict
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/grid")
async def update_grid_config(
    grid_config: GridConfigRequest,
    engine: TradingEngine = Depends(get_trading_engine)
):
    """Update grid configuration."""
    if engine and engine.is_running:
        raise HTTPException(
            status_code=400, 
            detail="Cannot update configuration while bot is running"
        )
    
    try:
        # Load current config
        config = load_config()
        
        # Update grid settings
        config.trading.symbol = grid_config.symbol
        config.trading.price_range = {
            "min": grid_config.min_price,
            "max": grid_config.max_price
        }
        config.trading.grid_levels = grid_config.num_levels
        config.trading.tp_percentage = grid_config.tp_percentage
        config.trading.order_size = grid_config.order_size
        
        # Validate configuration
        if grid_config.min_price >= grid_config.max_price:
            raise HTTPException(
                status_code=400,
                detail="Minimum price must be less than maximum price"
            )
        
        # Save configuration
        save_config(config)
        logger.info("Grid configuration updated")
        
        return {"message": "Grid configuration updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating grid config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/risk")
async def update_risk_config(
    risk_config: RiskConfigRequest,
    engine: TradingEngine = Depends(get_trading_engine)
):
    """Update risk management configuration."""
    if engine and engine.is_running:
        raise HTTPException(
            status_code=400,
            detail="Cannot update configuration while bot is running"
        )
    
    try:
        # Load current config
        config = load_config()
        
        # Update risk settings
        config.risk_management.max_positions = risk_config.max_positions
        config.risk_management.max_exposure = risk_config.max_exposure
        config.risk_management.stop_loss_percentage = risk_config.stop_loss_percentage
        config.risk_management.max_drawdown = risk_config.max_drawdown
        config.risk_management.min_balance = risk_config.min_balance
        
        # Save configuration
        save_config(config)
        logger.info("Risk configuration updated")
        
        return {"message": "Risk configuration updated successfully"}
    except Exception as e:
        logger.error(f"Error updating risk config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Portfolio endpoints
@router.get("/portfolio")
async def get_portfolio(engine: TradingEngine = Depends(get_trading_engine)):
    """Get portfolio information."""
    if not engine or not engine.portfolio_manager:
        raise HTTPException(status_code=503, detail="Portfolio manager not available")
    
    try:
        return engine.portfolio_manager.get_portfolio_summary()
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/snapshots")
async def get_portfolio_snapshots(
    limit: int = 100,
    engine: TradingEngine = Depends(get_trading_engine)
):
    """Get portfolio snapshots."""
    if not engine or not engine.portfolio_manager:
        raise HTTPException(status_code=503, detail="Portfolio manager not available")
    
    try:
        return engine.portfolio_manager.get_snapshots(limit=limit)
    except Exception as e:
        logger.error(f"Error getting portfolio snapshots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/chart-data")
async def get_chart_data(
    hours: int = 24,
    engine: TradingEngine = Depends(get_trading_engine)
):
    """Get portfolio chart data."""
    if not engine or not engine.portfolio_manager:
        raise HTTPException(status_code=503, detail="Portfolio manager not available")
    
    try:
        return engine.portfolio_manager.get_performance_chart_data(hours=hours)
    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Grid management endpoints
@router.post("/grid/reset-level/{level_id}")
async def reset_grid_level(
    level_id: int,
    engine: TradingEngine = Depends(get_trading_engine)
):
    """Reset a specific grid level."""
    if not engine:
        raise HTTPException(status_code=503, detail="Trading engine not available")
    
    try:
        success = await engine.force_reset_grid_level(level_id)
        if success:
            logger.info(f"Grid level {level_id} reset")
            return {"message": f"Grid level {level_id} reset successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Grid level {level_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting grid level {level_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Market data endpoints
@router.get("/market-data/{symbol}")
async def get_market_data(
    symbol: str,
    engine: TradingEngine = Depends(get_trading_engine)
):
    """Get current market data for symbol."""
    if not engine or not engine.client:
        raise HTTPException(status_code=503, detail="API client not available")
    
    try:
        market_data = await engine.client.get_market_data(symbol)
        return {
            "symbol": market_data.symbol,
            "last_price": float(market_data.last_price),
            "bid_price": float(market_data.bid_price),
            "ask_price": float(market_data.ask_price),
            "volume_24h": float(market_data.volume_24h),
            "price_change_24h": float(market_data.price_change_24h),
            "timestamp": market_data.timestamp.isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Logs endpoint
@router.get("/logs")
async def get_logs(lines: int = 100):
    """Get recent log entries."""
    try:
        from pathlib import Path
        
        log_file = Path("logs/trading.log")
        if not log_file.exists():
            return {"logs": [], "message": "No log file found"}
        
        # Read last N lines
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "logs": [line.strip() for line in recent_lines],
            "total_lines": len(all_lines),
            "returned_lines": len(recent_lines)
        }
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Include WebSocket router
router.include_router(websocket_router)
