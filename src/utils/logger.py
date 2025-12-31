"""
Logging configuration and utilities.

This module provides a consistent logging interface for the entire framework.
"""

import logging
import sys
from .config import config


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Creates or retrieves a logger with the specified name. Configures it
    with appropriate handlers and formatters if not already configured.
    
    Args:
        name: Name for the logger (typically __name__ of calling module)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        # Set logging level from config
        logger.setLevel(getattr(logging, config.log_level.upper()))
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, config.log_level.upper()))
        
        # Create formatter with timestamp and context
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
    
    return logger