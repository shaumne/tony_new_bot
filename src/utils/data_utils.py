def generate_tradingview_data(num_candles=500, timeframe='15m'):
    """
    Generate synthetic OHLCV data for testing with more realistic market movements
    
    Args:
        num_candles (int): Number of candles to generate
        timeframe (str): Timeframe for the candles
        
    Returns:
        list: List of OHLCV candles
    """
    import numpy as np
    from datetime import datetime, timedelta
    import logging
    
    logging.info(f"Generating {num_candles} synthetic candles for {timeframe} timeframe")
    
    # Convert timeframe to minutes for timestamp calculation
    tf_minutes = 0
    if timeframe.endswith('m'):
        tf_minutes = int(timeframe[:-1])
    elif timeframe.endswith('h'):
        tf_minutes = int(timeframe[:-1]) * 60
    elif timeframe.endswith('d'):
        tf_minutes = int(timeframe[:-1]) * 1440
    
    # Start with a base price around 30000 (similar to BTC)
    base_price = 30000
    
    # Create timestamps (most recent first as per Bitget API)
    end_time = datetime.now()
    timestamps = [(end_time - timedelta(minutes=i * tf_minutes)).timestamp() * 1000 for i in range(num_candles)]
    timestamps.reverse()  # Oldest first
    
    # Generate price data with trends and volatility
    prices = []
    current_price = base_price
    
    # Create some trend periods
    trend_length = 50  # Length of trend periods
    num_trends = (num_candles // trend_length) + 1
    
    # Generate trends with different slopes
    trends = []
    for i in range(num_trends):
        # Alternate between bullish and bearish trends with different strengths
        if i % 2 == 0:
            trend = np.random.uniform(0.001, 0.005)  # Bullish trend
        else:
            trend = np.random.uniform(-0.005, -0.001)  # Bearish trend
        trends.extend([trend] * min(trend_length, num_candles - len(trends)))
    
    # Generate price data
    for i in range(num_candles):
        # Apply the trend factor
        trend_factor = 1 + trends[i]
        
        # Add noise/volatility
        volatility = np.random.normal(0, 0.01)
        
        # Update price with trend and volatility
        current_price *= (trend_factor + volatility)
        
        # Add some random spikes for crossover opportunities (every ~25 candles)
        if i % 25 == 0:
            spike_direction = 1 if np.random.random() > 0.5 else -1
            current_price *= (1 + spike_direction * np.random.uniform(0.01, 0.03))
        
        prices.append(current_price)
    
    # Generate OHLCV data
    ohlcv_data = []
    for i in range(num_candles):
        timestamp = int(timestamps[i])
        
        # Calculate price range for this candle
        price = prices[i]
        range_percent = np.random.uniform(0.005, 0.02)  # 0.5% to 2% range
        
        # Determine if candle is bullish or bearish
        is_bullish = np.random.random() > 0.5
        
        if is_bullish:
            open_price = price * (1 - np.random.uniform(0, range_percent/2))
            close_price = price * (1 + np.random.uniform(0, range_percent/2))
            high_price = close_price * (1 + np.random.uniform(0, range_percent/4))
            low_price = open_price * (1 - np.random.uniform(0, range_percent/4))
        else:
            open_price = price * (1 + np.random.uniform(0, range_percent/2))
            close_price = price * (1 - np.random.uniform(0, range_percent/2))
            high_price = open_price * (1 + np.random.uniform(0, range_percent/4))
            low_price = close_price * (1 - np.random.uniform(0, range_percent/4))
        
        # Volume varies with price movement
        volume = np.random.uniform(10, 100) * (abs(close_price - open_price) / price)
        
        ohlcv_data.append([
            timestamp,  # timestamp
            float(open_price),  # open
            float(high_price),  # high
            float(low_price),   # low
            float(close_price), # close
            float(volume)       # volume
        ])
    
    logging.info(f"Generated {len(ohlcv_data)} synthetic candles with realistic market movements")
    return ohlcv_data 