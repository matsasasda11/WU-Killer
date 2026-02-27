# API Reference

## 📚 Przegląd Modułów

### api/
Moduły integracji z Bybit API

### strategy/
Moduły strategii tradingowej

### core/
Główne moduły aplikacji

### utils/
Narzędzia pomocnicze

---

## 🔌 api.bybit_client

### BybitClient

Główny klient do komunikacji z Bybit API.

```python
from api import BybitClient

client = BybitClient(
    api_key="your_key",
    api_secret="your_secret",
    testnet=True
)
```

#### Metody

**`async connect() -> None`**
Nawiązuje połączenie z API.

**`async disconnect() -> None`**
Zamyka połączenie z API.

**`async get_balance(coin: str = "USDT") -> Balance`**
Pobiera saldo konta.

**`async get_market_data(symbol: str) -> MarketData`**
Pobiera dane rynkowe dla symbolu.

**`async place_order(symbol: str, side: OrderSide, order_type: OrderType, quantity: Decimal, price: Optional[Decimal] = None) -> Order`**
Składa zlecenie.

**`async cancel_order(order_id: str, symbol: str) -> bool`**
Anuluje zlecenie.

**`async get_order_status(order_id: str, symbol: str) -> Order`**
Pobiera status zlecenia.

---

## 📊 api.models

### Order

Model zlecenia.

```python
from api.models import Order, OrderSide, OrderType, OrderStatus

order = Order(
    order_id="123",
    symbol="BTCUSDT",
    side=OrderSide.BUY,
    order_type=OrderType.LIMIT,
    quantity=Decimal("0.001"),
    price=Decimal("45000"),
    status=OrderStatus.NEW,
    created_time=datetime.now()
)
```

#### Pola
- `order_id: str` - ID zlecenia
- `symbol: str` - Symbol pary
- `side: OrderSide` - Strona zlecenia (BUY/SELL)
- `order_type: OrderType` - Typ zlecenia (LIMIT/MARKET)
- `quantity: Decimal` - Ilość
- `price: Decimal` - Cena
- `status: OrderStatus` - Status zlecenia
- `filled_quantity: Decimal` - Wykonana ilość
- `average_price: Optional[Decimal]` - Średnia cena wykonania
- `created_time: datetime` - Czas utworzenia
- `updated_time: Optional[datetime]` - Czas aktualizacji

### GridLevel

Model poziomu siatki.

```python
from api.models import GridLevel, GridLevelStatus

level = GridLevel(
    level_id=0,
    price=Decimal("45000"),
    tp_price=Decimal("44775"),
    quantity=Decimal("0.001"),
    status=GridLevelStatus.INACTIVE
)
```

#### Pola
- `level_id: int` - ID poziomu
- `price: Decimal` - Cena poziomu
- `tp_price: Decimal` - Cena Take Profit
- `quantity: Decimal` - Ilość zlecenia
- `status: GridLevelStatus` - Status poziomu
- `sell_order_id: Optional[str]` - ID zlecenia sprzedaży
- `buy_order_id: Optional[str]` - ID zlecenia kupna
- `created_time: datetime` - Czas utworzenia
- `last_updated: datetime` - Ostatnia aktualizacja

### Balance

Model salda konta.

```python
from api.models import Balance

balance = Balance(
    coin="USDT",
    wallet_balance=Decimal("1000"),
    available_balance=Decimal("900"),
    locked_balance=Decimal("100")
)
```

---

## 🎯 strategy.grid_strategy

### GridStrategy

Główna klasa strategii grid trading.

```python
from strategy import GridStrategy
from strategy.grid_strategy import GridConfig

config = GridConfig(
    symbol="BTCUSDT",
    min_price=Decimal("40000"),
    max_price=Decimal("50000"),
    num_levels=10,
    tp_percentage=Decimal("0.5"),
    order_size=Decimal("0.001")
)

strategy = GridStrategy(
    client=client,
    order_manager=order_manager,
    risk_manager=risk_manager,
    config=config
)
```

#### Metody

**`async initialize_grid() -> bool`**
Inicjalizuje poziomy siatki.

**`async start() -> None`**
Uruchamia strategię.

**`async stop() -> None`**
Zatrzymuje strategię.

**`get_grid_status() -> Dict[str, any]`**
Zwraca status siatki.

**`get_grid_levels_info() -> List[Dict[str, any]]`**
Zwraca informacje o poziomach siatki.

**`async force_reset_level(level_id: int) -> bool`**
Wymusza reset poziomu siatki.

**`get_performance_summary() -> Dict[str, any]`**
Zwraca podsumowanie wydajności.

---

## 📋 strategy.order_manager

### OrderManager

Zarządza zleceniami.

```python
from strategy import OrderManager

manager = OrderManager(
    client=client,
    max_retry_attempts=3,
    retry_delay=1.0,
    order_timeout=300
)
```

#### Metody

**`async place_order(symbol: str, side: OrderSide, quantity: Decimal, price: Decimal, order_id: Optional[str] = None) -> Optional[Order]`**
Składa zlecenie z logiką ponawiania.

