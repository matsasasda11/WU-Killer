/**
 * Dashboard JavaScript functionality
 * Handles real-time updates, charts, and user interactions
 */

class Dashboard {
    constructor() {
        this.charts = {};
        this.websocket = null;
        this.updateInterval = null;
        this.isConnected = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.connectWebSocket();
        this.startPeriodicUpdates();
    }
    
    setupEventListeners() {
        // Refresh button
        document.getElementById('refresh-data')?.addEventListener('click', () => {
            this.loadAllData();
        });
        
        // Export button
        document.getElementById('export-data')?.addEventListener('click', () => {
            this.exportData();
        });
        
        // Timeframe selection
        document.querySelectorAll('input[name="timeframe"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.updatePerformanceChart();
            });
        });
        
        // Grid refresh
        document.getElementById('refresh-grid')?.addEventListener('click', () => {
            this.loadGridLevels();
        });
    }
    
    initializeCharts() {
        this.initPerformanceChart();
    }
    
    initPerformanceChart() {
        const ctx = document.getElementById('performance-chart');
        if (!ctx) return;
        
        this.charts.performance = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Portfolio Value',
                    data: [],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: '#2563eb',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return 'Value: $' + context.parsed.y.toFixed(2);
                            }
                        }
                    }
                },
                animation: {
                    duration: 750,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/v1/ws`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.updateConnectionStatus(true);
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus(false);
                
                // Attempt to reconnect after 3 seconds
                setTimeout(() => {
                    this.connectWebSocket();
                }, 3000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateConnectionStatus(false);
        }
    }
    
    handleWebSocketMessage(data) {
        switch(data.type) {
            case 'status_update':
                this.updateStatus(data.data);
                break;
            case 'performance_update':
                this.updatePerformance(data.data);
                break;
            case 'grid_levels_update':
                this.updateGridLevels(data.data);
                break;
            case 'order_filled':
                this.handleOrderFilled(data.data);
                break;
            case 'grid_cycle_completed':
                this.handleCycleCompleted(data.data);
                break;
            case 'risk_alert':
                this.handleRiskAlert(data.data);
                break;
            case 'emergency_stop':
                this.handleEmergencyStop(data.data);
                break;
            case 'notification':
                this.showNotification(data.message, data.notification_type);
                break;
        }
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (!statusElement) return;
        
        const indicator = statusElement.querySelector('.status-indicator');
        const text = statusElement.querySelector('.status-text');
        
        if (connected) {
            indicator.className = 'status-indicator status-running';
            text.textContent = 'Connected';
        } else {
            indicator.className = 'status-indicator status-stopped';
            text.textContent = 'Disconnected';
        }
    }
    
    async loadAllData() {
        try {
            await Promise.all([
                this.loadStatus(),
                this.loadPerformance(),
                this.loadGridLevels(),
                this.loadMarketData()
            ]);
        } catch (error) {
            console.error('Error loading data:', error);
            this.showNotification('Error loading dashboard data', 'danger');
        }
    }
    
    async loadStatus() {
        try {
            const response = await fetch('/api/v1/status');
            if (response.ok) {
                const data = await response.json();
                this.updateStatus(data);
            }
        } catch (error) {
            console.error('Error loading status:', error);
        }
    }
    
    async loadPerformance() {
        try {
            const response = await fetch('/api/v1/performance');
            if (response.ok) {
                const data = await response.json();
                this.updatePerformance(data);
            }
        } catch (error) {
            console.error('Error loading performance:', error);
        }
    }
    
    async loadGridLevels() {
        try {
            const response = await fetch('/api/v1/grid-levels');
            if (response.ok) {
                const data = await response.json();
                this.updateGridLevels(data);
            }
        } catch (error) {
            console.error('Error loading grid levels:', error);
        }
    }
    
    async loadMarketData() {
        try {
            // Get symbol from config
            const configResponse = await fetch('/api/v1/config');
            let symbol = 'BTCUSDT';
            if (configResponse.ok) {
                const config = await configResponse.json();
                symbol = config.trading?.symbol || 'BTCUSDT';
            }
            
            const response = await fetch(`/api/v1/market-data/${symbol}`);
            if (response.ok) {
                const data = await response.json();
                this.updateMarketData(data);
            }
        } catch (error) {
            console.error('Error loading market data:', error);
        }
    }
    
    updateStatus(data) {
        // Bot status
        this.updateElement('bot-status-text', data.is_running ? 'Running' : 'Stopped');
        this.updateElement('bot-uptime', `Uptime: ${this.formatUptime(data.uptime_seconds)}`);
        
        const statusIndicator = document.getElementById('bot-status-indicator');
        if (statusIndicator) {
            statusIndicator.className = data.is_running ? 
                'status-indicator status-running' : 
                'status-indicator status-stopped';
        }
        
        // Risk metrics
        if (data.risk_status) {
            this.updateRiskMetrics(data.risk_status);
        }
        
        // Grid status
        if (data.grid_status) {
            this.updateGridStatus(data.grid_status);
        }
    }
    
    updatePerformance(data) {
        this.updateElement('total-pnl', '$' + (data.total_pnl || 0).toFixed(2));
        this.updateElement('daily-pnl', 'Daily: $' + (data.daily_pnl || 0).toFixed(2));
        this.updateElement('win-rate', (data.win_rate || 0).toFixed(1) + '%');
        this.updateElement('total-trades', `Trades: ${data.total_trades || 0}`);
        
        // Update performance chart
        this.updatePerformanceChart();
    }
    
    updateGridLevels(data) {
        const container = document.getElementById('grid-levels-container');
        if (!container) return;
        
        if (!data || data.length === 0) {
            container.innerHTML = '<div class="text-center text-muted"><p>No grid levels configured</p></div>';
            return;
        }
        
        const html = data.map(level => this.createGridLevelHTML(level)).join('');
        container.innerHTML = html;
    }
    
    updateMarketData(data) {
        this.updateElement('market-symbol', data.symbol);
        this.updateElement('market-price', '$' + data.last_price.toFixed(2));
        this.updateElement('market-volume', data.volume_24h.toLocaleString());
        this.updateElement('market-bid', '$' + data.bid_price.toFixed(2));
        this.updateElement('market-ask', '$' + data.ask_price.toFixed(2));
        
        // Update price change with color
        const changeElement = document.getElementById('market-change');
        if (changeElement) {
            const change = data.price_change_24h;
            changeElement.textContent = (change > 0 ? '+' : '') + change.toFixed(2) + '%';
            changeElement.className = 'fw-bold ' + (change > 0 ? 'text-success' : change < 0 ? 'text-danger' : '');
        }
    }
    
    updateRiskMetrics(riskData) {
        this.updateElement('current-drawdown', riskData.current_drawdown.toFixed(2) + '%');
        this.updateElement('active-positions', `${riskData.current_positions}/${riskData.max_positions}`);
        
        // Update progress bars
        this.updateProgressBar('drawdown-progress', Math.min(riskData.current_drawdown, 100));
        
        const exposure = (riskData.current_exposure / riskData.max_exposure) * 100;
        this.updateElement('position-exposure', exposure.toFixed(1) + '%');
        this.updateProgressBar('exposure-progress', Math.min(exposure, 100));
        
        // Update risk status alert
        this.updateRiskAlert(riskData);
    }
    
    updateGridStatus(gridData) {
        const activeLevels = Object.values(gridData.status_counts)
            .reduce((sum, count) => sum + count, 0) - (gridData.status_counts.inactive || 0);
        
        this.updateElement('active-levels', activeLevels);
        this.updateElement('total-levels', `Total: ${gridData.total_levels}`);
    }
    
    async updatePerformanceChart() {
        const timeframe = document.querySelector('input[name="timeframe"]:checked')?.value || '24';
        
        try {
            const response = await fetch(`/api/v1/portfolio/chart-data?hours=${timeframe}`);
            if (response.ok) {
                const data = await response.json();
                
                const labels = data.map(point => {
                    const date = new Date(point.timestamp);
                    return timeframe <= 24 ? date.toLocaleTimeString() : date.toLocaleDateString();
                });
                
                const values = data.map(point => point.total_value);
                
                if (this.charts.performance) {
                    this.charts.performance.data.labels = labels;
                    this.charts.performance.data.datasets[0].data = values;
                    this.charts.performance.update('none');
                }
            }
        } catch (error) {
            console.error('Error updating performance chart:', error);
        }
    }
    
    // Event handlers
    handleOrderFilled(data) {
        this.showNotification(`Order filled: ${data.symbol} ${data.side} ${data.quantity}`, 'success');
        this.addRecentActivity(`Order filled: ${data.symbol}`, 'success');
    }
    
    handleCycleCompleted(data) {
        this.showNotification(`Grid cycle completed: Level ${data.level_id}`, 'success');
        this.addRecentActivity(`Cycle completed: Level ${data.level_id}, Profit: $${data.profit}`, 'success');
    }
    
    handleRiskAlert(data) {
        this.showNotification(`Risk Alert: ${data.message}`, 'warning');
        this.addRecentActivity(`Risk Alert: ${data.message}`, 'warning');
    }
    
    handleEmergencyStop(data) {
        this.showNotification('Emergency Stop Triggered!', 'danger');
        this.addRecentActivity('Emergency Stop Triggered!', 'danger');
    }
    
    // Utility methods
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    updateProgressBar(id, percentage) {
        const element = document.getElementById(id);
        if (element) {
            element.style.width = percentage + '%';
        }
    }
    
    formatUptime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
    
    createGridLevelHTML(level) {
        const statusClass = this.getGridLevelStatusClass(level.status);
        const statusIcon = this.getGridLevelStatusIcon(level.status);
        
        return `
            <div class="grid-level-card card mb-2 ${statusClass}">
                <div class="card-body py-2">
                    <div class="row align-items-center">
                        <div class="col-2">
                            <strong>L${level.level_id}</strong>
                        </div>
                        <div class="col-3">
                            <small class="text-muted">Price</small><br>
                            <strong>$${level.price}</strong>
                        </div>
                        <div class="col-3">
                            <small class="text-muted">TP</small><br>
                            <strong>$${level.tp_price}</strong>
                        </div>
                        <div class="col-2">
                            <small class="text-muted">Qty</small><br>
                            <strong>${level.quantity}</strong>
                        </div>
                        <div class="col-2 text-end">
                            ${statusIcon}
                            <small class="d-block text-muted">${level.status}</small>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    getGridLevelStatusClass(status) {
        const statusMap = {
            'inactive': 'grid-level-inactive',
            'sell_pending': 'grid-level-active',
            'sell_filled': 'grid-level-filled',
            'waiting_tp': 'grid-level-waiting',
            'buy_pending': 'grid-level-active',
            'buy_filled': 'grid-level-filled'
        };
        return statusMap[status] || 'grid-level-inactive';
    }
    
    getGridLevelStatusIcon(status) {
        const iconMap = {
            'inactive': '<i class="bi bi-circle text-muted"></i>',
            'sell_pending': '<i class="bi bi-arrow-up-circle text-primary"></i>',
            'sell_filled': '<i class="bi bi-check-circle text-success"></i>',
            'waiting_tp': '<i class="bi bi-clock text-warning"></i>',
            'buy_pending': '<i class="bi bi-arrow-down-circle text-primary"></i>',
            'buy_filled': '<i class="bi bi-check-circle text-success"></i>'
        };
        return iconMap[status] || '<i class="bi bi-circle text-muted"></i>';
    }
    
    updateRiskAlert(riskData) {
        const alertElement = document.getElementById('risk-status');
        if (!alertElement) return;
        
        if (riskData.emergency_stop) {
            alertElement.className = 'alert alert-custom alert-danger border-danger';
            alertElement.innerHTML = '<i class="bi bi-exclamation-triangle me-2"></i>Emergency stop active!';
        } else if (riskData.current_drawdown > 5) {
            alertElement.className = 'alert alert-custom alert-warning border-warning';
            alertElement.innerHTML = '<i class="bi bi-exclamation-triangle me-2"></i>High drawdown detected';
        } else {
            alertElement.className = 'alert alert-custom alert-info border-info';
            alertElement.innerHTML = '<i class="bi bi-info-circle me-2"></i>Risk levels normal';
        }
    }
    
    addRecentActivity(message, type) {
        // Implementation for recent activity updates
        const container = document.getElementById('recent-activity');
        if (!container) return;
        
        const timestamp = new Date().toLocaleTimeString();
        const badgeClass = type === 'success' ? 'bg-success' : 
                          type === 'warning' ? 'bg-warning' : 
                          type === 'danger' ? 'bg-danger' : 'bg-primary';
        
        const activityHTML = `
            <div class="d-flex justify-content-between align-items-start mb-2 fade-in">
                <div>
                    <span class="badge ${badgeClass} me-2">${type}</span>
                    <span>${message}</span>
                </div>
                <small class="text-muted">${timestamp}</small>
            </div>
        `;
        
        container.insertAdjacentHTML('afterbegin', activityHTML);
        
        // Keep only last 10 activities
        const activities = container.querySelectorAll('.d-flex');
        if (activities.length > 10) {
            activities[activities.length - 1].remove();
        }
    }
    
    showNotification(message, type = 'info') {
        // This will be handled by the base template's notification system
        if (window.showNotification) {
            window.showNotification(message, type);
        }
    }
    
    exportData() {
        // Export dashboard data as CSV
        const data = [
            ['Metric', 'Value'],
            ['Bot Status', document.getElementById('bot-status-text')?.textContent || ''],
            ['Total PnL', document.getElementById('total-pnl')?.textContent || ''],
            ['Win Rate', document.getElementById('win-rate')?.textContent || ''],
            ['Active Levels', document.getElementById('active-levels')?.textContent || ''],
            ['Current Drawdown', document.getElementById('current-drawdown')?.textContent || '']
        ];
        
        const csvContent = data.map(row => row.join(',')).join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `dashboard_export_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        this.showNotification('Dashboard data exported successfully', 'success');
    }
    
    startPeriodicUpdates() {
        // Update data every 30 seconds if WebSocket is not connected
        this.updateInterval = setInterval(() => {
            if (!this.isConnected) {
                this.loadAllData();
            }
        }, 30000);
    }
    
    destroy() {
        // Cleanup
        if (this.websocket) {
            this.websocket.close();
        }
        
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.dashboard) {
        window.dashboard.destroy();
    }
});
