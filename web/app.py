"""
Main FastAPI application for the web GUI.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware

from core.trading_engine import TradingEngine
from utils.config import load_config
from utils.logger import setup_logger, get_logger
from .api import router as api_router
from .websocket import WebSocketManager


# Global instances
trading_engine: Optional[TradingEngine] = None
websocket_manager: Optional[WebSocketManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global trading_engine, websocket_manager
    
    logger = get_logger("WebApp")
    logger.info("Starting web application...")
    
    try:
        # Initialize trading engine
        config = load_config()
        trading_engine = TradingEngine()
        
        # Initialize WebSocket manager
        websocket_manager = WebSocketManager(trading_engine)
        
        # Initialize trading engine
        if await trading_engine.initialize():
            logger.info("Trading engine initialized successfully")
            
            # Subscribe to events for real-time updates
            if trading_engine.event_handler:
                await websocket_manager.setup_event_subscriptions()
            
        else:
            logger.error("Failed to initialize trading engine")
        
        # Store instances in app state
        app.state.trading_engine = trading_engine
        app.state.websocket_manager = websocket_manager
        
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        yield
    finally:
        # Cleanup
        logger.info("Shutting down web application...")
        if trading_engine:
            await trading_engine.cleanup()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    # Setup logging
    setup_logger(log_level="INFO", log_file="logs/web.log")
    
    # Create FastAPI app
    app = FastAPI(
        title="Bybit Grid Trading Bot",
        description="Modern web interface for grid trading bot",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add session middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key="your-secret-key-change-in-production"  # Change in production
    )
    
    # Setup templates
    templates_dir = Path(__file__).parent / "templates"
    templates = Jinja2Templates(directory=str(templates_dir))
    
    # Setup static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # Main dashboard route
    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        """Main dashboard page."""
        return templates.TemplateResponse(
            "dashboard.html",
            {"request": request, "title": "Grid Trading Dashboard"}
        )
    
    # Configuration page
    @app.get("/config", response_class=HTMLResponse)
    async def config_page(request: Request):
        """Configuration page."""
        return templates.TemplateResponse(
            "config.html",
            {"request": request, "title": "Configuration"}
        )
    
    # Analytics page
    @app.get("/analytics", response_class=HTMLResponse)
    async def analytics_page(request: Request):
        """Analytics page."""
        return templates.TemplateResponse(
            "analytics.html",
            {"request": request, "title": "Analytics"}
        )
    
    # Logs page
    @app.get("/logs", response_class=HTMLResponse)
    async def logs_page(request: Request):
        """Logs page."""
        return templates.TemplateResponse(
            "logs.html",
            {"request": request, "title": "Logs"}
        )
    
    # Health check
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "trading_engine": trading_engine.is_running if trading_engine else False,
            "websocket_manager": websocket_manager.is_running if websocket_manager else False
        }
    
    return app


def get_trading_engine() -> Optional[TradingEngine]:
    """Get the global trading engine instance."""
    return trading_engine


def get_websocket_manager() -> Optional[WebSocketManager]:
    """Get the global WebSocket manager instance."""
    return websocket_manager
