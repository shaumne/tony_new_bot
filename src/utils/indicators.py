def is_around_vwap_band(price, band_value, threshold=0.001):
    """
    Check if price is around a specific VWAP band value within the threshold
    
    Args:
        price (float): Current price
        band_value (float): VWAP band value (lower, middle, upper)
        threshold (float): Threshold percentage (default 0.1%)
    
    Returns:
        bool: True if price is within threshold of the band
    """
    # Calculate threshold range based on band value
    threshold_value = band_value * threshold
    
    # Check if price is within range
    return abs(price - band_value) <= threshold_value

def detect_ema_crossover(current_short, current_long, previous_short, previous_long):
    """
    Detect EMA crossover
    
    Args:
        current_short (float): Current short-term EMA value
        current_long (float): Current long-term EMA value
        previous_short (float): Previous short-term EMA value
        previous_long (float): Previous long-term EMA value
    
    Returns:
        int: 1 for bullish crossover, -1 for bearish crossover, 0 for no crossover
    """
    # Bullish crossover: short EMA crosses above long EMA
    if previous_short <= previous_long and current_short > current_long:
        return 1
    # Bearish crossover: short EMA crosses below long EMA
    elif previous_short >= previous_long and current_short < current_long:
        return -1
    # No crossover
    else:
        return 0

def detect_macd_crossover(current_macd, current_signal, previous_macd, previous_signal):
    """
    Detect MACD crossover
    
    Args:
        current_macd (float): Current MACD value
        current_signal (float): Current MACD signal value
        previous_macd (float): Previous MACD value
        previous_signal (float): Previous MACD signal value
    
    Returns:
        int: 1 for bullish crossover, -1 for bearish crossover, 0 for no crossover
    """
    # Bullish crossover: MACD crosses above signal line
    if previous_macd <= previous_signal and current_macd > current_signal:
        return 1
    # Bearish crossover: MACD crosses below signal line
    elif previous_macd >= previous_signal and current_macd < current_signal:
        return -1
    # No crossover
    else:
        return 0 