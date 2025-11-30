"""
Configuration management for TradeAlgo
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

class Config:
    """Central configuration manager"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_file = self.base_dir / "config" / "config.yaml"
        self._config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_file}")
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    # Kite API Credentials
    @property
    def kite_api_key(self) -> str:
        return os.getenv('KITE_API_KEY', '')
    
    @property
    def kite_api_secret(self) -> str:
        return os.getenv('KITE_API_SECRET', '')
    
    @property
    def kite_redirect_url(self) -> str:
        return os.getenv('KITE_REDIRECT_URL', 'http://127.0.0.1:5000/callback')
    
    # Database
    @property
    def database_url(self) -> str:
        return os.getenv('DATABASE_URL', 'sqlite:///data_storage/database/tradealgo.db')
    
    # API
    @property
    def api_host(self) -> str:
        return os.getenv('API_HOST', '127.0.0.1')
    
    @property
    def api_port(self) -> int:
        return int(os.getenv('API_PORT', 5000))
    
    # Logging
    @property
    def log_level(self) -> str:
        return os.getenv('LOG_LEVEL', 'INFO')
    
    @property
    def log_file(self) -> str:
        return os.getenv('LOG_FILE', 'logs/tradealgo.log')
    
    # Risk Management
    @property
    def max_daily_loss_percent(self) -> float:
        return float(os.getenv('MAX_DAILY_LOSS_PERCENT', 5))
    
    @property
    def max_position_size_percent(self) -> float:
        return float(os.getenv('MAX_POSITION_SIZE_PERCENT', 10))
    
    @property
    def max_positions(self) -> int:
        return int(os.getenv('MAX_POSITIONS', 5))
    
    # Trading
    @property
    def default_slippage_percent(self) -> float:
        return float(os.getenv('DEFAULT_SLIPPAGE_PERCENT', 0.1))
    
    @property
    def default_brokerage_percent(self) -> float:
        return float(os.getenv('DEFAULT_BROKERAGE_PERCENT', 0.03))


# Global config instance
config = Config()
