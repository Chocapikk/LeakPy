"""Logging configuration for LeakPy."""

import logging
import sys


def setup_logger(name="LeakPy", verbose=False, level=None):
    """
    Setup and configure the logger.
    
    Args:
        name (str): Logger name.
        verbose (bool): Enable verbose logging (DEBUG level).
        level: Optional logging level override.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Determine logging level (DRY: calculate once, use multiple times)
    log_level = logging.DEBUG if verbose else (level or logging.INFO)
    
    logger.setLevel(log_level)
    
    # Console handler with custom format
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Clean format: LEVEL: message (no timestamp for cleaner output)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger

