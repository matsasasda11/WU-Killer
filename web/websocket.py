"""
WebSocket manager for real-time updates.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from core.trading_engine import TradingEngine
from core.event_handler import EventType, Event


class WebSocketManager:
    """
    Manages WebSocket connections and real-time updates.
    
    Provides:
    - Real-time status updates
    - Live trading events
    - Portfolio updates
    - Grid level changes
    - Risk alerts
    """
    
    def __init__(self, trading_engine: TradingEngine):
        """
        Initialize WebSocket manager.
        
        Args:
            trading_engine: Trading engine instance
        """
        self.trading_engine = trading_engine
        self.active_connections: Set[WebSocket] = set()
        self.is_running = False
        self.update_task: Optional[asyncio.Task] = None
        
        logger.info("WebSocket manager initialized")
    
    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send initial status
        await self.send_to_connection(websocket, {
            "type": "connection_established",
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to trading bot"
        })
        
        # Send current status
        if self.trading_engine:
            status = self.trading_engine.get_status()
            await self.send_to_connection(websocket, {
                "type": "status_update",
                "data": status,
                "timestamp": datetime.now().isoformat()
            })
    
    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
        """
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_to_connection(self, websocket: WebSocket, data: Dict[str, Any]) -> None:
        """
        Send data to a specific WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            data: Data to send
        """
        try:
            await websocket.send_text(json.dumps(data, default=str))
        except Exception as e:
            logger.error(f"Error sending data to WebSocket: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, data: Dict[str, Any]) -> None:
        """
        Broadcast data to all connected WebSocket clients.
        
        Args:
            data: Data to broadcast
        """
        if not self.active_connections:
            return
        
        message = json.dumps(data, default=str)
        disconnected = set()
        
        for websocket in self.active_connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def setup_event_subscriptions(self) -> None:
        """Setup event subscriptions for real-time updates."""
        if not self.trading_engine or not self.trading_engine.event_handler:
            logger.warning("Cannot setup event subscriptions: event handler not available")
            return
        
        event_handler = self.trading_engine.event_handler
        
        # Subscribe to all relevant events
        event_handler.subscribe(EventType.ORDER_FILLED, self._on_order_filled)
        event_handler.subscribe(EventType.ORDER_CANCELLED, self._on_order_cancelled)
        event_handler.subscribe(EventType.GRID_LEVEL_ACTIVATED, self._on_grid_level_activated)
        event_handler.subscribe(EventType.GRID_CYCLE_COMPLETED, self._on_grid_cycle_completed)
        event_handler.subscribe(EventType.RISK_LIMIT_EXCEEDED, self._on_risk_limit_exceeded)
        event_handler.subscribe(EventType.EMERGENCY_STOP, self._on_emergency_stop)
        event_handler.subscribe(EventType.BALANCE_UPDATE, self._on_balance_update)
        event_handler.subscribe(EventType.ERROR_OCCURRED, self._on_error_occurred)
        
        logger.info("Event subscriptions setup completed")
    
    async def start_periodic_updates(self) -> None:
        """Start periodic status updates."""
        self.is_running = True
        self.update_task = asyncio.create_task(self._periodic_update_loop())
        logger.info("Periodic updates started")
    
    async def stop_periodic_updates(self) -> None:
        """Stop periodic status updates."""
        self.is_running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        logger.info("Periodic updates stopped")
    
    async def _periodic_update_loop(self) -> None:
        """Periodic update loop for status and metrics."""
        while self.is_running:
            try:
                if self.active_connections and self.trading_engine:
                    # Send status update
                    status = self.trading_engine.get_status()
                    await self.broadcast({
                        "type": "status_update",
                        "data": status,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Send performance update
                    performance = self.trading_engine.get_performance_summary()
                    await self.broadcast({
                        "type": "performance_update",
                        "data": performance,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Send grid levels update
                    grid_levels = self.trading_engine.get_grid_levels_info()
                    await self.broadcast({
                        "type": "grid_levels_update",
                        "data": grid_levels,
                        "timestamp": datetime.now().isoformat()
                    })
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in periodic update loop: {e}")
                await asyncio.sleep(5)
    
    # Event handlers
    async def _on_order_filled(self, event: Event) -> None:
        """Handle order filled event."""
        await self.broadcast({
            "type": "order_filled",
            "data": event.data,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source
        })
    
    async def _on_order_cancelled(self, event: Event) -> None:
        """Handle order cancelled event."""
        await self.broadcast({
            "type": "order_cancelled",
            "data": event.data,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source
        })
    
    async def _on_grid_level_activated(self, event: Event) -> None:
        """Handle grid level activated event."""
        await self.broadcast({
            "type": "grid_level_activated",
            "data": event.data,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source
        })
    
    async def _on_grid_cycle_completed(self, event: Event) -> None:
        """Handle grid cycle completed event."""
        await self.broadcast({
            "type": "grid_cycle_completed",
            "data": event.data,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source
        })
        
        # Also send updated performance data
        if self.trading_engine:
            performance = self.trading_engine.get_performance_summary()
            await self.broadcast({
                "type": "performance_update",
                "data": performance,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _on_risk_limit_exceeded(self, event: Event) -> None:
        """Handle risk limit exceeded event."""
        await self.broadcast({
            "type": "risk_alert",
            "data": event.data,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source,
            "severity": "warning"
        })
    
    async def _on_emergency_stop(self, event: Event) -> None:
        """Handle emergency stop event."""
        await self.broadcast({
            "type": "emergency_stop",
            "data": event.data,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source,
            "severity": "critical"
        })
    
    async def _on_balance_update(self, event: Event) -> None:
        """Handle balance update event."""
        await self.broadcast({
            "type": "balance_update",
            "data": event.data,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source
        })
    
    async def _on_error_occurred(self, event: Event) -> None:
        """Handle error occurred event."""
        await self.broadcast({
            "type": "error",
            "data": event.data,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source,
            "severity": "error"
        })
    
    async def send_notification(
        self, 
        message: str, 
        notification_type: str = "info",
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send a notification to all connected clients.
        
        Args:
            message: Notification message
            notification_type: Type of notification (info, warning, error, success)
            data: Additional data
        """
        await self.broadcast({
            "type": "notification",
            "message": message,
            "notification_type": notification_type,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)
    
    async def handle_client_message(self, websocket: WebSocket, message: str) -> None:
        """
        Handle incoming message from client.
        
        Args:
            websocket: WebSocket connection
            message: Message from client
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                await self.send_to_connection(websocket, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            
            elif message_type == "subscribe":
                # Handle subscription requests
                subscription_type = data.get("subscription")
                await self.send_to_connection(websocket, {
                    "type": "subscription_confirmed",
                    "subscription": subscription_type,
                    "timestamp": datetime.now().isoformat()
                })
            
            elif message_type == "request_status":
                # Send current status
                if self.trading_engine:
                    status = self.trading_engine.get_status()
                    await self.send_to_connection(websocket, {
                        "type": "status_update",
                        "data": status,
                        "timestamp": datetime.now().isoformat()
                    })
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message from client: {message}")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")


# WebSocket endpoint
from fastapi import APIRouter

websocket_router = APIRouter()

@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    from .app import get_websocket_manager
    
    manager = get_websocket_manager()
    if not manager:
        await websocket.close(code=1011, reason="WebSocket manager not available")
        return
    
    await manager.connect(websocket)
    
    # Start periodic updates if not already running
    if not manager.is_running:
        await manager.start_periodic_updates()
    
    try:
        while True:
            # Wait for messages from client
            message = await websocket.receive_text()
            await manager.handle_client_message(websocket, message)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
