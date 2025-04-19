"""
Logging utilities.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(log_level="INFO", log_file=None):
    """
    Set up logging configuration.
    
    Args:
        log_level (str): Logging level
        log_file (str, optional): Log file path
        
    Returns:
        logger: Configured logger
    """
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    # Set up logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Convert string log level to logging level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    # Set up handlers
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=handlers
    )
    
    # Get logger
    logger = logging.getLogger()
    
    # Add filter to remove duplicate logs
    for handler in logger.handlers:
        handler.addFilter(lambda record: record.getMessage() != "")
    
    logger.info(f"Logging initialized with level {log_level}")
    
    return logger


def get_logger(name, log_level="INFO"):
    """
    Get a logger for a specific module.
    
    Args:
        name (str): Logger name
        log_level (str): Logging level
        
    Returns:
        logger: Configured logger
    """
    logger = logging.getLogger(name)
    
    # Convert string log level to logging level
    numeric_level = getattr(logging, log_level.upper(), None)
    if isinstance(numeric_level, int):
        logger.setLevel(numeric_level)
    
    return logger


def create_log_file_path(strategy_name="trading_bot"):
    """
    Create a log file path with date.
    
    Args:
        strategy_name (str): Strategy name for the log file
        
    Returns:
        str: Log file path
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create log file name with date
    date_str = datetime.now().strftime("%Y%m%d")
    log_file = logs_dir / f"{strategy_name}_{date_str}.log"
    
    return str(log_file) 