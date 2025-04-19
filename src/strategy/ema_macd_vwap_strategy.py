"""
EMA-MACD-VWAP trading strategy implementation.

This strategy places LONG orders when EMA (9,21) bullish crossover and MACD (12,26) bullish crossover
occur at or around the VWAP bands. Similarly, SHORT orders are placed when bearish crossovers occur
at or around the VWAP bands.

Stop Loss: 2X ATR
Take Profit 1: 3X ATR
Take Profit 2: 5X ATR

Positions are closed when EMA and MACD both show crossovers in the opposite direction.
"""
import logging
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from src.indicators.technical_indicators import (
    calculate_ema, calculate_macd, calculate_vwap, calculate_atr,
    detect_ema_crossover, detect_macd_crossover, is_around_vwap_band
)

logger = logging.getLogger(__name__)


class EMAMACDVWAPStrategy:
    """
    Implementation of the EMA-MACD-VWAP trading strategy.
    """
    
    def __init__(self, bitget_client, tradingview_client, config, email_notifier=None):
        """
        Initialize the strategy.
        
        Args:
            bitget_client: Bitget exchange client
            tradingview_client: TradingView data client
            config: Configuration object
            email_notifier: Email notifier object
        """
        self.bitget_client = bitget_client
        self.tradingview_client = tradingview_client
        self.config = config
        self.email_notifier = email_notifier
        
        # Initialize strategy state
        self.open_orders = []
        self.daily_trades = 0
        self.last_trade_reset = datetime.now().date()
        self.trading_active = True
        
        # For TP1 tracking
        self.tp1_hit = {}  # Order ID -> bool
        
        logger.info("EMA-MACD-VWAP strategy initialized")
    
    def reset_daily_trades(self):
        """Reset daily trades counter if day has changed."""
        current_date = datetime.now().date()
        if current_date > self.last_trade_reset:
            self.daily_trades = 0
            self.last_trade_reset = current_date
            logger.info(f"Daily trades reset for {current_date}")
    
    def prepare_data(self, data):
        """
        Prepare and calculate indicators for the data.
        
        Args:
            data (pd.DataFrame): OHLCV data
            
        Returns:
            pd.DataFrame: Data with calculated indicators
        """
        # Calculate EMAs
        data['ema_short'] = calculate_ema(data, self.config.ema_short)
        data['ema_long'] = calculate_ema(data, self.config.ema_long)
        
        # Calculate MACD
        data['macd'], data['macd_signal'], data['macd_hist'] = calculate_macd(
            data, 
            self.config.macd_fast,
            self.config.macd_slow,
            self.config.macd_signal
        )
        
        # Calculate VWAP and bands
        data['vwap_middle'], data['vwap_upper'], data['vwap_lower'] = calculate_vwap(
            data, 
            self.config.vwap_lookback
        )
        
        # Calculate ATR
        data['atr'] = calculate_atr(data, self.config.atr_period)
        
        return data
    
    def check_entry_conditions(self, data):
        """
        Check entry conditions for the strategy.
        
        Args:
            data (pd.DataFrame): Prepared data with indicators
            
        Returns:
            tuple: (entry_signal, side, entry_price, stop_loss, take_profit1, take_profit2, atr_value)
        """
        # Get latest data points
        current_idx = len(data) - 1
        if current_idx < 2:  # Need at least 2 previous candles
            return False, None, None, None, None, None, None
        
        current_price = data['close'].iloc[-1]
        atr_value = data['atr'].iloc[-1]
        
        # Current and previous values for crossover detection
        current_ema_short = data['ema_short'].iloc[-1]
        current_ema_long = data['ema_long'].iloc[-1]
        current_macd = data['macd'].iloc[-1]
        current_macd_signal = data['macd_signal'].iloc[-1]
        
        previous_ema_short = data['ema_short'].iloc[-2]
        previous_ema_long = data['ema_long'].iloc[-2]
        previous_macd = data['macd'].iloc[-2]
        previous_macd_signal = data['macd_signal'].iloc[-2]
        
        # VWAP bands
        vwap_middle = data['vwap_middle'].iloc[-1]
        vwap_upper = data['vwap_upper'].iloc[-1]
        vwap_lower = data['vwap_lower'].iloc[-1]
        
        # Check if price is around any VWAP band
        near_vwap, band_name = is_around_vwap_band(
            current_price, 
            vwap_middle, 
            vwap_upper, 
            vwap_lower, 
            self.config.vwap_band_threshold
        )
        
        if not near_vwap:
            return False, None, None, None, None, None, None
        
        # Detect crossovers
        ema_crossover = detect_ema_crossover(
            current_ema_short, 
            current_ema_long, 
            previous_ema_short, 
            previous_ema_long
        )
        
        macd_crossover = detect_macd_crossover(
            current_macd, 
            current_macd_signal, 
            previous_macd, 
            previous_macd_signal
        )
        
        # LONG signal: Both EMA and MACD show bullish crossover
        if ema_crossover == 1 and macd_crossover == 1:
            # Calculate stop loss and take profit
            stop_loss = current_price - (atr_value * self.config.stop_loss_atr_multiplier)
            take_profit1 = current_price + (atr_value * self.config.take_profit1_atr_multiplier)
            take_profit2 = current_price + (atr_value * self.config.take_profit2_atr_multiplier)
            
            logger.info(f"LONG signal - EMA and MACD bullish crossover near VWAP {band_name} band")
            return True, "buy", current_price, stop_loss, take_profit1, take_profit2, atr_value
        
        # SHORT signal: Both EMA and MACD show bearish crossover
        elif ema_crossover == -1 and macd_crossover == -1:
            # Calculate stop loss and take profit for SHORT
            stop_loss = current_price + (atr_value * self.config.stop_loss_atr_multiplier)
            take_profit1 = current_price - (atr_value * self.config.take_profit1_atr_multiplier)
            take_profit2 = current_price - (atr_value * self.config.take_profit2_atr_multiplier)
            
            logger.info(f"SHORT signal - EMA and MACD bearish crossover near VWAP {band_name} band")
            return True, "sell", current_price, stop_loss, take_profit1, take_profit2, atr_value
        
        return False, None, None, None, None, None, None
    
    def check_exit_conditions(self, data, order_side):
        """
        Check exit conditions for an existing position.
        
        Args:
            data (pd.DataFrame): Prepared data with indicators
            order_side (str): Order side ('buy' for LONG, 'sell' for SHORT)
            
        Returns:
            bool: True if exit conditions are met, False otherwise
        """
        # Get latest data points
        current_idx = len(data) - 1
        if current_idx < 2:  # Need at least 2 previous candles
            return False
        
        # Current and previous values for crossover detection
        current_ema_short = data['ema_short'].iloc[-1]
        current_ema_long = data['ema_long'].iloc[-1]
        current_macd = data['macd'].iloc[-1]
        current_macd_signal = data['macd_signal'].iloc[-1]
        
        previous_ema_short = data['ema_short'].iloc[-2]
        previous_ema_long = data['ema_long'].iloc[-2]
        previous_macd = data['macd'].iloc[-2]
        previous_macd_signal = data['macd_signal'].iloc[-2]
        
        # Detect crossovers
        ema_crossover = detect_ema_crossover(
            current_ema_short, 
            current_ema_long, 
            previous_ema_short, 
            previous_ema_long
        )
        
        macd_crossover = detect_macd_crossover(
            current_macd, 
            current_macd_signal, 
            previous_macd, 
            previous_macd_signal
        )
        
        # For LONG positions, exit on bearish crossovers
        if order_side == 'buy' and ema_crossover == -1 and macd_crossover == -1:
            logger.info("Exit signal for LONG - EMA and MACD bearish crossover")
            return True
        
        # For SHORT positions, exit on bullish crossovers
        elif order_side == 'sell' and ema_crossover == 1 and macd_crossover == 1:
            logger.info("Exit signal for SHORT - EMA and MACD bullish crossover")
            return True
        
        return False
    
    def calculate_position_size(self, price, side):
        """
        Calculate position size based on risk percentage.
        
        Args:
            price (float): Current price
            side (str): Order side ('buy' or 'sell')
            
        Returns:
            float: Position size
        """
        try:
            # Get base and quote currency
            base_currency, quote_currency = self.config.symbol.split('/')
            
            # Get current balance
            if side == 'buy':
                balance = self.bitget_client.get_balance(quote_currency)
                if not balance or balance['free'] <= 0:
                    logger.error(f"Insufficient {quote_currency} balance")
                    return 0
                
                # Calculate order amount in base currency
                wallet_amount = balance['free']
                risk_amount = wallet_amount * (self.config.risk_percentage / 100)
                order_amount = risk_amount / price
                
            else:  # sell
                if self.config.trading_mode == 'paper':
                    # For paper trading, simulate balance
                    wallet_amount = 1000  # Placeholder USDT balance
                    risk_amount = wallet_amount * (self.config.risk_percentage / 100)
                    order_amount = risk_amount / price
                else:
                    # For live trading with margin/futures
                    balance = self.bitget_client.get_balance(quote_currency)
                    if not balance or balance['free'] <= 0:
                        logger.error(f"Insufficient {quote_currency} balance for short")
                        return 0
                    
                    wallet_amount = balance['free']
                    risk_amount = wallet_amount * (self.config.risk_percentage / 100)
                    order_amount = risk_amount / price
            
            # Round order amount to appropriate precision
            if self.bitget_client.markets and self.config.symbol in self.bitget_client.markets:
                market = self.bitget_client.markets[self.config.symbol]
                if 'precision' in market and 'amount' in market['precision']:
                    precision = market['precision']['amount']
                    order_amount = float(round(order_amount, precision))
            
            logger.info(f"Calculated position size: {order_amount} {base_currency} "
                       f"({self.config.risk_percentage}% of {wallet_amount} {quote_currency})")
            
            return order_amount
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0
    
    def place_order(self, side, amount, price=None, order_type='market'):
        """
        Place an order with the exchange.
        
        Args:
            side (str): Order side ('buy' or 'sell')
            amount (float): Order amount
            price (float, optional): Order price (for limit orders)
            order_type (str): Order type ('market' or 'limit')
            
        Returns:
            dict: Order information or None if order failed
        """
        try:
            # Check if we're in paper trading mode
            if self.config.trading_mode == 'paper':
                # Simulate order
                order_id = f"paper_{int(time.time())}"
                order = {
                    'id': order_id,
                    'symbol': self.config.symbol,
                    'side': side,
                    'amount': amount,
                    'price': price if price else self.bitget_client.get_market_price(self.config.symbol),
                    'timestamp': int(time.time() * 1000),
                    'status': 'open',
                    'type': order_type
                }
                logger.info(f"Placed PAPER trading order: {side} {amount} {self.config.symbol}")
                return order
            else:
                # Place real order
                order = self.bitget_client.place_order(
                    self.config.symbol, 
                    side, 
                    amount, 
                    price, 
                    order_type
                )
                
                if order:
                    logger.info(f"Order placed: {side} {amount} {self.config.symbol}")
                    
                return order
                
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            
            # Send email notification about error
            if self.email_notifier:
                self.email_notifier.send_error_notification(f"Error placing order: {str(e)}")
            
            return None
    
    def close_order(self, order, reason="Strategy exit signal"):
        """
        Close an open order.
        
        Args:
            order (dict): Order information
            reason (str): Reason for closing the order
            
        Returns:
            dict: Close order information or None if failed
        """
        try:
            symbol = order['symbol']
            order_id = order['id']
            side = 'sell' if order['side'] == 'buy' else 'buy'
            amount = order['amount']
            
            # Check if we're in paper trading mode
            if self.config.trading_mode == 'paper' or order_id.startswith('paper_'):
                # Simulate closing order
                close_price = self.bitget_client.get_market_price(symbol)
                profit_loss = (close_price - order['price']) * amount if side == 'sell' else (order['price'] - close_price) * amount
                
                logger.info(f"Closed PAPER trading order: {order_id}, Reason: {reason}, P/L: {profit_loss}")
                
                # Remove from open orders
                self.open_orders = [o for o in self.open_orders if o['id'] != order_id]
                
                # Simulate close order
                close_order = {
                    'id': f"close_{order_id}",
                    'symbol': symbol,
                    'side': side,
                    'amount': amount,
                    'price': close_price,
                    'timestamp': int(time.time() * 1000),
                    'status': 'closed',
                    'type': 'market'
                }
                
                return close_order
            else:
                # Close real order
                close_order = self.bitget_client.place_order(symbol, side, amount)
                
                if close_order:
                    logger.info(f"Closed order: {order_id}, Reason: {reason}")
                    
                    # Remove from open orders
                    self.open_orders = [o for o in self.open_orders if o['id'] != order_id]
                
                return close_order
                
        except Exception as e:
            logger.error(f"Error closing order: {str(e)}")
            
            # Send email notification about error
            if self.email_notifier:
                self.email_notifier.send_error_notification(f"Error closing order: {str(e)}")
            
            return None
    
    def check_take_profit_stop_loss(self, data):
        """
        Check if any open orders hit take profit or stop loss levels.
        
        Args:
            data (pd.DataFrame): Current price data
        """
        if not self.open_orders:
            return
        
        current_price = data['close'].iloc[-1]
        
        for order in list(self.open_orders):  # Use list() to create a copy for safe iteration
            if 'stop_loss' not in order or 'take_profit1' not in order or 'take_profit2' not in order:
                continue
            
            order_id = order['id']
            side = order['side']
            stop_loss = order['stop_loss']
            take_profit1 = order['take_profit1']
            take_profit2 = order['take_profit2']
            
            # Check if TP1 has been hit
            if order_id not in self.tp1_hit:
                self.tp1_hit[order_id] = False
            
            # For LONG positions
            if side == 'buy':
                # Check stop loss
                if current_price <= stop_loss:
                    logger.info(f"Stop loss hit for {order_id} at {current_price}")
                    self.close_order(order, reason="Stop loss")
                    
                    # Send email notification
                    if self.email_notifier:
                        self.email_notifier.send_trade_notification(
                            "CLOSE", self.config.symbol, "sell", order['amount'], current_price,
                            reason="Stop Loss"
                        )
                
                # Check take profit 2
                elif current_price >= take_profit2:
                    logger.info(f"Take profit 2 hit for {order_id} at {current_price}")
                    self.close_order(order, reason="Take profit 2")
                    
                    # Send email notification
                    if self.email_notifier:
                        self.email_notifier.send_trade_notification(
                            "CLOSE", self.config.symbol, "sell", order['amount'], current_price,
                            reason="Take Profit 2"
                        )
                
                # Check take profit 1
                elif current_price >= take_profit1 and not self.tp1_hit[order_id]:
                    logger.info(f"Take profit 1 hit for {order_id} at {current_price}")
                    self.tp1_hit[order_id] = True
                    
                    # Here you can implement moving the stop loss to breakeven or partially closing the position
                    # For simplicity, we'll just log the event and send a notification
                    if self.email_notifier:
                        self.email_notifier.send_email(
                            f"Take Profit 1 Hit - {self.config.symbol}",
                            f"Take Profit 1 has been hit for order {order_id} at {current_price}. "
                            f"Consider moving stop loss to breakeven."
                        )
            
            # For SHORT positions
            elif side == 'sell':
                # Check stop loss
                if current_price >= stop_loss:
                    logger.info(f"Stop loss hit for {order_id} at {current_price}")
                    self.close_order(order, reason="Stop loss")
                    
                    # Send email notification
                    if self.email_notifier:
                        self.email_notifier.send_trade_notification(
                            "CLOSE", self.config.symbol, "buy", order['amount'], current_price,
                            reason="Stop Loss"
                        )
                
                # Check take profit 2
                elif current_price <= take_profit2:
                    logger.info(f"Take profit 2 hit for {order_id} at {current_price}")
                    self.close_order(order, reason="Take profit 2")
                    
                    # Send email notification
                    if self.email_notifier:
                        self.email_notifier.send_trade_notification(
                            "CLOSE", self.config.symbol, "buy", order['amount'], current_price,
                            reason="Take Profit 2"
                        )
                
                # Check take profit 1
                elif current_price <= take_profit1 and not self.tp1_hit[order_id]:
                    logger.info(f"Take profit 1 hit for {order_id} at {current_price}")
                    self.tp1_hit[order_id] = True
                    
                    # Here you can implement moving the stop loss to breakeven or partially closing the position
                    if self.email_notifier:
                        self.email_notifier.send_email(
                            f"Take Profit 1 Hit - {self.config.symbol}",
                            f"Take Profit 1 has been hit for order {order_id} at {current_price}. "
                            f"Consider moving stop loss to breakeven."
                        )
    
    def check_exit_signals(self, data):
        """
        Check if any open orders meet the exit signal conditions.
        
        Args:
            data (pd.DataFrame): Data with indicators
        """
        if not self.open_orders:
            return
        
        for order in list(self.open_orders):  # Use list() to create a copy for safe iteration
            side = order['side']
            
            # Check if exit conditions are met
            if self.check_exit_conditions(data, side):
                self.close_order(order, reason="Exit signal")
                
                # Send email notification
                if self.email_notifier:
                    close_side = 'sell' if side == 'buy' else 'buy'
                    current_price = data['close'].iloc[-1]
                    
                    self.email_notifier.send_trade_notification(
                        "CLOSE", self.config.symbol, close_side, order['amount'], current_price,
                        reason="Exit Signal"
                    )
    
    def run(self):
        """
        Run the strategy.
        
        This is the main method that executes the trading logic.
        """
        logger.info(f"Starting EMA-MACD-VWAP strategy on {self.config.symbol} ({self.config.timeframe})")
        
        while self.trading_active:
            try:
                # Reset daily trades if day has changed
                self.reset_daily_trades()
                
                # Check if maximum daily trades reached
                if self.daily_trades >= self.config.max_daily_trades:
                    logger.info(f"Maximum daily trades reached ({self.daily_trades}). Waiting for next day.")
                    time.sleep(60)  # Check again after a minute
                    continue
                
                # Fetch latest data
                data = self.bitget_client.fetch_ohlcv(
                    self.config.symbol, 
                    self.config.timeframe, 
                    limit=100
                )
                
                if data is None or len(data) < 50:  # Ensure enough data for indicators
                    logger.error("Failed to fetch sufficient data")
                    time.sleep(30)
                    continue
                
                # Prepare data with indicators
                prepared_data = self.prepare_data(data)
                
                # Check take profit and stop loss for open orders
                self.check_take_profit_stop_loss(prepared_data)
                
                # Check exit signals for open orders
                self.check_exit_signals(prepared_data)
                
                # Check if we can open new orders
                if len(self.open_orders) < self.config.max_open_orders:
                    # Check entry conditions
                    entry_signal, side, price, stop_loss, take_profit1, take_profit2, atr = self.check_entry_conditions(prepared_data)
                    
                    if entry_signal and side:
                        # Calculate position size
                        amount = self.calculate_position_size(price, side)
                        
                        if amount > 0:
                            # Place order
                            order = self.place_order(side, amount)
                            
                            if order:
                                # Add stop loss and take profit to order info
                                order['stop_loss'] = stop_loss
                                order['take_profit1'] = take_profit1
                                order['take_profit2'] = take_profit2
                                order['atr'] = atr
                                
                                # Add to open orders
                                self.open_orders.append(order)
                                
                                # Increment daily trades
                                self.daily_trades += 1
                                
                                # Send email notification
                                if self.email_notifier:
                                    self.email_notifier.send_trade_notification(
                                        "OPEN", self.config.symbol, side, amount, price,
                                        stop_loss, take_profit1, take_profit2
                                    )
                
                # Sleep before next iteration
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in strategy execution: {str(e)}")
                
                # Send email notification about error
                if self.email_notifier:
                    self.email_notifier.send_error_notification(f"Strategy execution error: {str(e)}")
                
                time.sleep(30)  # Wait before retrying
    
    def stop(self):
        """Stop the strategy."""
        logger.info("Stopping strategy")
        self.trading_active = False
    
    def backtest(self, start_date, end_date):
        """
        Run a backtest of the strategy on historical data.
        
        Args:
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            
        Returns:
            dict: Backtest results
        """
        logger.info(f"Running backtest from {start_date} to {end_date} on {self.config.symbol} ({self.config.timeframe})")
        
        try:
            # Convert start_date and end_date to datetime
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            # Calculate the number of candles needed based on timeframe
            if self.config.timeframe == '15m':
                candles_per_day = 24 * 4  # 15 minutes candles
            elif self.config.timeframe == '1h':
                candles_per_day = 24
            elif self.config.timeframe == '4h':
                candles_per_day = 6
            elif self.config.timeframe == '1d':
                candles_per_day = 1
            else:
                candles_per_day = 24 * 4  # Default to 15m
            
            # Calculate total days and candles needed
            total_days = (end_dt - start_dt).days
            total_candles = total_days * candles_per_day
            
            # Fetch historical data
            data = self.bitget_client.fetch_ohlcv(
                self.config.symbol, 
                self.config.timeframe, 
                limit=min(total_candles, 1000)  # Most exchanges limit to 1000 candles
            )
            
            if data is None or len(data) < 50:
                logger.error("Failed to fetch sufficient data for backtesting")
                return {"error": "Insufficient data"}
            
            # Prepare data with indicators
            prepared_data = self.prepare_data(data)
            
            # Initialize backtest variables
            backtest_orders = []
            equity_curve = [1000]  # Start with 1000 units
            current_equity = 1000
            max_equity = 1000
            max_drawdown = 0
            total_trades = 0
            winning_trades = 0
            losing_trades = 0
            
            # Simulate trading
            for i in range(50, len(prepared_data)):  # Start from 50 to ensure indicators are calculated
                current_data = prepared_data.iloc[:i+1]
                current_price = current_data['close'].iloc[-1]
                
                # Check for exit signals for open positions
                for order in list(backtest_orders):
                    exit_signal = self.check_exit_conditions(current_data, order['side'])
                    hit_stop_loss = (order['side'] == 'buy' and current_price <= order['stop_loss']) or \
                                   (order['side'] == 'sell' and current_price >= order['stop_loss'])
                    hit_take_profit = (order['side'] == 'buy' and current_price >= order['take_profit2']) or \
                                     (order['side'] == 'sell' and current_price <= order['take_profit2'])
                    
                    if exit_signal or hit_stop_loss or hit_take_profit:
                        # Calculate profit/loss
                        pl = 0
                        if order['side'] == 'buy':
                            pl = (current_price - order['price']) / order['price'] * 100
                        else:  # sell
                            pl = (order['price'] - current_price) / order['price'] * 100
                        
                        # Update equity
                        current_equity *= (1 + pl/100)
                        equity_curve.append(current_equity)
                        
                        # Update statistics
                        total_trades += 1
                        if pl > 0:
                            winning_trades += 1
                        else:
                            losing_trades += 1
                        
                        # Update max equity and drawdown
                        if current_equity > max_equity:
                            max_equity = current_equity
                        
                        drawdown = (max_equity - current_equity) / max_equity * 100
                        if drawdown > max_drawdown:
                            max_drawdown = drawdown
                        
                        # Remove order
                        backtest_orders.remove(order)
                        
                        # Log trade
                        logger.info(f"Backtest Exit: {order['side']} {self.config.symbol} at {current_price}, "
                                   f"P/L: {pl:.2f}%, Reason: {'Exit Signal' if exit_signal else 'Stop Loss' if hit_stop_loss else 'Take Profit'}")
                
                # Check for entry signals
                if len(backtest_orders) < self.config.max_open_orders:
                    entry_signal, side, price, stop_loss, take_profit1, take_profit2, atr = self.check_entry_conditions(current_data)
                    
                    if entry_signal and side:
                        # Create order
                        order = {
                            'id': f"backtest_{len(backtest_orders)}_{i}",
                            'symbol': self.config.symbol,
                            'side': side,
                            'amount': 1,  # Simplified for backtest
                            'price': price,
                            'stop_loss': stop_loss,
                            'take_profit1': take_profit1,
                            'take_profit2': take_profit2,
                            'timestamp': current_data.index[-1],
                            'atr': atr
                        }
                        
                        # Add to orders
                        backtest_orders.append(order)
                        
                        # Log entry
                        logger.info(f"Backtest Entry: {side} {self.config.symbol} at {price}, "
                                   f"SL: {stop_loss}, TP1: {take_profit1}, TP2: {take_profit2}")
            
            # Calculate final statistics
            win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
            total_return = (current_equity - 1000) / 1000 * 100
            
            # Create results
            results = {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": win_rate,
                "total_return": total_return,
                "max_drawdown": max_drawdown,
                "final_equity": current_equity,
                "equity_curve": equity_curve
            }
            
            logger.info(f"Backtest results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error in backtesting: {str(e)}")
            return {"error": str(e)} 