#!/usr/bin/env python3
"""Run all unit tests for LeakPy."""

import unittest
import sys
from pathlib import Path

# Add parent directory to path to import leakpy
sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == "__main__":
    # Discover and run all tests
    # Note: Only files matching "test_*.py" are discovered
    # Integration tests like doc_examples_test.py are excluded
    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)



