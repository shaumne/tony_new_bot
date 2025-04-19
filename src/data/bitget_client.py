"""
Bitget exchange client for trading operations.
"""
import logging
import time
from datetime import datetime
import pandas as pd
import ccxt

logger = logging.getLogger(__name__)


class BitgetClient:
    """Client for Bitget exchange operations."""
    
    def __init__(self, api_key, secret_key, passphrase, testnet=False):
        """
        Initialize Bitget client.
        
        Args:
            api_key (str): API key
            secret_key (str): Secret key
            passphrase (str): API passphrase
            testnet (bool): Whether to use testnet
        """
        self.exchange = ccxt.bitget({
            'apiKey': api_key,
            'secret': secret_key,
            'password': passphrase,
            'enableRateLimit': True,
        })
        
        if testnet:
            self.exchange.set_sandbox_mode(True)
        
        # Initialize exchange
        self.markets = None
        self.update_markets()
    
    def update_markets(self):
        """Update markets information."""
        try:
            self.markets = self.exchange.load_markets()
            logger.info("Markets updated successfully")
            return True
        except Exception as e:
            logger.error(f"Error updating markets: {str(e)}")
            return False
    
    def get_balance(self, currency=None):
        """
        Get account balance.
        
        Args:
            currency (str, optional): Currency to get balance for
            
        Returns:
            dict: Balance information
        """
        try:
            balance = self.exchange.fetch_balance()
            
            if currency:
                if currency in balance['total']:
                    return {
                        'free': balance['free'].get(currency, 0),
                        'used': balance['used'].get(currency, 0),
                        'total': balance['total'].get(currency, 0)
                    }
                else:
                    logger.warning(f"Currency {currency} not found in balance")
                    return {'free': 0, 'used': 0, 'total': 0}
            
            return balance
            
        except Exception as e:
            logger.error(f"Error fetching balance: {str(e)}")
            return None
    
    def get_market_price(self, symbol):
        """
        Get current market price for a symbol.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTC/USDT')
            
        Returns:
            float: Current price
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            logger.error(f"Error fetching market price for {symbol}: {str(e)}")
            return None
    
    def fetch_ohlcv(self, symbol, timeframe='15m', limit=100):
        """
        Fetch OHLCV (candle) data.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTC/USDT')
            timeframe (str): Timeframe (e.g., '15m', '1h', '1d')
            limit (int): Number of candles to fetch
            
        Returns:
            pd.DataFrame: DataFrame with OHLCV data
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV data for {symbol}: {str(e)}")
            return None
    
    def place_order(self, symbol, side, amount, price=None, order_type='market'):
        """
        Place an order.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTC/USDT')
            side (str): Order side ('buy' or 'sell')
            amount (float): Order amount
            price (float, optional): Order price (required for limit orders)
            order_type (str): Order type ('market' or 'limit')
            
        Returns:
            dict: Order information
        """
        try:
            # Validate side
            if side not in ['buy', 'sell']:
                raise ValueError(f"Invalid side: {side}. Must be 'buy' or 'sell'")
            
            # Validate order type
            if order_type not in ['market', 'limit']:
                raise ValueError(f"Invalid order type: {order_type}. Must be 'market' or 'limit'")
            
            # Check if price is provided for limit orders
            if order_type == 'limit' and price is None:
                raise ValueError("Price must be provided for limit orders")
            
            # Place order
            if order_type == 'market':
                order = self.exchange.create_market_order(symbol, side, amount)
            else:
                order = self.exchange.create_limit_order(symbol, side, amount, price)
            
            logger.info(f"Order placed: {order}")
            return order
            
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return None
    
    def cancel_order(self, order_id, symbol):
        """
        Cancel an order.
        
        Args:
            order_id (str): Order ID
            symbol (str): Trading symbol (e.g., 'BTC/USDT')
            
        Returns:
            dict: Cancellation result
        """
        try:
            result = self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Order cancelled: {result}")
            return result
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return None
    
    def get_open_orders(self, symbol=None):
        """
        Get open orders.
        
        Args:
            symbol (str, optional): Trading symbol (e.g., 'BTC/USDT')
            
        Returns:
            list: Open orders
        """
        try:
            if symbol:
                orders = self.exchange.fetch_open_orders(symbol)
            else:
                orders = self.exchange.fetch_open_orders()
            
            return orders
        except Exception as e:
            logger.error(f"Error fetching open orders: {str(e)}")
            return []
    
    def get_order_status(self, order_id, symbol):
        """
        Get order status.
        
        Args:
            order_id (str): Order ID
            symbol (str): Trading symbol (e.g., 'BTC/USDT')
            
        Returns:
            dict: Order information
        """
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            return order
        except Exception as e:
            logger.error(f"Error fetching order status: {str(e)}")
            return None
    
    def get_closed_orders(self, symbol=None, limit=50):
        """
        Get closed orders.
        
        Args:
            symbol (str, optional): Trading symbol (e.g., 'BTC/USDT')
            limit (int): Maximum number of orders to fetch
            
        Returns:
            list: Closed orders
        """
        try:
            if symbol:
                orders = self.exchange.fetch_closed_orders(symbol, limit=limit)
            else:
                # Note: Some exchanges may not support fetching all closed orders without a symbol
                orders = []
                for sym in self.markets:
                    try:
                        sym_orders = self.exchange.fetch_closed_orders(sym, limit=limit)
                        orders.extend(sym_orders)
                    except:
                        continue
            
            return orders
        except Exception as e:
            logger.error(f"Error fetching closed orders: {str(e)}")
            return [] 