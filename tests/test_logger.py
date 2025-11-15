"""Unit tests for logger module."""

import unittest
import logging
from leakpy.logger import setup_logger


class TestLogger(unittest.TestCase):
    """Test cases for logger functions."""

    def test_setup_logger(self):
        """Test logger setup."""
        logger = setup_logger("TestLogger", verbose=False)
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "TestLogger")

    def test_setup_logger_verbose(self):
        """Test logger setup with verbose mode."""
        logger = setup_logger("TestLoggerVerbose", verbose=True)
        self.assertEqual(logger.level, logging.DEBUG)

    def test_setup_logger_non_verbose(self):
        """Test logger setup without verbose mode."""
        logger = setup_logger("TestLoggerNormal", verbose=False)
        self.assertEqual(logger.level, logging.INFO)

    def test_logger_handlers(self):
        """Test that logger has handlers."""
        logger = setup_logger("TestLoggerHandlers")
        self.assertTrue(len(logger.handlers) > 0)

    def test_logger_no_propagation(self):
        """Test that logger doesn't propagate."""
        logger = setup_logger("TestLoggerPropagation")
        self.assertFalse(logger.propagate)


if __name__ == "__main__":
    unittest.main()