**`async cancel_order(order_id: str, symbol: str) -> bool`**
Anuluje zlecenie.

**`async update_order_status(order_id: str, symbol: str) -> Optional[Order]`**
Aktualizuje status zlecenia.

**`async update_all_orders(symbol: str) -> None`**
Aktualizuje wszystkie aktywne zlecenia.

**`get_active_orders(status_filter: Optional[OrderStatus] = None) -> List[Order]`**
Zwraca listę aktywnych zleceń.

**`get_statistics() -> Dict[str, int]`**
Zwraca statystyki zarządzania zleceniami.

---

## ⚠️ strategy.risk_manager

### RiskManager

Zarządza ryzykiem.

```python
from strategy import RiskManager
from strategy.risk_manager import RiskLimits

limits = RiskLimits(
    max_positions=5,
    max_exposure=Decimal("0.1"),
    stop_loss_percentage=Decimal("5.0"),
    max_drawdown=Decimal("10.0")
)

risk_manager = RiskManager(limits)
```

#### Metody

**`can_open_position(position_size: Decimal, position_value: Decimal, current_balance: Decimal) -> Tuple[bool, str]`**
Sprawdza czy można otworzyć pozycję.

**`update_balance(balance: Balance) -> None`**
Aktualizuje saldo i metryki ryzyka.

**`record_trade(entry_price: Decimal, exit_price: Decimal, quantity: Decimal, side: str) -> None`**
Rejestruje wykonaną transakcję.

**`check_stop_loss(current_balance: Decimal) -> bool`**
Sprawdza czy stop loss powinien być uruchomiony.

**`get_risk_status() -> Dict[str, any]`**
Zwraca aktualny status ryzyka.

**`reset_emergency_stop() -> None`**
Resetuje awaryjne zatrzymanie.

---

## 🏗️ core.trading_engine

### TradingEngine

Główny silnik tradingowy.

```python
from core import TradingEngine

engine = TradingEngine(config_path="config/config.yaml")
```

#### Metody

**`async initialize() -> bool`**
Inicjalizuje wszystkie komponenty.

**`async start() -> None`**
Uruchamia silnik tradingowy.

**`async stop() -> None`**
Zatrzymuje silnik tradingowy.

**`get_status() -> Dict[str, Any]`**
Zwraca status silnika.

**`get_performance_summary() -> Dict[str, Any]`**
Zwraca podsumowanie wydajności.

**`async emergency_stop(reason: str = "Manual emergency stop") -> None`**
Awaryjne zatrzymanie.

**`async reset_emergency_stop() -> None`**
Reset awaryjnego zatrzymania.

---

## 🎪 core.event_handler

### EventHandler

System obsługi zdarzeń.

```python
from core import EventHandler, EventType

handler = EventHandler()

# Subskrypcja zdarzeń
async def on_order_filled(event):
    print(f"Order filled: {event.data}")

handler.subscribe(EventType.ORDER_FILLED, on_order_filled)

# Emitowanie zdarzeń
await handler.emit(
    EventType.ORDER_FILLED,
    {"order_id": "123", "symbol": "BTCUSDT"},
    source="order_manager"
)
```

#### Metody

**`subscribe(event_type: EventType, callback: Callable) -> None`**
Subskrybuje zdarzenie.

**`unsubscribe(event_type: EventType, callback: Callable) -> bool`**
Anuluje subskrypcję.

**`async emit(event_type: EventType, data: Dict[str, Any], source: str = "unknown") -> None`**
Emituje zdarzenie.

**`get_event_history(event_type: Optional[EventType] = None, limit: Optional[int] = None) -> List[Event]`**
Zwraca historię zdarzeń.

---

## 💼 core.portfolio_manager

### PortfolioManager

Zarządza portfelem i metrykami wydajności.

```python
from core import PortfolioManager

portfolio = PortfolioManager(
    client=client,
    event_handler=event_handler,
    base_currency="USDT"
)
```

#### Metody

**`async start() -> None`**
Uruchamia monitorowanie portfela.

**`async stop() -> None`**
Zatrzymuje monitorowanie.

**`get_portfolio_summary() -> Dict[str, any]`**
Zwraca podsumowanie portfela.

**`get_snapshots(limit: Optional[int] = None) -> List[Dict[str, any]]`**
Zwraca migawki portfela.

**`get_performance_chart_data(hours: int = 24) -> List[Dict[str, any]]`**
Zwraca dane do wykresów wydajności.

---

## ⚙️ utils.config

### Config

Zarządzanie konfiguracją.

```python
from utils.config import load_config, validate_config

config = load_config("config/config.yaml")
validate_config(config)
```

#### Funkcje

**`load_config(config_path: Optional[str] = None) -> Config`**
Ładuje konfigurację z pliku i zmiennych środowiskowych.

**`save_config(config: Config, config_path: Optional[str] = None) -> None`**
Zapisuje konfigurację do pliku.

**`validate_config(config: Config) -> bool`**
Waliduje konfigurację.

---

