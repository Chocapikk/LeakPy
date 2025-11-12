# Unit Tests for LeakPy

This directory contains unit tests for LeakPy.

## Structure

- `test_parser.py` : Tests for the parser module
- `test_config.py` : Tests for configuration management
- `test_logger.py` : Tests for the logging system
- `run_tests.py` : Script to run all tests

## Running Tests

### All tests
```bash
python3 tests/run_tests.py
```

### Specific test file
```bash
python3 -m unittest tests.test_parser
python3 -m unittest tests.test_config
python3 -m unittest tests.test_logger
```

### Specific test
```bash
python3 -m unittest tests.test_parser.TestParser.test_extract_data_full
```

### Verbose mode
```bash
python3 -m unittest -v tests.test_parser
```

## Adding New Tests

1. Create a new file `test_<module>.py` in the `tests/` directory
2. Import `unittest` and the module to test
3. Create a class that inherits from `unittest.TestCase`
4. Add methods starting with `test_`

Example:
```python
import unittest
from leakpy.my_module import my_function

class TestMyModule(unittest.TestCase):
    def test_my_function(self):
        result = my_function("input")
        self.assertEqual(result, "expected_output")
```

## Alternative Test Frameworks

- **pytest** : More modern and flexible
  ```bash
  pip install pytest
  pytest tests/
  ```

- **unittest** : Built into Python (currently used)

## Continuous Integration

Tests are automatically run on GitHub Actions when:
- Code is pushed to `main`, `master`, or `develop` branches
- Pull requests are opened

See `.github/workflows/` for CI configuration.

