"""
MIT License

Copyright (c) 2025 Valentin Lobstein (balgogan@protonmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import logging
import sys
from .constants import _DEFAULT_LOGGER_NAME, _LOG_FORMAT


def get_log_function(logger, level):
    """Get appropriate log function from logger."""
    return getattr(logger, level.lower(), logger.info)


def _create_console_handler(log_level):
    """Create and configure console handler with formatter."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    formatter = logging.Formatter(_LOG_FORMAT)
    handler.setFormatter(formatter)
    return handler


def _configure_logger(logger, log_level):
    """Configure logger with level and handler."""
    logger.setLevel(log_level)
    handler = _create_console_handler(log_level)
    logger.addHandler(handler)
    logger.propagate = False


def setup_logger(name=_DEFAULT_LOGGER_NAME, verbose=False, level=None):
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
    
    log_level = logging.DEBUG if verbose else (level or logging.INFO)
    _configure_logger(logger, log_level)
    
    return logger

