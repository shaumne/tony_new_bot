"""
Configuration utilities for loading and validating environment variables.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """Configuration class for loading and accessing environment variables."""
    
    def __init__(self, env_file='.env'):
        """
        Initialize configuration.
        
        Args:
            env_file (str): Path to the .env file
        """
        # Load environment variables from .env file
        load_dotenv(env_file)
        
        # Initialize configuration
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables."""
        # Exchange API credentials
        self.bitget_api_key = os.getenv('BITGET_API_KEY')
        self.bitget_secret_key = os.getenv('BITGET_SECRET_KEY')
        self.bitget_passphrase = os.getenv('BITGET_PASSPHRASE')
        
        # Trading parameters
        self.symbol = os.getenv('SYMBOL', 'BTC/USDT')
        self.timeframe = os.getenv('TIMEFRAME', '15m')
        self.risk_percentage = float(os.getenv('RISK_PERCENTAGE', '50'))
        self.max_open_orders = int(os.getenv('MAX_OPEN_ORDERS', '2'))
        self.max_daily_trades = int(os.getenv('MAX_DAILY_TRADES', '6'))
        
        # Strategy parameters
        self.ema_short = int(os.getenv('EMA_SHORT', '9'))
        self.ema_long = int(os.getenv('EMA_LONG', '21'))
        self.macd_fast = int(os.getenv('MACD_FAST', '12'))
        self.macd_slow = int(os.getenv('MACD_SLOW', '26'))
        self.macd_signal = int(os.getenv('MACD_SIGNAL', '9'))
        self.vwap_lookback = int(os.getenv('VWAP_LOOKBACK', '14'))
        self.atr_period = int(os.getenv('ATR_PERIOD', '14'))
        self.stop_loss_atr_multiplier = float(os.getenv('STOP_LOSS_ATR_MULTIPLIER', '2'))
        self.take_profit1_atr_multiplier = float(os.getenv('TAKE_PROFIT1_ATR_MULTIPLIER', '3'))
        self.take_profit2_atr_multiplier = float(os.getenv('TAKE_PROFIT2_ATR_MULTIPLIER', '5'))
        self.vwap_band_threshold = float(os.getenv('VWAP_BAND_THRESHOLD', '0.0015'))
        
        # Email notification settings
        self.email_enabled = os.getenv('EMAIL_ENABLED', 'True').lower() in ('true', '1', 't')
        self.email_sender = os.getenv('EMAIL_SENDER', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        self.email_recipient = os.getenv('EMAIL_RECIPIENT', '')
        self.email_smtp_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.email_smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
        
        # Trading mode
        self.trading_mode = os.getenv('TRADING_MODE', 'paper')
        
        # Backtesting parameters
        self.backtest_start_date = os.getenv('BACKTEST_START_DATE', '2023-01-01')
        self.backtest_end_date = os.getenv('BACKTEST_END_DATE', '2023-02-01')
        
        # Logging settings
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # Database settings
        self.db_enabled = os.getenv('DB_ENABLED', 'False').lower() in ('true', '1', 't')
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.db_name = os.getenv('DB_NAME', 'trading_bot')
    
    def validate(self):
        """
        Validate configuration.
        
        Returns:
            bool: True if valid, False otherwise
        """
        # Required fields
        required_fields = {
            'bitget_api_key': 'BITGET_API_KEY',
            'bitget_secret_key': 'BITGET_SECRET_KEY',
            'bitget_passphrase': 'BITGET_PASSPHRASE'
        }
        
        missing_fields = []
        for field, env_var in required_fields.items():
            if not getattr(self, field):
                missing_fields.append(env_var)
        
        if missing_fields:
            logger.error(f"Missing required configuration fields: {', '.join(missing_fields)}")
            return False
        
        # Validate trading mode
        if self.trading_mode not in ['paper', 'live']:
            logger.error(f"Invalid trading mode: {self.trading_mode}. Must be 'paper' or 'live'")
            return False
        
        # Validate email settings if enabled
        if self.email_enabled:
            if not all([self.email_sender, self.email_password, self.email_recipient]):
                logger.error("Email notification is enabled but some settings are missing")
                return False
        
        return True
    
    def to_dict(self):
        """
        Convert configuration to dictionary.
        
        Returns:
            dict: Configuration as dictionary
        """
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    def __str__(self):
        """Return string representation of configuration."""
        config_dict = self.to_dict()
        
        # Hide sensitive data
        if 'bitget_api_key' in config_dict:
            config_dict['bitget_api_key'] = '********'
        if 'bitget_secret_key' in config_dict:
            config_dict['bitget_secret_key'] = '********'
        if 'bitget_passphrase' in config_dict:
            config_dict['bitget_passphrase'] = '********'
        if 'email_password' in config_dict:
            config_dict['email_password'] = '********'
        
        return str(config_dict) 