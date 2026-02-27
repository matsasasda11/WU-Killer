"""
Event handling system for the trading application.
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from utils.logger import LoggerMixin


class EventType(str, Enum):
    """Event type enumeration."""
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    GRID_LEVEL_ACTIVATED = "grid_level_activated"
    GRID_CYCLE_COMPLETED = "grid_cycle_completed"
    RISK_LIMIT_EXCEEDED = "risk_limit_exceeded"
    EMERGENCY_STOP = "emergency_stop"
    MARKET_DATA_UPDATE = "market_data_update"
    BALANCE_UPDATE = "balance_update"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class Event:
    """Event data structure."""
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str = "unknown"


class EventHandler(LoggerMixin):
    """
    Event handling system for managing application events.
    
    Provides:
    - Event registration and subscription
    - Asynchronous event dispatching
    - Event history tracking
    - Error handling for event callbacks
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize event handler.
        
        Args:
            max_history: Maximum number of events to keep in history
        """
        self.max_history = max_history
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.event_history: List[Event] = []
        self.event_queue = asyncio.Queue()
        self.is_running = False
        
        # Initialize subscribers for all event types
        for event_type in EventType:
            self.subscribers[event_type] = []
        
        self.logger.info("Event handler initialized")
    
    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Callback function to execute when event occurs
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(callback)
        self.logger.info(f"Subscribed to {event_type.value} events")
    
    def unsubscribe(self, event_type: EventType, callback: Callable) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Callback function to remove
            
        Returns:
            True if callback was found and removed
        """
        if event_type in self.subscribers and callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            self.logger.info(f"Unsubscribed from {event_type.value} events")
            return True
        return False
    
    async def emit(
        self, 
        event_type: EventType, 
        data: Dict[str, Any], 
        source: str = "unknown"
    ) -> None:
        """
        Emit an event.
        
        Args:
            event_type: Type of event
            data: Event data
            source: Source of the event
        """
        event = Event(
            event_type=event_type,
            timestamp=datetime.now(),
            data=data,
            source=source
        )
        
        # Add to queue for processing
        await self.event_queue.put(event)
    
    async def start(self) -> None:
        """Start the event processing loop."""
        if self.is_running:
            self.logger.warning("Event handler is already running")
            return
        
        self.is_running = True
        self.logger.info("Starting event handler...")
        
        try:
            while self.is_running:
                try:
                    # Wait for events with timeout
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                    await self._process_event(event)
                except asyncio.TimeoutError:
                    # Continue loop on timeout
                    continue
                except Exception as e:
                    self.logger.error(f"Error in event processing loop: {e}")
                    
        except Exception as e:
            self.logger.error(f"Fatal error in event handler: {e}")
        finally:
            self.is_running = False
            self.logger.info("Event handler stopped")
    
    async def stop(self) -> None:
        """Stop the event processing loop."""
        self.logger.info("Stopping event handler...")
        self.is_running = False
    
    async def _process_event(self, event: Event) -> None:
        """
        Process a single event.
        
        Args:
            event: Event to process
        """
        try:
            # Add to history
            self._add_to_history(event)
            
            # Get subscribers for this event type
            callbacks = self.subscribers.get(event.event_type, [])
            
            if not callbacks:
                return
            
            # Execute all callbacks
            tasks = []
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        task = callback(event)
                        tasks.append(task)
                    else:
                        # Run sync callback in executor
                        task = asyncio.get_event_loop().run_in_executor(
                            None, callback, event
                        )
                        tasks.append(task)
                except Exception as e:
                    self.logger.error(f"Error creating task for callback: {e}")
            
            # Wait for all callbacks to complete
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Log any exceptions
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        self.logger.error(
                            f"Error in event callback {i} for {event.event_type.value}: {result}"
                        )
            
            self.logger.debug(
                f"Processed {event.event_type.value} event from {event.source} "
                f"with {len(callbacks)} callbacks"
            )
            
        except Exception as e:
            self.logger.error(f"Error processing event {event.event_type.value}: {e}")
    
    def _add_to_history(self, event: Event) -> None:
        """Add event to history with size limit."""
        self.event_history.append(event)
        
        # Maintain history size limit
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
    
    def get_event_history(
        self, 
        event_type: Optional[EventType] = None,
        limit: Optional[int] = None
    ) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return (optional)
            
        Returns:
            List of events
        """
        events = self.event_history
        
        # Filter by event type
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Apply limit
        if limit:
            events = events[-limit:]
        
        return events
    
    def get_event_counts(self) -> Dict[str, int]:
        """
        Get count of events by type.
        
        Returns:
            Dictionary with event counts
        """
        counts = {}
        for event_type in EventType:
            counts[event_type.value] = 0
        
        for event in self.event_history:
            counts[event.event_type.value] += 1
        
        return counts
    
    def clear_history(self) -> None:
        """Clear event history."""
        self.event_history.clear()
        self.logger.info("Event history cleared")
    
    async def emit_order_filled(
        self, 
        order_id: str, 
        symbol: str, 
        side: str, 
        quantity: float, 
        price: float
    ) -> None:
        """Emit order filled event."""
        await self.emit(
            EventType.ORDER_FILLED,
            {
                "order_id": order_id,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price
            },
            source="order_manager"
        )
    
    async def emit_grid_cycle_completed(
        self, 
        level_id: int, 
        profit: float, 
        total_profit: float
    ) -> None:
        """Emit grid cycle completed event."""
        await self.emit(
            EventType.GRID_CYCLE_COMPLETED,
            {
                "level_id": level_id,
                "profit": profit,
                "total_profit": total_profit
            },
            source="grid_strategy"
        )
    
    async def emit_risk_limit_exceeded(
        self, 
        limit_type: str, 
        current_value: float, 
        limit_value: float
    ) -> None:
        """Emit risk limit exceeded event."""
        await self.emit(
            EventType.RISK_LIMIT_EXCEEDED,
            {
                "limit_type": limit_type,
                "current_value": current_value,
                "limit_value": limit_value
            },
            source="risk_manager"
        )
    
    async def emit_emergency_stop(self, reason: str) -> None:
        """Emit emergency stop event."""
        await self.emit(
            EventType.EMERGENCY_STOP,
            {"reason": reason},
            source="risk_manager"
        )