## 📝 utils.logger

### Logging

System logowania.

```python
from utils.logger import setup_logger, get_logger, LoggerMixin

# Konfiguracja
setup_logger(
    log_level="INFO",
    log_file="logs/trading.log"
)

# Użycie
logger = get_logger("MyModule")
logger.info("Message")

# Mixin dla klas
class MyClass(LoggerMixin):
    def method(self):
        self.logger.info("Method called")
```

#### Funkcje

**`setup_logger(log_level: str = "INFO", log_file: Optional[str] = None, ...) -> None`**
Konfiguruje system logowania.

**`get_logger(name: str)`**
Zwraca instancję loggera.

**`log_trade_execution(action: str, symbol: str, side: str, quantity: float, price: float, order_id: str = None) -> None`**
Loguje wykonanie transakcji.

**`log_grid_update(level_id: int, status: str, price: float, tp_price: float) -> None`**
Loguje aktualizację poziomu siatki.

---

## 🔧 utils.helpers

### Helper Functions

Funkcje pomocnicze.

```python
from utils.helpers import (
    calculate_grid_levels,
    calculate_tp_price,
    round_price,
    round_quantity,
    retry_async
)

# Kalkulacja poziomów siatki
levels = calculate_grid_levels(
    min_price=Decimal("40000"),
    max_price=Decimal("50000"),
    num_levels=10,
    spacing_mode="linear"
)

# Kalkulacja TP
tp_price = calculate_tp_price(
    grid_price=Decimal("45000"),
    tp_percentage=Decimal("0.5")
)

# Retry z backoff
result = await retry_async(
    func=some_async_function,
    max_attempts=3,
    delay=1.0,
    backoff_factor=2.0
)
```

---

## ✅ utils.validators

### Validation Functions

Funkcje walidacji.

```python
from utils.validators import (
    validate_symbol,
    validate_price,
    validate_quantity,
    validate_price_range,
    validate_api_credentials
)

# Walidacja symbolu
validate_symbol("BTCUSDT")  # True

# Walidacja ceny
price = validate_price("45000.50")  # Decimal("45000.50")

# Walidacja zakresu
min_price, max_price = validate_price_range("40000", "50000")
```

---

## 🚨 Obsługa Błędów

### Wyjątki API

```python
from api.exceptions import (
    BybitAPIError,
    OrderError,
    InsufficientBalanceError,
    RateLimitError,
    ConnectionError
)

try:
    await client.place_order(...)
except InsufficientBalanceError:
    logger.error("Insufficient balance")
except RateLimitError:
    logger.error("Rate limit exceeded")
except BybitAPIError as e:
    logger.error(f"API error: {e}")
```

### Kody Błędów

- `BybitAPIError` - Ogólny błąd API
- `OrderError` - Błąd zlecenia
- `InsufficientBalanceError` - Niewystarczające saldo
- `RateLimitError` - Przekroczenie limitu zapytań
- `ConnectionError` - Błąd połączenia
- `ValidationError` - Błąd walidacji
- `PositionError` - Błąd pozycji
- `MarketDataError` - Błąd danych rynkowych

---

## 📊 Typy Danych

### Enums

```python
from api.models import OrderSide, OrderType, OrderStatus, GridLevelStatus

# Strony zleceń
OrderSide.BUY
OrderSide.SELL

# Typy zleceń
OrderType.LIMIT
OrderType.MARKET

# Statusy zleceń
OrderStatus.NEW
OrderStatus.FILLED
OrderStatus.CANCELLED

# Statusy poziomów siatki
GridLevelStatus.INACTIVE
GridLevelStatus.SELL_PENDING
GridLevelStatus.WAITING_TP
GridLevelStatus.BUY_PENDING
```

### Decimal Precision

Wszystkie wartości finansowe używają `Decimal` dla precyzji:

```python
from decimal import Decimal

price = Decimal("45000.50")
quantity = Decimal("0.001")
```

---

## 🔗 Przykłady Użycia

### Podstawowe Użycie

```python
import asyncio
from core import TradingEngine

async def main():
    engine = TradingEngine("config/config.yaml")
    
    if await engine.initialize():
        await engine.start()
    else:
        print("Failed to initialize")

asyncio.run(main())
```

### Niestandardowa Strategia

```python
from strategy import GridStrategy
from strategy.grid_strategy import GridConfig

config = GridConfig(
    symbol="ETHUSDT",
    min_price=Decimal("2000"),
    max_price=Decimal("3000"),
    num_levels=15,
    tp_percentage=Decimal("0.3"),
    order_size=Decimal("0.01")
)

strategy = GridStrategy(client, order_manager, risk_manager, config)
await strategy.start()
```

### Monitoring Zdarzeń

```python
from core import EventHandler, EventType

handler = EventHandler()

async def on_cycle_completed(event):
    data = event.data
    print(f"Cycle completed: Level {data['level_id']}, Profit: {data['profit']}")

handler.subscribe(EventType.GRID_CYCLE_COMPLETED, on_cycle_completed)
await handler.start()
```
