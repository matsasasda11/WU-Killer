# Web GUI Guide

## 🌐 Przegląd

Nowoczesny interfejs webowy dla Bybit Grid Trading Bot zapewnia intuicyjne zarządzanie i monitorowanie bota tradingowego w czasie rzeczywistym.

## 🚀 Uruchomienie

### Podstawowe uruchomienie
```bash
# Uruchomienie serwera web
make web

# Lub bezpośrednio
python web_server.py
```

### Tryb deweloperski
```bash
# Z auto-reload i debug
make web-dev

# Lub z parametrami
python web_server.py --reload --log-level DEBUG --host 0.0.0.0 --port 8080
```

### Dostęp do interfejsu
- **URL**: http://localhost:8000
- **Host**: Domyślnie 127.0.0.1 (localhost)
- **Port**: Domyślnie 8000

## 📊 Funkcje Interfejsu

### 1. Dashboard (Główny Panel)

**Metryki w czasie rzeczywistym:**
- Status bota (Running/Stopped)
- Całkowity PnL
- Współczynnik wygranych
- Aktywne poziomy siatki

**Wykresy:**
- Wykres wydajności portfela
- Metryki ryzyka
- Poziomy siatki

**Kontrola:**
- Start/Stop bota
- Emergency Stop
- Refresh danych

### 2. Configuration (Konfiguracja)

**Grid Trading:**
- Symbol handlowy
- Liczba poziomów siatki
- Zakres cenowy (min/max)
- Procent Take Profit
- Wielkość zlecenia

**Risk Management:**
- Maksymalna liczba pozycji
- Maksymalna ekspozycja
- Stop Loss
- Maksymalny drawdown
- Minimalny balans

**Technical:**
- Liczba prób ponowienia
- Timeout operacji
- Opóźnienie rate limit
- Precyzja ceny/ilości

### 3. Analytics (Analityka)

**Metryki wydajności:**
- Całkowity zwrot
- Sharpe Ratio
- Maksymalny drawdown
- Współczynnik wygranych

**Wykresy:**
- Wykres wydajności portfela
- Rozkład zysków
- Statystyki tradingu

**Statystyki siatki:**
- Ukończone cykle
- Aktywne poziomy
- Najlepszy poziom
- Efektywność siatki

### 4. Logs (Logi)

**Funkcje:**
- Podgląd logów w czasie rzeczywistym
- Filtrowanie po poziomie (DEBUG, INFO, WARNING, ERROR)
- Wyszukiwanie w logach
- Auto-refresh i auto-scroll
- Pobieranie logów

**Statystyki:**
- Liczba logów według typu
- Ostatnia aktualizacja
- Status połączenia

## 🔧 Architektura Techniczna

### Backend (FastAPI)

**Komponenty:**
- `web/app.py` - Główna aplikacja FastAPI
- `web/api.py` - Endpointy REST API
- `web/websocket.py` - WebSocket dla real-time updates
- `web_server.py` - Launcher serwera

**API Endpoints:**
```
GET  /api/v1/status          - Status bota
GET  /api/v1/performance     - Metryki wydajności
GET  /api/v1/grid-levels     - Poziomy siatki
POST /api/v1/start           - Start bota
POST /api/v1/stop            - Stop bota
POST /api/v1/emergency-stop  - Emergency stop
GET  /api/v1/config          - Konfiguracja
PUT  /api/v1/config/grid     - Aktualizacja konfiguracji siatki
PUT  /api/v1/config/risk     - Aktualizacja zarządzania ryzykiem
GET  /api/v1/portfolio       - Informacje o portfelu
GET  /api/v1/logs            - Logi systemu
WS   /api/v1/ws              - WebSocket connection
```

### Frontend (HTML/CSS/JavaScript)

**Technologie:**
- Bootstrap 5 - UI Framework
- Chart.js - Wykresy
- WebSocket - Real-time updates
- Vanilla JavaScript - Logika

**Szablony:**
- `base.html` - Szablon bazowy
- `dashboard.html` - Dashboard
- `config.html` - Konfiguracja
- `analytics.html` - Analityka
- `logs.html` - Logi

## 🔄 Real-time Updates

### WebSocket Events

**Zdarzenia systemowe:**
```javascript
{
  "type": "status_update",
  "data": { /* status data */ },
  "timestamp": "2024-01-15T10:30:45Z"
}
```

**Zdarzenia tradingowe:**
```javascript
{
  "type": "order_filled",
  "data": {
    "order_id": "123",
    "symbol": "BTCUSDT",
    "side": "sell",
    "quantity": 0.001,
    "price": 45000
  }
}
```

