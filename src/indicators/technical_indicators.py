"""
Technical indicators for trading strategy.
"""
import numpy as np
import pandas as pd
import ta


def calculate_ema(data, period):
    """
    Calculate Exponential Moving Average.
    
    Args:
        data (pd.DataFrame): DataFrame with 'close' column
        period (int): EMA period
        
    Returns:
        pd.Series: EMA values
    """
    ema = ta.trend.ema_indicator(data['close'], window=period)
    # İlk değeri kapanış fiyatıyla doldur
    ema.iloc[0] = data['close'].iloc[0]
    return ema


def calculate_macd(data, fast_period, slow_period, signal_period):
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        data (pd.DataFrame): DataFrame with 'close' column
        fast_period (int): MACD fast period
        slow_period (int): MACD slow period
        signal_period (int): MACD signal period
        
    Returns:
        tuple: (MACD line, MACD signal, MACD histogram)
    """
    macd_line = ta.trend.macd(data['close'], window_slow=slow_period, window_fast=fast_period)
    macd_signal = ta.trend.macd_signal(data['close'], window_slow=slow_period, 
                                       window_fast=fast_period, window_sign=signal_period)
    macd_diff = ta.trend.macd_diff(data['close'], window_slow=slow_period, 
                                  window_fast=fast_period, window_sign=signal_period)
    
    return macd_line, macd_signal, macd_diff


def calculate_vwap(data, period=14):
    """
    Calculate VWAP (Volume Weighted Average Price) with bands.
    
    Args:
        data (pd.DataFrame): DataFrame with 'high', 'low', 'close', and 'volume' columns
        period (int): VWAP period
        
    Returns:
        tuple: (VWAP, upper band, lower band)
    """
    if 'volume' not in data.columns:
        raise ValueError("DataFrame must have a 'volume' column to calculate VWAP")
    
    # Calculate typical price
    data['typical_price'] = (data['high'] + data['low'] + data['close']) / 3
    
    # Calculate VWAP
    data['vp'] = data['typical_price'] * data['volume']
    data['cumulative_vp'] = data['vp'].rolling(window=period).sum()
    data['cumulative_volume'] = data['volume'].rolling(window=period).sum()
    vwap = data['cumulative_vp'] / data['cumulative_volume']
    
    # Calculate standard deviation for bands
    price_std = data['typical_price'].rolling(window=period).std()
    upper_band = vwap + 2 * price_std
    middle_band = vwap
    lower_band = vwap - 2 * price_std
    
    return middle_band, upper_band, lower_band


def calculate_atr(data, period=14):
    """
    Calculate Average True Range.
    
    Args:
        data (pd.DataFrame): DataFrame with 'high', 'low', 'close' columns
        period (int): ATR period
        
    Returns:
        pd.Series: ATR values
    """
    return ta.volatility.average_true_range(high=data['high'], low=data['low'], 
                                           close=data['close'], window=period)


def detect_ema_crossover(short_ema, long_ema, previous_short_ema, previous_long_ema):
    """
    Detect EMA crossover.
    
    Args:
        short_ema (float): Current short period EMA
        long_ema (float): Current long period EMA
        previous_short_ema (float): Previous short period EMA
        previous_long_ema (float): Previous long period EMA
        
    Returns:
        int: 1 for bullish crossover, -1 for bearish crossover, 0 for no crossover
    """
    # Bullish crossover (short crosses above long)
    if previous_short_ema <= previous_long_ema and short_ema > long_ema:
        return 1
    # Bearish crossover (short crosses below long)
    elif previous_short_ema >= previous_long_ema and short_ema < long_ema:
        return -1
    # No crossover
    else:
        return 0


def detect_macd_crossover(macd, signal, previous_macd, previous_signal):
    """
    Detect MACD crossover.
    
    Args:
        macd (float): Current MACD line
        signal (float): Current MACD signal line
        previous_macd (float): Previous MACD line
        previous_signal (float): Previous MACD signal line
        
    Returns:
        int: 1 for bullish crossover, -1 for bearish crossover, 0 for no crossover
    """
    # Bullish crossover (MACD crosses above signal)
    if previous_macd <= previous_signal and macd > signal:
        return 1
    # Bearish crossover (MACD crosses below signal)
    elif previous_macd >= previous_signal and macd < signal:
        return -1
    # No crossover
    else:
        return 0


def is_around_vwap_band(price, vwap_middle, vwap_upper, vwap_lower, threshold=0.0015):
    """
    Check if price is around any VWAP band.
    
    Args:
        price (float): Current price
        vwap_middle (float): VWAP middle band
        vwap_upper (float): VWAP upper band
        vwap_lower (float): VWAP lower band
        threshold (float): Percentage threshold to consider "around" the band
        
    Returns:
        tuple: (is_around_any_band (bool), band_name (str))
    """
    # Calculate thresholds
    middle_threshold = vwap_middle * threshold
    upper_threshold = vwap_upper * threshold
    lower_threshold = vwap_lower * threshold
    
    # Check if price is around any band
    if abs(price - vwap_lower) <= lower_threshold:
        return True, "lower"
    elif abs(price - vwap_middle) <= middle_threshold:
        return True, "middle"
    elif abs(price - vwap_upper) <= upper_threshold:
        return True, "upper"
    else:
        return False, None 