"""
EMA-MACD trading strategy implementation.

This strategy places LONG orders when EMA (9,21) bullish crossover and MACD (12,26) bullish crossover occur.
Similarly, SHORT orders are placed when bearish crossovers occur.

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
    calculate_ema, calculate_macd, calculate_atr,
    detect_ema_crossover, detect_macd_crossover
)

logger = logging.getLogger(__name__)


class EMAMACDStrategy:
    """
    EMA-MACD Trading Strategy
    
    Entry Conditions:
    - Long: EMA(9,21) bullish crossover AND MACD(12,26) bullish crossover
    - Short: EMA(9,21) bearish crossover AND MACD(12,26) bearish crossover
    
    Exit Conditions:
    - Close Long: EMA and MACD bearish crossover
    - Close Short: EMA and MACD bullish crossover
    
    Risk Management:
    - Stop Loss: 2X ATR
    - Take Profit 1: 3X ATR
    - Take Profit 2: 5X ATR
    - Risk: 50% of wallet amount per trade
    - Max open orders: 2
    - Max trades per day: 6
    """
    
    def __init__(self, exchange_client, data_client, config, email_notifier=None):
        """
        Initialize the strategy.
        
        Args:
            exchange_client: Exchange client for executing trades
            data_client: Data client for retrieving market data
            config: Configuration settings
            email_notifier: Email notifier for sending alerts
        """
        self.exchange = exchange_client
        self.data_client = data_client
        self.config = config
        self.email_notifier = email_notifier
        
        # Strategy parameters
        self.symbol = config.symbol
        self.timeframe = config.timeframe
        self.fast_ema = 9
        self.slow_ema = 21
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.atr_period = 14
        self.sl_atr_multiplier = 2.0
        self.tp1_atr_multiplier = 3.0
        self.tp2_atr_multiplier = 5.0
        self.max_open_orders = 2
        self.max_trades_per_day = 6
        self.risk_per_trade = 0.50  # 50% of wallet per trade
        
        # Trading state
        self.running = False
        self.orders = {}
        self.trades_today = 0
        self.last_trade_time = None
        
        # Initialize logger
        setup_logging(config.log_level)
        
        logger.info(f"EMA-MACD Strategy initialized for {self.symbol} on {self.timeframe}")
        logger.info(f"Strategy parameters: EMA({self.fast_ema},{self.slow_ema}), MACD({self.macd_fast},{self.macd_slow},{self.macd_signal})")
        logger.info(f"Risk parameters: SL: {self.sl_atr_multiplier}xATR, TP1: {self.tp1_atr_multiplier}xATR, TP2: {self.tp2_atr_multiplier}xATR")
    
    def prepare_data(self):
        """
        Prepare and process data for analysis.
        
        Returns:
            pd.DataFrame: Processed data with indicators
        """
        try:
            # Get candlestick data
            raw_data = self.data_client.get_klines(self.symbol, self.timeframe)
            
            # Convert to dataframe
            df = pd.DataFrame(raw_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Convert string values to float
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # Calculate indicators
            df = self.calculate_indicators(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error preparing data: {e}")
            return None
    
    def calculate_indicators(self, df):
        """
        Calculate technical indicators.
        
        Args:
            df: DataFrame with price data
            
        Returns:
            DataFrame with indicators
        """
        try:
            # Calculate EMAs
            df['ema_fast'] = df['close'].ewm(span=self.fast_ema, adjust=False).mean()
            df['ema_slow'] = df['close'].ewm(span=self.slow_ema, adjust=False).mean()
            
            # Calculate MACD
            df['macd_line'] = df['close'].ewm(span=self.macd_fast, adjust=False).mean() - df['close'].ewm(span=self.macd_slow, adjust=False).mean()
            df['macd_signal'] = df['macd_line'].ewm(span=self.macd_signal, adjust=False).mean()
            df['macd_histogram'] = df['macd_line'] - df['macd_signal']
            
            # Calculate ATR
            df['tr'] = df.apply(
                lambda x: max(
                    x['high'] - x['low'],
                    abs(x['high'] - x['close'].shift(1)),
                    abs(x['low'] - x['close'].shift(1))
                ),
                axis=1
            )
            df['atr'] = df['tr'].rolling(window=self.atr_period).mean()
            
            # Calculate crossovers
            df['ema_crossover'] = np.where(
                (df['ema_fast'].shift(1) < df['ema_slow'].shift(1)) & (df['ema_fast'] >= df['ema_slow']),
                1,  # Bullish crossover
                np.where(
                    (df['ema_fast'].shift(1) > df['ema_slow'].shift(1)) & (df['ema_fast'] <= df['ema_slow']),
                    -1,  # Bearish crossover
                    0
                )
            )
            
            df['macd_crossover'] = np.where(
                (df['macd_line'].shift(1) < df['macd_signal'].shift(1)) & (df['macd_line'] >= df['macd_signal']),
                1,  # Bullish crossover
                np.where(
                    (df['macd_line'].shift(1) > df['macd_signal'].shift(1)) & (df['macd_line'] <= df['macd_signal']),
                    -1,  # Bearish crossover
                    0
                )
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return df
    
    def check_entry_conditions(self, df):
        """
        Check for entry conditions.
        
        Args:
            df: DataFrame with indicators
            
        Returns:
            dict: Entry signals (long, short)
        """
        signals = {'long': False, 'short': False}
        
        try:
            # Check if we have enough data
            if len(df) < max(self.slow_ema, self.macd_slow, self.atr_period) + 10:
                return signals
            
            # Get the most recent data
            current = df.iloc[-1]
            
            # Check long conditions
            if (current['ema_crossover'] == 1 and current['macd_crossover'] == 1):
                signals['long'] = True
                logger.info(f"Long entry signal for {self.symbol}: EMA and MACD bullish crossover")
            
            # Check short conditions
            if (current['ema_crossover'] == -1 and current['macd_crossover'] == -1):
                signals['short'] = True
                logger.info(f"Short entry signal for {self.symbol}: EMA and MACD bearish crossover")
                
            return signals
            
        except Exception as e:
            logger.error(f"Error checking entry conditions: {e}")
            return signals
    
    def check_exit_conditions(self, df, position_side):
        """
        Check for exit conditions.
        
        Args:
            df: DataFrame with indicators
            position_side: The side of the position ('long' or 'short')
            
        Returns:
            bool: Whether to exit the position
        """
        try:
            # Check if we have enough data
            if len(df) < max(self.slow_ema, self.macd_slow, self.atr_period) + 10:
                return False
            
            # Get the most recent data
            current = df.iloc[-1]
            
            # Exit long if EMA and MACD bearish crossover
            if position_side == 'long' and current['ema_crossover'] == -1 and current['macd_crossover'] == -1:
                logger.info(f"Exit signal for long position on {self.symbol}: EMA and MACD bearish crossover")
                return True
            
            # Exit short if EMA and MACD bullish crossover
            if position_side == 'short' and current['ema_crossover'] == 1 and current['macd_crossover'] == 1:
                logger.info(f"Exit signal for short position on {self.symbol}: EMA and MACD bullish crossover")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking exit conditions: {e}")
            return False
    
    def can_place_new_trade(self):
        """
        Check if we can place a new trade based on limits.
        
        Returns:
            bool: Whether a new trade can be placed
        """
        # Check max open orders
        open_positions = self.exchange.get_positions(self.symbol)
        if len(open_positions) >= self.max_open_orders:
            logger.info(f"Cannot place new trade: Max open orders reached ({self.max_open_orders})")
            return False
        
        # Check max trades per day
        if self.trades_today >= self.max_trades_per_day:
            logger.info(f"Cannot place new trade: Max trades per day reached ({self.max_trades_per_day})")
            return False
        
        # Reset trades count if it's a new day
        now = datetime.now()
        if self.last_trade_time and self.last_trade_time.date() < now.date():
            self.trades_today = 0
        
        return True
    
    def place_order(self, side, current_price, atr_value):
        """
        Place a new order.
        
        Args:
            side: Order side ('long' or 'short')
            current_price: Current price
            atr_value: Current ATR value
            
        Returns:
            dict: Order information or None if failed
        """
        try:
            # Get wallet balance
            balance = self.exchange.get_balance()
            
            if balance <= 0:
                logger.warning(f"Cannot place order: Insufficient balance ({balance})")
                return None
            
            # Calculate position size (50% of wallet)
            position_size = calculate_position_size(
                balance,
                self.risk_per_trade,
                self.symbol,
                self.exchange.get_min_order_size(self.symbol)
            )
            
            if position_size <= 0:
                logger.warning(f"Cannot place order: Position size too small ({position_size})")
                return None
            
            # Calculate stop loss and take profit levels
            sl_price = None
            if side == 'long':
                sl_price = current_price - (atr_value * self.sl_atr_multiplier)
                tp1_price = current_price + (atr_value * self.tp1_atr_multiplier)
                tp2_price = current_price + (atr_value * self.tp2_atr_multiplier)
            else:  # short
                sl_price = current_price + (atr_value * self.sl_atr_multiplier)
                tp1_price = current_price - (atr_value * self.tp1_atr_multiplier)
                tp2_price = current_price - (atr_value * self.tp2_atr_multiplier)
            
            # Place the order
            order_id = self.exchange.place_order(
                symbol=self.symbol,
                side=side,
                quantity=position_size,
                price=current_price,
                stop_loss=sl_price
            )
            
            if not order_id:
                logger.error(f"Failed to place {side} order")
                return None
            
            # Record the trade
            order_info = {
                'id': order_id,
                'symbol': self.symbol,
                'side': side,
                'entry_price': current_price,
                'quantity': position_size,
                'stop_loss': sl_price,
                'take_profit_1': tp1_price,
                'take_profit_2': tp2_price,
                'time': datetime.now()
            }
            
            # Update trade count
            self.trades_today += 1
            self.last_trade_time = datetime.now()
            
            # Store order info
            self.orders[order_id] = order_info
            
            # Log the order
            logger.info(f"Placed {side} order: {order_info}")
            
            # Send email notification
            if self.email_notifier:
                subject = f"New {side.upper()} Order Placed - {self.symbol}"
                message = f"""
                Order Details:
                Symbol: {self.symbol}
                Side: {side.upper()}
                Entry Price: {current_price}
                Quantity: {position_size}
                Stop Loss: {sl_price}
                Take Profit 1: {tp1_price}
                Take Profit 2: {tp2_price}
                Time: {datetime.now()}
                """
                self.email_notifier.send_email(subject, message)
            
            return order_info
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def close_position(self, position):
        """
        Close an open position.
        
        Args:
            position: Position information
            
        Returns:
            bool: Success or failure
        """
        try:
            # Close the position
            success = self.exchange.close_position(
                symbol=position['symbol'],
                side='sell' if position['side'] == 'long' else 'buy',
                quantity=position['quantity']
            )
            
            if success:
                logger.info(f"Closed position: {position}")
                
                # Send email notification
                if self.email_notifier:
                    subject = f"Position Closed - {position['symbol']}"
                    message = f"""
                    Position Closed:
                    Symbol: {position['symbol']}
                    Side: {position['side'].upper()}
                    Entry Price: {position['entry_price']}
                    Quantity: {position['quantity']}
                    Time: {datetime.now()}
                    """
                    self.email_notifier.send_email(subject, message)
                
                # Remove from orders
                if position['id'] in self.orders:
                    del self.orders[position['id']]
                
                return True
            else:
                logger.error(f"Failed to close position: {position}")
                return False
                
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False
    
    def manage_take_profit(self, position, current_price):
        """
        Manage take profit for an open position.
        
        Args:
            position: Position information
            current_price: Current price
            
        Returns:
            bool: Whether take profit was hit
        """
        try:
            # Check if take profit is hit
            if position['side'] == 'long':
                if current_price >= position['take_profit_2']:
                    logger.info(f"Take Profit 2 hit for {position['symbol']}: {position['take_profit_2']}")
                    return self.close_position(position)
                elif current_price >= position['take_profit_1']:
                    # Could implement partial close here for TP1
                    logger.info(f"Take Profit 1 hit for {position['symbol']}: {position['take_profit_1']}")
                    return False
            else:  # short
                if current_price <= position['take_profit_2']:
                    logger.info(f"Take Profit 2 hit for {position['symbol']}: {position['take_profit_2']}")
                    return self.close_position(position)
                elif current_price <= position['take_profit_1']:
                    # Could implement partial close here for TP1
                    logger.info(f"Take Profit 1 hit for {position['symbol']}: {position['take_profit_1']}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error managing take profit: {e}")
            return False
    
    def run(self):
        """
        Run the strategy in a loop.
        """
        self.running = True
        
        logger.info(f"Starting EMA-MACD strategy for {self.symbol}")
        
        while self.running:
            try:
                # Prepare data
                df = self.prepare_data()
                
                if df is None or len(df) == 0:
                    logger.warning("No data available. Retrying...")
                    time.sleep(10)
                    continue
                
                # Get current price and ATR
                current_price = df['close'].iloc[-1]
                atr_value = df['atr'].iloc[-1]
                
                # Check and manage open positions
                positions = self.exchange.get_positions(self.symbol)
                
                for position in positions:
                    # Check exit conditions
                    if self.check_exit_conditions(df, position['side']):
                        self.close_position(position)
                    
                    # Check take profit
                    self.manage_take_profit(position, current_price)
                
                # Check for new entry signals if we can place new trades
                if self.can_place_new_trade():
                    signals = self.check_entry_conditions(df)
                    
                    if signals['long']:
                        self.place_order('long', current_price, atr_value)
                    
                    if signals['short']:
                        self.place_order('short', current_price, atr_value)
                
                # Sleep until next iteration
                time.sleep(self.config.check_interval)
                
            except Exception as e:
                logger.error(f"Error in strategy run loop: {e}")
                time.sleep(30)
    
    def stop(self):
        """
        Stop the strategy.
        """
        self.running = False
        logger.info(f"Stopping EMA-MACD strategy for {self.symbol}")
    
    def backtest(self, start_date, end_date):
        """
        Run a backtest for the strategy.
        
        Args:
            start_date: Start date for backtest
            end_date: End date for backtest
            
        Returns:
            dict: Backtest results
        """
        logger.info(f"Running backtest from {start_date} to {end_date}")
        
        try:
            # Get historical data
            raw_data = self.data_client.get_historical_klines(
                self.symbol,
                self.timeframe,
                start_date,
                end_date
            )
            
            # Convert to dataframe
            df = pd.DataFrame(raw_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Convert string values to float
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # Calculate indicators
            df = self.calculate_indicators(df)
            
            # Initialize backtest variables
            equity = self.config.initial_capital
            positions = []
            trades = []
            
            # Run backtest
            for i in range(max(self.slow_ema, self.macd_slow, self.atr_period) + 10, len(df)):
                # Get data up to current point
                current_data = df.iloc[:i+1]
                current_row = current_data.iloc[-1]
                
                # Check for exit signals first
                for pos in positions[:]:
                    # Check stop loss
                    if pos['side'] == 'long' and current_row['low'] <= pos['stop_loss']:
                        trades.append({
                            'entry_price': pos['entry_price'],
                            'exit_price': pos['stop_loss'],
                            'side': pos['side'],
                            'profit_pct': (pos['stop_loss'] / pos['entry_price'] - 1) * 100 if pos['side'] == 'long' else (pos['entry_price'] / pos['stop_loss'] - 1) * 100,
                            'exit_type': 'stop_loss',
                            'exit_time': current_row['timestamp']
                        })
                        positions.remove(pos)
                    elif pos['side'] == 'short' and current_row['high'] >= pos['stop_loss']:
                        trades.append({
                            'entry_price': pos['entry_price'],
                            'exit_price': pos['stop_loss'],
                            'side': pos['side'],
                            'profit_pct': (pos['entry_price'] / pos['stop_loss'] - 1) * 100 if pos['side'] == 'short' else (pos['stop_loss'] / pos['entry_price'] - 1) * 100,
                            'exit_type': 'stop_loss',
                            'exit_time': current_row['timestamp']
                        })
                        positions.remove(pos)
                    
                    # Check take profit 2
                    elif pos['side'] == 'long' and current_row['high'] >= pos['take_profit_2']:
                        trades.append({
                            'entry_price': pos['entry_price'],
                            'exit_price': pos['take_profit_2'],
                            'side': pos['side'],
                            'profit_pct': (pos['take_profit_2'] / pos['entry_price'] - 1) * 100,
                            'exit_type': 'take_profit_2',
                            'exit_time': current_row['timestamp']
                        })
                        positions.remove(pos)
                    elif pos['side'] == 'short' and current_row['low'] <= pos['take_profit_2']:
                        trades.append({
                            'entry_price': pos['entry_price'],
                            'exit_price': pos['take_profit_2'],
                            'side': pos['side'],
                            'profit_pct': (pos['entry_price'] / pos['take_profit_2'] - 1) * 100,
                            'exit_type': 'take_profit_2',
                            'exit_time': current_row['timestamp']
                        })
                        positions.remove(pos)
                    
                    # Check exit conditions
                    elif self.check_exit_conditions(current_data, pos['side']):
                        trades.append({
                            'entry_price': pos['entry_price'],
                            'exit_price': current_row['close'],
                            'side': pos['side'],
                            'profit_pct': (current_row['close'] / pos['entry_price'] - 1) * 100 if pos['side'] == 'long' else (pos['entry_price'] / current_row['close'] - 1) * 100,
                            'exit_type': 'signal',
                            'exit_time': current_row['timestamp']
                        })
                        positions.remove(pos)
                
                # Check entry conditions if we have fewer than max_open_orders positions
                if len(positions) < self.max_open_orders:
                    signals = self.check_entry_conditions(current_data)
                    
                    if signals['long']:
                        # Calculate position size (1% of equity per trade)
                        position_size = equity * 0.01 / (current_row['close'] * self.sl_atr_multiplier / 100)
                        
                        # Add position
                        positions.append({
                            'entry_price': current_row['close'],
                            'side': 'long',
                            'size': position_size,
                            'stop_loss': current_row['close'] - (current_row['atr'] * self.sl_atr_multiplier),
                            'take_profit_1': current_row['close'] + (current_row['atr'] * self.tp1_atr_multiplier),
                            'take_profit_2': current_row['close'] + (current_row['atr'] * self.tp2_atr_multiplier),
                            'entry_time': current_row['timestamp']
                        })
                    
                    if signals['short']:
                        # Calculate position size (1% of equity per trade)
                        position_size = equity * 0.01 / (current_row['close'] * self.sl_atr_multiplier / 100)
                        
                        # Add position
                        positions.append({
                            'entry_price': current_row['close'],
                            'side': 'short',
                            'size': position_size,
                            'stop_loss': current_row['close'] + (current_row['atr'] * self.sl_atr_multiplier),
                            'take_profit_1': current_row['close'] - (current_row['atr'] * self.tp1_atr_multiplier),
                            'take_profit_2': current_row['close'] - (current_row['atr'] * self.tp2_atr_multiplier),
                            'entry_time': current_row['timestamp']
                        })
            
            # Close any remaining positions at the end of the backtest
            for pos in positions:
                trades.append({
                    'entry_price': pos['entry_price'],
                    'exit_price': df['close'].iloc[-1],
                    'side': pos['side'],
                    'profit_pct': (df['close'].iloc[-1] / pos['entry_price'] - 1) * 100 if pos['side'] == 'long' else (pos['entry_price'] / df['close'].iloc[-1] - 1) * 100,
                    'exit_type': 'end_of_backtest',
                    'exit_time': df['timestamp'].iloc[-1]
                })
            
            # Calculate backtest metrics
            total_trades = len(trades)
            winning_trades = sum(1 for t in trades if t['profit_pct'] > 0)
            losing_trades = sum(1 for t in trades if t['profit_pct'] <= 0)
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            total_profit_pct = sum(t['profit_pct'] for t in trades)
            avg_profit_pct = total_profit_pct / total_trades if total_trades > 0 else 0
            
            # Calculate final equity
            final_equity = self.config.initial_capital * (1 + total_profit_pct / 100)
            
            # Calculate drawdown
            equity_curve = [self.config.initial_capital]
            for t in trades:
                equity_curve.append(equity_curve[-1] * (1 + t['profit_pct'] / 100))
            
            max_equity = self.config.initial_capital
            max_drawdown = 0
            
            for equity_point in equity_curve:
                max_equity = max(max_equity, equity_point)
                drawdown = (max_equity - equity_point) / max_equity * 100
                max_drawdown = max(max_drawdown, drawdown)
            
            # Return results
            results = {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_return': total_profit_pct,
                'avg_profit_per_trade': avg_profit_pct,
                'max_drawdown': max_drawdown,
                'final_equity': final_equity,
                'trades': trades
            }
            
            logger.info(f"Backtest completed: {results}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'avg_profit_per_trade': 0,
                'max_drawdown': 0,
                'final_equity': self.config.initial_capital,
                'trades': []
            } 