**Zdarzenia siatki:**
```javascript
{
  "type": "grid_cycle_completed",
  "data": {
    "level_id": 3,
    "profit": 0.05
  }
}
```

**Alerty ryzyka:**
```javascript
{
  "type": "risk_alert",
  "data": {
    "message": "High drawdown detected",
    "severity": "warning"
  }
}
```

## 🎨 Customizacja UI

### CSS Variables
```css
:root {
    --primary-color: #2563eb;
    --success-color: #10b981;
    --danger-color: #ef4444;
    --warning-color: #f59e0b;
}
```

### Responsive Design
- Mobile-first approach
- Breakpoints: 576px, 768px, 992px, 1200px
- Adaptive sidebar i navigation

### Dark Mode
- Automatyczne wykrywanie preferencji systemu
- CSS media queries: `@media (prefers-color-scheme: dark)`

## 🔒 Bezpieczeństwo

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Skonfiguruj dla produkcji
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Session Management
```python
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key"  # Zmień w produkcji
)
```

### API Security
- Walidacja danych wejściowych (Pydantic)
- Rate limiting (planowane)
- Authentication (planowane)

## 📱 Responsive Features

### Mobile Optimization
- Touch-friendly controls
- Swipe gestures
- Optimized charts
- Collapsible sidebar

### Tablet Support
- Adaptive layouts
- Touch interactions
- Optimized spacing

## 🔧 Konfiguracja Zaawansowana

### Environment Variables
```bash
# Web server configuration
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_RELOAD=false
WEB_LOG_LEVEL=INFO

# CORS settings
CORS_ORIGINS=["http://localhost:3000"]
```

### Custom Styling
```css
/* web/static/css/custom.css */
.custom-metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

### JavaScript Extensions
```javascript
// web/static/js/custom.js
class CustomDashboard extends Dashboard {
    // Rozszerzenia funkcjonalności
}
```

## 🚀 Deployment

### Development
```bash
# Local development
python web_server.py --reload --log-level DEBUG
```

### Production
```bash
# Production server
python web_server.py --host 0.0.0.0 --port 80
```

### Docker (planowane)
```dockerfile
FROM python:3.10-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["python", "web_server.py", "--host", "0.0.0.0"]
```

### Nginx Proxy (planowane)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/v1/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🐛 Troubleshooting

### Częste problemy

**1. WebSocket nie łączy się**
```bash
# Sprawdź czy serwer działa
curl http://localhost:8000/health

# Sprawdź logi
tail -f logs/web.log
```

**2. Błędy CORS**
```python
# Zaktualizuj konfigurację CORS w web/app.py
allow_origins=["http://localhost:3000"]
```

**3. Problemy z Chart.js**
```javascript
// Sprawdź czy Chart.js jest załadowany
console.log(typeof Chart);
```

**4. Błędy API**
```bash
# Sprawdź status API
curl http://localhost:8000/api/v1/status
```

### Debug Mode
```bash
# Uruchom z debugiem
python web_server.py --log-level DEBUG --reload
```

### Browser Console
```javascript
// Sprawdź połączenie WebSocket
console.log(window.dashboard.isConnected);

// Sprawdź ostatnie błędy
console.log(window.dashboard.lastError);
```

## 📈 Performance

### Optymalizacje
- Lazy loading komponentów
- Debounced updates
- Efficient chart rendering
- WebSocket connection pooling

### Monitoring
- Real-time connection status
- Performance metrics
- Error tracking
- User analytics (planowane)

## 🔮 Przyszłe Funkcje

### Planowane rozszerzenia
- [ ] Backtesting interface
- [ ] Strategy builder
- [ ] Multi-bot management
- [ ] Advanced charting
- [ ] Mobile app
- [ ] API documentation UI
- [ ] User authentication
- [ ] Role-based access
- [ ] Notification system
- [ ] Export/Import configs

### Integracje
- [ ] TradingView widgets
- [ ] Telegram notifications
- [ ] Discord webhooks
- [ ] Email alerts
- [ ] SMS notifications

## 💡 Tips & Tricks

### Keyboard Shortcuts
- `Ctrl + R` - Refresh data
- `Ctrl + S` - Save configuration
- `Esc` - Close modals
- `Space` - Start/Stop bot

### URL Parameters
```
http://localhost:8000/?timeframe=1h
http://localhost:8000/config?tab=risk
http://localhost:8000/analytics?export=true
```

### Browser Extensions
- Zalecane: Chrome DevTools
- WebSocket debugging
- Performance profiling

**Interfejs webowy zapewnia kompletne, profesjonalne środowisko do zarządzania botem tradingowym z intuicyjnym UI i zaawansowanymi funkcjami monitorowania! 🚀**
