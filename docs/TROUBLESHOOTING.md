# Rozwiązywanie Problemów

## 🚨 Częste Problemy

### 1. Błędy Połączenia z API

#### Problem: "Failed to connect to Bybit API"
**Przyczyny:**
- Nieprawidłowe klucze API
- Brak połączenia internetowego
- Problemy z serwerami Bybit
- Blokada przez firewall

**Rozwiązania:**
```bash
# Sprawdź klucze API
python -c "
from utils.config import load_config
config = load_config()
print(f'API Key: {config.api_key[:8]}...')
print(f'Testnet: {config.testnet}')
"

# Test połączenia
python -c "
import asyncio
from api import BybitClient
async def test():
    client = BybitClient('key', 'secret', testnet=True)
    try:
        await client.connect()
        print('Connection successful')
    except Exception as e:
        print(f'Connection failed: {e}')
asyncio.run(test())
"
```

#### Problem: "Rate limit exceeded"
**Rozwiązania:**
- Zwiększ `rate_limit_delay` w konfiguracji
- Zmniejsz częstotliwość aktualizacji
- Sprawdź czy nie masz innych aplikacji używających API

```yaml
technical:
  rate_limit_delay: 0.5  # Zwiększ z 0.1 do 0.5
  update_interval: 2.0   # Zwiększ interwał aktualizacji
```

### 2. Problemy z Zleceniami

#### Problem: "Insufficient balance"
**Przyczyny:**
- Za mało środków na koncie
- Środki zablokowane w innych zleceniach
- Nieprawidłowa kalkulacja wielkości pozycji

**Rozwiązania:**
```python
# Sprawdź saldo
python main.py --mode status

# Zmniejsz wielkość zleceń
# W config/config.yaml:
trading:
  order_size: 0.0005  # Zmniejsz z 0.001
```

#### Problem: "Order rejected"
**Przyczyny:**
- Cena poza dozwolonym zakresem
- Minimalna wielkość zlecenia nie spełniona
- Symbol nie jest dostępny

**Rozwiązania:**
```python
# Sprawdź informacje o symbolu
import ccxt
exchange = ccxt.bybit({'sandbox': True})
markets = exchange.load_markets()
print(markets['BTC/USDT'])
```

### 3. Problemy ze Strategią

#### Problem: "Grid levels not activating"
**Przyczyny:**
- Cena rynkowa poza zakresem siatki
- Wszystkie poziomy już aktywne
- Limity ryzyka blokują nowe pozycje

**Diagnostyka:**
```bash
python main.py --mode status
```

**Rozwiązania:**
```yaml
# Dostosuj zakres siatki
trading:
  price_range:
    min: 42000.0  # Bliżej aktualnej ceny
    max: 48000.0

# Zwiększ limity ryzyka
risk_management:
  max_positions: 10  # Zwiększ z 5
  max_exposure: 0.2  # Zwiększ z 0.1
```

#### Problem: "Take Profit not triggering"
**Przyczyny:**
- TP poziom za daleko od ceny rynkowej
- Niska volatilność
- Błędna kalkulacja TP

**Rozwiązania:**
```yaml
trading:
  tp_percentage: 0.3  # Zmniejsz z 0.5 dla częstszych TP
```

### 4. Problemy z Performance

#### Problem: "High memory usage"
**Przyczyny:**
- Za dużo historii zdarzeń
- Wyciek pamięci w logach
- Za dużo snapshots portfela

**Rozwiązania:**
```python
# W core/event_handler.py
handler = EventHandler(max_history=500)  # Zmniejsz z 1000

# W core/portfolio_manager.py
portfolio = PortfolioManager(snapshot_interval=600)  # Zwiększ z 300
```

#### Problem: "Slow execution"
**Przyczyny:**
- Za częste aktualizacje
- Synchroniczne operacje
- Problemy z siecią

