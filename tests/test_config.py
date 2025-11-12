"""Unit tests for config module."""

import unittest
import tempfile
import os
from pathlib import Path
from leakpy.config import APIKeyManager, get_config_dir


class TestConfig(unittest.TestCase):
    """Test cases for config functions."""

    def test_get_config_dir(self):
        """Test getting config directory."""
        config_dir = get_config_dir()
        self.assertIsInstance(config_dir, Path)
        self.assertTrue(config_dir.exists())

    def test_api_key_manager_save_and_read(self):
        """Test saving and reading API key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the config dir
            original_init = APIKeyManager.__init__
            def mock_init(self):
                self.api_key_file = Path(tmpdir) / "api_key.txt"
                # Initialize _use_keyring attribute
                try:
                    import keyring
                    self._use_keyring = True
                except ImportError:
                    self._use_keyring = False
            
            APIKeyManager.__init__ = mock_init
            
            manager = APIKeyManager()
            test_key = "test_api_key_123456789012345678901234567890123456"
            manager.save(test_key)
            
            read_key = manager.read()
            self.assertEqual(read_key, test_key)
            
            APIKeyManager.__init__ = original_init

    def test_api_key_manager_is_valid(self):
        """Test API key validation."""
        manager = APIKeyManager()
        
        # Valid key (48 characters)
        valid_key = "a" * 48
        self.assertTrue(manager.is_valid(valid_key))
        
        # Invalid keys
        self.assertFalse(manager.is_valid(""))
        self.assertFalse(manager.is_valid(None))
        self.assertFalse(manager.is_valid("short"))
        self.assertFalse(manager.is_valid("a" * 47))
        self.assertFalse(manager.is_valid("a" * 49))

    def test_api_key_manager_read_nonexistent(self):
        """Test reading non-existent API key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_init = APIKeyManager.__init__
            def mock_init(self):
                self.api_key_file = Path(tmpdir) / "nonexistent_key.txt"
                # Initialize _use_keyring attribute
                try:
                    import keyring
                    self._use_keyring = True
                except ImportError:
                    self._use_keyring = False
            
            APIKeyManager.__init__ = mock_init
            
            manager = APIKeyManager()
            result = manager.read()
            self.assertIsNone(result)
            
            APIKeyManager.__init__ = original_init


if __name__ == "__main__":
    unittest.main()

