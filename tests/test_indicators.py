"""
Tests for technical indicators.
"""
import unittest
import numpy as np
import pandas as pd

from src.indicators.technical_indicators import (
    calculate_ema, calculate_macd, calculate_vwap, calculate_atr,
    detect_ema_crossover, detect_macd_crossover, is_around_vwap_band
)


class TestIndicators(unittest.TestCase):
    """Tests for technical indicators."""
    
    def setUp(self):
        """Set up test data."""
        # Create sample OHLCV data
        self.data = pd.DataFrame({
            'open': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
            'high': [105, 106, 107, 108, 109, 110, 111, 112, 113, 114],
            'low': [95, 96, 97, 98, 99, 100, 101, 102, 103, 104],
            'close': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
        })
    
    def test_calculate_ema(self):
        """Test EMA calculation."""
        ema = calculate_ema(self.data, 3)
        self.assertEqual(len(ema), len(self.data))
        self.assertIsInstance(ema, pd.Series)
        
        # First value should match the first close price
        self.assertAlmostEqual(ema.iloc[0], self.data['close'].iloc[0])
        
        # EMA should smooth the data
        self.assertTrue(np.std(ema) <= np.std(self.data['close']))
    
    def test_calculate_macd(self):
        """Test MACD calculation."""
        macd_line, macd_signal, macd_hist = calculate_macd(self.data, 3, 6, 2)
        
        self.assertEqual(len(macd_line), len(self.data))
        self.assertEqual(len(macd_signal), len(self.data))
        self.assertEqual(len(macd_hist), len(self.data))
        
        # Earlier values may be NaN due to calculation window
        self.assertTrue(np.isnan(macd_line.iloc[0]))
        
        # Later values should be valid
        self.assertFalse(np.isnan(macd_line.iloc[-1]))
        self.assertFalse(np.isnan(macd_signal.iloc[-1]))
        self.assertFalse(np.isnan(macd_hist.iloc[-1]))
    
    def test_calculate_vwap(self):
        """Test VWAP calculation."""
        vwap_middle, vwap_upper, vwap_lower = calculate_vwap(self.data, 5)
        
        self.assertEqual(len(vwap_middle), len(self.data))
        self.assertEqual(len(vwap_upper), len(self.data))
        self.assertEqual(len(vwap_lower), len(self.data))
        
        # VWAP should be between low and high prices
        for i in range(len(self.data)):
            if not np.isnan(vwap_middle.iloc[i]):
                self.assertTrue(
                    self.data['low'].iloc[i] <= vwap_upper.iloc[i] or 
                    np.isclose(self.data['low'].iloc[i], vwap_upper.iloc[i])
                )
                self.assertTrue(
                    vwap_lower.iloc[i] <= self.data['high'].iloc[i] or 
                    np.isclose(vwap_lower.iloc[i], self.data['high'].iloc[i])
                )
        
        # Upper band should be above middle, lower below middle
        for i in range(len(self.data)):
            if not np.isnan(vwap_middle.iloc[i]):
                self.assertTrue(vwap_upper.iloc[i] >= vwap_middle.iloc[i])
                self.assertTrue(vwap_lower.iloc[i] <= vwap_middle.iloc[i])
    
    def test_calculate_atr(self):
        """Test ATR calculation."""
        atr = calculate_atr(self.data, 5)
        
        self.assertEqual(len(atr), len(self.data))
        
        # ATR should be positive
        for i in range(len(atr)):
            if not np.isnan(atr.iloc[i]):
                self.assertTrue(atr.iloc[i] > 0)
    
    def test_detect_ema_crossover(self):
        """Test EMA crossover detection."""
        # Test bullish crossover
        short_ema = 102
        long_ema = 101
        previous_short_ema = 100
        previous_long_ema = 101
        
        result = detect_ema_crossover(short_ema, long_ema, previous_short_ema, previous_long_ema)
        self.assertEqual(result, 1)
        
        # Test bearish crossover
        short_ema = 100
        long_ema = 101
        previous_short_ema = 101
        previous_long_ema = 100
        
        result = detect_ema_crossover(short_ema, long_ema, previous_short_ema, previous_long_ema)
        self.assertEqual(result, -1)
        
        # Test no crossover
        short_ema = 102
        long_ema = 100
        previous_short_ema = 101
        previous_long_ema = 99
        
        result = detect_ema_crossover(short_ema, long_ema, previous_short_ema, previous_long_ema)
        self.assertEqual(result, 0)
    
    def test_detect_macd_crossover(self):
        """Test MACD crossover detection."""
        # Test bullish crossover
        macd = 1
        signal = 0
        previous_macd = -1
        previous_signal = 0
        
        result = detect_macd_crossover(macd, signal, previous_macd, previous_signal)
        self.assertEqual(result, 1)
        
        # Test bearish crossover
        macd = -1
        signal = 0
        previous_macd = 1
        previous_signal = 0
        
        result = detect_macd_crossover(macd, signal, previous_macd, previous_signal)
        self.assertEqual(result, -1)
        
        # Test no crossover
        macd = 2
        signal = 0
        previous_macd = 1
        previous_signal = 0
        
        result = detect_macd_crossover(macd, signal, previous_macd, previous_signal)
        self.assertEqual(result, 0)
    
    def test_is_around_vwap_band(self):
        """Test VWAP band proximity check."""
        # Test price near middle band
        price = 100
        vwap_middle = 100.1
        vwap_upper = 105
        vwap_lower = 95
        threshold = 0.002
        
        is_near, band = is_around_vwap_band(price, vwap_middle, vwap_upper, vwap_lower, threshold)
        self.assertTrue(is_near)
        self.assertEqual(band, "middle")
        
        # Test price near upper band
        price = 104.9
        
        is_near, band = is_around_vwap_band(price, vwap_middle, vwap_upper, vwap_lower, threshold)
        self.assertTrue(is_near)
        self.assertEqual(band, "upper")
        
        # Test price near lower band
        price = 95.1
        
        is_near, band = is_around_vwap_band(price, vwap_middle, vwap_upper, vwap_lower, threshold)
        self.assertTrue(is_near)
        self.assertEqual(band, "lower")
        
        # Test price not near any band
        price = 97
        
        is_near, band = is_around_vwap_band(price, vwap_middle, vwap_upper, vwap_lower, threshold)
        self.assertFalse(is_near)
        self.assertIsNone(band)


if __name__ == '__main__':
    unittest.main() 