**Rozwiązania:**
```yaml
trading:
  update_interval: 2.0  # Zwiększ z 1.0

technical:
  timeout_seconds: 60   # Zwiększ z 30
```

## 🔧 Narzędzia Diagnostyczne

### 1. Sprawdzenie Konfiguracji

```bash
python -c "
from utils.config import load_config, validate_config
try:
    config = load_config()
    validate_config(config)
    print('✓ Configuration is valid')
except Exception as e:
    print(f'✗ Configuration error: {e}')
"
```

### 2. Test Połączenia API

```bash
python -c "
import asyncio
from api import BybitClient
from utils.config import load_config

async def test_api():
    config = load_config()
    client = BybitClient(config.api_key, config.api_secret, config.testnet)
    
    try:
        await client.connect()
        balance = await client.get_balance()
        market_data = await client.get_market_data('BTC/USDT')
        print(f'✓ API connection successful')
        print(f'Balance: {balance.available_balance} USDT')
        print(f'BTC Price: {market_data.last_price}')
    except Exception as e:
        print(f'✗ API test failed: {e}')
    finally:
        await client.disconnect()

asyncio.run(test_api())
"
```

### 3. Test Strategii

```bash
python -c "
import asyncio
from decimal import Decimal
from strategy.grid_strategy import GridConfig
from utils.helpers import calculate_grid_levels, validate_grid_configuration

config = GridConfig(
    symbol='BTCUSDT',
    min_price=Decimal('40000'),
    max_price=Decimal('50000'),
    num_levels=10,
    tp_percentage=Decimal('0.5'),
    order_size=Decimal('0.001')
)

try:
    validate_grid_configuration(
        config.min_price,
        config.max_price,
        config.num_levels,
        config.tp_percentage,
        config.order_size
    )
    
    levels = calculate_grid_levels(
        config.min_price,
        config.max_price,
        config.num_levels
    )
    
    print('✓ Grid configuration is valid')
    print(f'Grid levels: {len(levels)}')
    print(f'Price range: {levels[0]} - {levels[-1]}')
    
except Exception as e:
    print(f'✗ Grid configuration error: {e}')
"
```

## 📊 Monitoring i Logi

### 1. Poziomy Logowania

```bash
# Debug - wszystkie szczegóły
python main.py --log-level DEBUG

# Info - standardowe informacje
python main.py --log-level INFO

# Warning - tylko ostrzeżenia i błędy
python main.py --log-level WARNING

# Error - tylko błędy
python main.py --log-level ERROR
```

### 2. Analiza Logów

```bash
# Ostatnie błędy
tail -f logs/trading.log | grep ERROR

# Statystyki zleceń
grep "TRADE" logs/trading.log | tail -20

# Aktualizacje siatki
grep "GRID UPDATE" logs/trading.log | tail -10

# Zdarzenia ryzyka
grep "RISK EVENT" logs/trading.log
```

### 3. Monitoring w Czasie Rzeczywistym

```bash
# Status co 30 sekund
watch -n 30 "python main.py --mode status"

# Monitoring logów
tail -f logs/trading.log | grep -E "(ERROR|WARNING|TRADE|GRID)"
```

## 🚨 Sytuacje Awaryjne

### 1. Awaryjne Zatrzymanie

```bash
# Natychmiastowe zatrzymanie
python main.py --mode stop

# Sprawdzenie czy zatrzymane
python main.py --mode status

# Reset po zatrzymaniu
python main.py --mode reset
```

### 2. Anulowanie Wszystkich Zleceń

```python
import asyncio
from api import BybitClient
from utils.config import load_config

async def cancel_all_orders():
    config = load_config()
    client = BybitClient(config.api_key, config.api_secret, config.testnet)
    
    try:
        await client.connect()
        # Pobierz wszystkie otwarte zlecenia
        orders = await client.fetch_open_orders('BTC/USDT')
        
        for order in orders:
            await client.cancel_order(order['id'], 'BTC/USDT')
            print(f"Cancelled order: {order['id']}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()

asyncio.run(cancel_all_orders())
```

