"""
TradingView data fetching client.
"""
import logging
from datetime import datetime, timedelta
import pandas as pd
import pytz
from tradingview_ta import TA_Handler, Interval

logger = logging.getLogger(__name__)

# Map timeframes to TradingView intervals - kullanılabilir sabitler için Interval sınıfını kontrol ettik
TIMEFRAME_MAPPING = {
    '1m': Interval.INTERVAL_1_MINUTE,
    '5m': Interval.INTERVAL_5_MINUTES,
    '15m': Interval.INTERVAL_15_MINUTES,
    '30m': Interval.INTERVAL_30_MINUTES,
    '1h': Interval.INTERVAL_1_HOUR,
    '2h': Interval.INTERVAL_2_HOURS,
    '4h': Interval.INTERVAL_4_HOURS,
    '1d': Interval.INTERVAL_1_DAY,
    '1W': Interval.INTERVAL_1_WEEK,
    '1M': Interval.INTERVAL_1_MONTH
}


class TradingViewClient:
    """Client for fetching data from TradingView."""
    
    def __init__(self, symbol, exchange="BITGET", screener="crypto"):
        """
        Initialize TradingView client.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            exchange (str): Exchange name
            screener (str): Screener name ('crypto', 'forex', 'america', etc.)
        """
        self.symbol = symbol
        self.exchange = exchange
        self.screener = screener
        
        # Convert ccxt symbol format (BTC/USDT) to TradingView format (BTCUSDT)
        if '/' in self.symbol:
            self.tv_symbol = self.symbol.replace('/', '')
        else:
            self.tv_symbol = self.symbol
    
    def get_indicators(self, timeframe='15m'):
        """
        Get technical indicators from TradingView.
        
        Args:
            timeframe (str): Timeframe (e.g., '15m', '1h', '1d')
            
        Returns:
            dict: Dictionary with technical indicators
        """
        try:
            if timeframe not in TIMEFRAME_MAPPING:
                raise ValueError(f"Unsupported timeframe: {timeframe}")
            
            tv_interval = TIMEFRAME_MAPPING[timeframe]
            
            handler = TA_Handler(
                symbol=self.tv_symbol,
                exchange=self.exchange,
                screener=self.screener,
                interval=tv_interval
            )
            
            analysis = handler.get_analysis()
            return analysis.indicators
            
        except Exception as e:
            logger.error(f"Error fetching TradingView indicators: {str(e)}")
            return None
    
    def get_latest_candle(self, timeframe='15m'):
        """
        Get the latest candle data.
        
        Args:
            timeframe (str): Timeframe (e.g., '15m', '1h', '1d')
            
        Returns:
            dict: Dictionary with candle data
        """
        try:
            indicators = self.get_indicators(timeframe)
            
            if not indicators:
                return None
            
            # Extract candle data from indicators
            candle = {
                'open': indicators.get('open', None),
                'high': indicators.get('high', None),
                'low': indicators.get('low', None),
                'close': indicators.get('close', None),
                'volume': indicators.get('volume', None),
                'timestamp': datetime.now(pytz.UTC)
            }
            
            return candle
        
        except Exception as e:
            logger.error(f"Error fetching latest candle: {str(e)}")
            return None
    
    def get_historical_data(self, timeframe='15m', limit=100):
        """
        Get historical candle data.
        
        Note: TradingView-TA doesn't provide historical data API directly.
        This implementation uses indicators which may be limited.
        For production use, consider a different data source or paid API.
        
        Args:
            timeframe (str): Timeframe (e.g., '15m', '1h', '1d')
            limit (int): Number of candles to fetch (may be limited by API)
            
        Returns:
            pd.DataFrame: DataFrame with historical data
        """
        try:
            # This is a limitation - TradingView-TA doesn't have a built-in historical data API
            # For demonstration purposes, we'll create synthetic data based on current values
            # In a production environment, use a proper data source
            
            current = self.get_latest_candle(timeframe)
            if not current:
                return None
            
            # Create a synthetic DataFrame for demonstration
            # In production, replace this with actual API calls
            data = []
            current_time = datetime.now(pytz.UTC)
            
            # Map timeframe to minutes
            if timeframe == '15m':
                minutes = 15
            elif timeframe == '1h':
                minutes = 60
            elif timeframe == '4h':
                minutes = 240
            elif timeframe == '1d':
                minutes = 1440
            else:
                minutes = 15  # default
            
            # Create synthetic data
            for i in range(limit):
                candle_time = current_time - timedelta(minutes=minutes * i)
                
                # Add some randomness to demonstrate different candles
                # In production, this should be actual historical data
                random_factor = 1 + (((i % 10) - 5) / 1000)
                
                data.append({
                    'timestamp': candle_time,
                    'open': current['open'] * random_factor,
                    'high': current['high'] * random_factor * 1.002,
                    'low': current['low'] * random_factor * 0.998,
                    'close': current['close'] * random_factor,
                    'volume': current['volume'] * random_factor
                })
            
            df = pd.DataFrame(reversed(data))
            
            logger.warning("Using synthetic historical data. In production, use a proper data source.")
            return df
            
        except Exception as e:
            logger.error(f"Error creating historical data: {str(e)}")
            return None 