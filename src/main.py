"""
Main entry point for the trading bot application.
"""
import os
import sys
import argparse
import threading
import time
from datetime import datetime

from src.utils.config import Config
from src.utils.logger import setup_logging, create_log_file_path
from src.utils.email_notifier import EmailNotifier
from src.data.bitget_client import BitgetClient
from src.data.tradingview_client import TradingViewClient
from src.strategy.ema_macd_vwap_strategy import EMAMACDVWAPStrategy


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Trading Bot')
    
    parser.add_argument('--mode', type=str, default='live',
                        choices=['live', 'paper', 'backtest'],
                        help='Trading mode: live, paper, or backtest')
    
    parser.add_argument('--env', type=str, default='.env',
                        help='Path to environment file')
    
    parser.add_argument('--backtest-start', type=str,
                        help='Start date for backtesting (YYYY-MM-DD)')
    
    parser.add_argument('--backtest-end', type=str,
                        help='End date for backtesting (YYYY-MM-DD)')
    
    return parser.parse_args()


def setup_clients(config):
    """
    Set up API clients.
    
    Args:
        config: Configuration object
        
    Returns:
        tuple: (bitget_client, tradingview_client)
    """
    # Initialize Bitget client
    bitget_client = BitgetClient(
        config.bitget_api_key,
        config.bitget_secret_key,
        config.bitget_passphrase,
        testnet=(config.trading_mode == 'paper')
    )
    
    # Initialize TradingView client
    tradingview_client = TradingViewClient(
        config.symbol
    )
    
    return bitget_client, tradingview_client


def setup_email_notifier(config):
    """
    Set up email notifier.
    
    Args:
        config: Configuration object
        
    Returns:
        EmailNotifier or None
    """
    if config.email_enabled:
        return EmailNotifier(
            config.email_sender,
            config.email_password,
            config.email_recipient,
            config.email_smtp_server,
            config.email_smtp_port
        )
    return None


def run_trading_bot(config):
    """
    Run the trading bot.
    
    Args:
        config: Configuration object
    """
    # Set up clients
    bitget_client, tradingview_client = setup_clients(config)
    
    # Set up email notifier
    email_notifier = setup_email_notifier(config)
    
    # Initialize strategy
    strategy = EMAMACDVWAPStrategy(
        bitget_client,
        tradingview_client,
        config,
        email_notifier
    )
    
    # Run strategy in a separate thread
    strategy_thread = threading.Thread(target=strategy.run)
    strategy_thread.daemon = True
    strategy_thread.start()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Stop strategy on keyboard interrupt
        strategy.stop()
        print("Trading bot stopped")


def run_backtest(config, start_date, end_date):
    """
    Run backtest.
    
    Args:
        config: Configuration object
        start_date: Start date
        end_date: End date
    """
    # Set up clients
    bitget_client, tradingview_client = setup_clients(config)
    
    # Initialize strategy
    strategy = EMAMACDVWAPStrategy(
        bitget_client,
        tradingview_client,
        config,
        None  # No email notifications for backtest
    )
    
    # Run backtest
    results = strategy.backtest(start_date, end_date)
    
    # Print results
    print("\nBacktest Results:")
    print(f"Symbol: {config.symbol}")
    print(f"Timeframe: {config.timeframe}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Total Trades: {results.get('total_trades', 0)}")
    print(f"Win Rate: {results.get('win_rate', 0):.2f}%")
    print(f"Total Return: {results.get('total_return', 0):.2f}%")
    print(f"Max Drawdown: {results.get('max_drawdown', 0):.2f}%")
    print(f"Final Equity: {results.get('final_equity', 0):.2f}")


def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging
    log_file = create_log_file_path("trading_bot")
    logger = setup_logging("INFO", log_file)
    
    # Load configuration
    config = Config(args.env)
    
    # Eğer komut satırında paper modu belirtilmişse, config'i güncelle
    if args.mode == 'paper':
        config.trading_mode = 'paper'
        logger.info("Setting trading mode to paper trading")
    
    # Validate configuration
    if not config.validate():
        logger.error("Invalid configuration. Please check your settings.")
        sys.exit(1)
    
    # Log configuration
    logger.info(f"Configuration loaded: {config}")
    
    # Run in appropriate mode
    if args.mode == 'live' or args.mode == 'paper':
        logger.info(f"Starting trading bot in {args.mode} mode")
        run_trading_bot(config)
    else:  # backtest
        # Get start and end dates
        start_date = args.backtest_start or config.backtest_start_date
        end_date = args.backtest_end or config.backtest_end_date
        
        logger.info(f"Starting backtest from {start_date} to {end_date}")
        run_backtest(config, start_date, end_date)


if __name__ == "__main__":
    main() 