### 3. Backup Konfiguracji

```bash
# Backup aktualnej konfiguracji
cp config/config.yaml config/config_backup_$(date +%Y%m%d_%H%M%S).yaml

# Przywrócenie domyślnej konfiguracji
cp config/config.yaml.example config/config.yaml
```

## 🔍 Debugowanie Krok po Kroku

### 1. Sprawdź Podstawy

```bash
# 1. Python version
python --version  # Powinno być 3.10+

# 2. Zainstalowane pakiety
pip list | grep -E "(ccxt|pydantic|loguru|pytest)"

# 3. Struktura plików
ls -la config/
ls -la logs/
```

### 2. Sprawdź Konfigurację

```bash
# 1. Zmienne środowiskowe
python -c "
import os
print('API_KEY:', os.getenv('BYBIT_API_KEY', 'Not set')[:8] + '...')
print('TESTNET:', os.getenv('BYBIT_TESTNET', 'Not set'))
"

# 2. Plik konfiguracyjny
python -c "
import yaml
with open('config/config.yaml') as f:
    config = yaml.safe_load(f)
    print('Symbol:', config['trading']['symbol'])
    print('Grid levels:', config['trading']['grid_levels'])
"
```

### 3. Test Komponentów

```bash
# 1. Test API
python -c "
import asyncio
from api import BybitClient
from utils.config import load_config

async def test():
    config = load_config()
    client = BybitClient(config.api_key, config.api_secret, True)
    await client.connect()
    print('✓ API OK')
    await client.disconnect()

asyncio.run(test())
"

# 2. Test strategii
python -c "
from strategy.grid_strategy import GridConfig
from decimal import Decimal

config = GridConfig(
    symbol='BTCUSDT',
    min_price=Decimal('40000'),
    max_price=Decimal('50000'),
    num_levels=5,
    tp_percentage=Decimal('0.5'),
    order_size=Decimal('0.001')
)
print('✓ Strategy config OK')
"
```

## 📞 Gdzie Szukać Pomocy

### 1. Dokumentacja
- `README.md` - Podstawowe informacje
- `docs/STRATEGY_GUIDE.md` - Przewodnik strategii
- `docs/API_REFERENCE.md` - Dokumentacja API

### 2. Logi i Diagnostyka
- `logs/trading.log` - Główny plik logów
- `python main.py --mode status` - Aktualny status
- `pytest tests/ -v` - Uruchomienie testów

### 3. Społeczność
- GitHub Issues
- Discord serwery o algo trading
- Reddit: r/algotrading

### 4. Bybit Resources
- [Bybit API Documentation](https://bybit-exchange.github.io/docs/)
- [Bybit Testnet](https://testnet.bybit.com/)
- [Bybit API Status](https://bybit-exchange.github.io/docs/spot/#t-introduction)

## 🛡️ Najlepsze Praktyki

### 1. Przed Uruchomieniem
- Zawsze testuj na testnet
- Sprawdź wszystkie parametry
- Uruchom testy jednostkowe
- Przygotuj plan awaryjny

### 2. Podczas Działania
- Monitoruj logi regularnie
- Sprawdzaj metryki wydajności
- Miej gotowy plan stop loss
- Nie zostawiaj bez nadzoru

### 3. Po Problemach
- Zapisz logi przed restartowaniem
- Przeanalizuj przyczyny
- Dostosuj parametry
- Przetestuj zmiany

### 4. Bezpieczeństwo
- Używaj tylko niezbędnych uprawnień API
- Regularnie zmieniaj klucze API
- Nie udostępniaj kluczy
- Używaj 2FA na koncie Bybit

**Pamiętaj: Lepiej zatrzymać bota i stracić potencjalny zysk niż kontynuować i stracić kapitał!**
