"""
Configuration management for the grid trading application.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv


class TradingConfig(BaseModel):
    """Trading configuration model."""
    symbol: str = "BTCUSDT"
    grid_levels: int = Field(default=10, ge=2, le=50)
    price_range: Dict[str, float] = Field(default={"min": 40000.0, "max": 50000.0})
    tp_percentage: float = Field(default=0.5, ge=0.1, le=5.0)
    tp_mode: str = Field(default="fixed", regex="^(fixed|dynamic)$")
    order_size: float = Field(default=0.001, gt=0)
    grid_spacing: str = "auto"
    update_interval: float = Field(default=1.0, ge=0.1)
    order_timeout: int = Field(default=300, ge=60)
    
    @validator('price_range')
    def validate_price_range(cls, v):
        if v['min'] >= v['max']:
            raise ValueError("min price must be less than max price")
        return v


class RiskManagementConfig(BaseModel):
    """Risk management configuration model."""
    max_positions: int = Field(default=5, ge=1, le=20)
    max_exposure: float = Field(default=0.1, ge=0.01, le=1.0)
    stop_loss_percentage: float = Field(default=5.0, ge=1.0, le=20.0)
    max_drawdown: float = Field(default=10.0, ge=1.0, le=50.0)
    min_balance: float = Field(default=100.0, gt=0)
    emergency_stop_loss: float = Field(default=15.0, ge=5.0, le=50.0)
    max_daily_trades: int = Field(default=100, ge=10, le=1000)


class TechnicalConfig(BaseModel):
    """Technical configuration model."""
    retry_attempts: int = Field(default=3, ge=1, le=10)
    timeout_seconds: int = Field(default=30, ge=5, le=120)
    rate_limit_delay: float = Field(default=0.1, ge=0.01, le=1.0)
    ws_reconnect_attempts: int = Field(default=5, ge=1, le=20)
    ws_ping_interval: int = Field(default=30, ge=10, le=300)
    price_precision: int = Field(default=2, ge=0, le=8)
    quantity_precision: int = Field(default=6, ge=0, le=8)


class LoggingConfig(BaseModel):
    """Logging configuration model."""
    level: str = Field(default="INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    rotation: str = "1 day"
    retention: str = "30 days"


class NotificationsConfig(BaseModel):
    """Notifications configuration model."""
    enabled: bool = False
    telegram: Dict[str, bool] = Field(default={"enabled": False})
    email: Dict[str, bool] = Field(default={"enabled": False})


class Config(BaseModel):
    """Main configuration model."""
    trading: TradingConfig = Field(default_factory=TradingConfig)
    risk_management: RiskManagementConfig = Field(default_factory=RiskManagementConfig)
    technical: TechnicalConfig = Field(default_factory=TechnicalConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
    
    # Environment variables
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    testnet: bool = True
    log_level: str = "INFO"
    log_file: str = "logs/trading.log"
    
    class Config:
        env_prefix = "BYBIT_"


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from YAML file and environment variables.
    
    Args:
        config_path: Path to configuration file (default: config/config.yaml)
        
    Returns:
        Config object
    """
    # Load environment variables
    load_dotenv()
    
    # Default config path
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    
    # Load YAML configuration
    config_data = {}
    if Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}
    
    # Override with environment variables
    env_overrides = {
        'api_key': os.getenv('BYBIT_API_KEY'),
        'api_secret': os.getenv('BYBIT_API_SECRET'),
        'testnet': os.getenv('BYBIT_TESTNET', 'true').lower() == 'true',
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'log_file': os.getenv('LOG_FILE', 'logs/trading.log')
    }
    
    # Remove None values
    env_overrides = {k: v for k, v in env_overrides.items() if v is not None}
    
    # Merge configurations
    config_data.update(env_overrides)
    
    return Config(**config_data)


def save_config(config: Config, config_path: Optional[str] = None) -> None:
    """
    Save configuration to YAML file.
    
    Args:
        config: Config object to save
        config_path: Path to save configuration file
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    
    # Convert to dict and remove sensitive data
    config_dict = config.dict()
    sensitive_keys = ['api_key', 'api_secret']
    for key in sensitive_keys:
        config_dict.pop(key, None)
    
    # Ensure directory exists
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save to file
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_dict, f, default_flow_style=False, indent=2)


def validate_config(config: Config) -> bool:
    """
    Validate configuration settings.
    
    Args:
        config: Config object to validate
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If configuration is invalid
    """
    # Check required API credentials
    if not config.api_key or not config.api_secret:
        raise ValueError("API key and secret are required")
    
    # Validate trading configuration
    if config.trading.price_range['min'] >= config.trading.price_range['max']:
        raise ValueError("Invalid price range: min must be less than max")
    
    # Validate risk management
    if config.risk_management.max_exposure > 1.0:
        raise ValueError("Max exposure cannot exceed 100%")
    
    if config.risk_management.stop_loss_percentage >= config.risk_management.emergency_stop_loss:
        raise ValueError("Emergency stop loss must be greater than regular stop loss")
    
    return True
