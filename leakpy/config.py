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

"""Configuration management for LeakPy."""

from pathlib import Path

from . import helpers

# Try to import keyring for secure storage
try:
    import keyring  # type: ignore
except ImportError:
    keyring = None  # type: ignore


class APIKeyManager:
    """Manages API key storage and retrieval with secure storage support."""
    
    SERVICE_NAME = "LeakPy"
    USERNAME = "api_key"
    
    def __init__(self):
        """Initialize the API key manager."""
        config_dir = helpers.get_config_dir()
        self.api_key_file = config_dir / "api_key.txt"
        self._use_keyring = keyring is not None
    
    
    
    def _try_keyring_operation(self, operation, *args, **kwargs):
        """
        Try a keyring operation, falling back to file storage if it fails.
        
        Args:
            operation: Function to call (e.g., keyring.set_password, keyring.get_password)
            *args, **kwargs: Arguments to pass to the operation
            
        Returns:
            Result of the operation, or None if it fails.
        """
        @helpers.handle_exceptions(default_return=None, exception_types=(Exception,))
        def _execute():
            if not self._use_keyring:
                return None
            result = operation(*args, **kwargs)
            return result
        
        result = _execute()
        if result is None and self._use_keyring:
            # If keyring fails, disable it and fall back to file storage
            self._use_keyring = False
        return result
    
    def _remove_old_file_storage(self):
        """Remove old file-based storage when using keyring."""
        helpers.delete_file_safe(self.api_key_file)
    
    def _save_to_keyring(self, api_key):
        """Save API key to keyring if available."""
        if not keyring:
            return False
        return self._try_keyring_operation(
            keyring.set_password, self.SERVICE_NAME, self.USERNAME, api_key
        ) is not None
    
    def save(self, api_key):
        """
        Save the API key securely.
        
        Uses keyring if available (secure system keychain), otherwise falls back
        to file storage with restrictive permissions.
        """
        if self._save_to_keyring(api_key):
            self._remove_old_file_storage()
            return
        
        helpers.write_file_safe(self.api_key_file, api_key, restrict_permissions=True)
    
    def _read_from_keyring(self):
        """Read API key from keyring if available."""
        if not self._use_keyring or not keyring:
            return None
        key = self._try_keyring_operation(
            keyring.get_password, self.SERVICE_NAME, self.USERNAME
        )
        return key.strip() if key else None
    
    def read(self):
        """
        Retrieve the API key from secure storage.
        
        Tries keyring first, then falls back to file storage.
        """
        return self._read_from_keyring() or helpers.read_file_safe(self.api_key_file)
    
    def migrate_old_location(self):
        """Migrate API key from old location (~/.local/.api.txt) to new location."""
        old_path = Path.home() / ".local" / ".api.txt"
        old_key = helpers.read_file_safe(old_path)
        if old_key:
            self.save(old_key)
            return old_key
        return None
    
    @helpers.handle_exceptions(default_return=None, exception_types=(Exception,))
    def _delete_from_keyring(self):
        """Delete API key from keyring if available."""
        if not self._use_keyring or not keyring:
            return
        keyring.delete_password(self.SERVICE_NAME, self.USERNAME)
    
    def delete(self):
        """
        Delete the stored API key from secure storage.
        
        Removes from keyring if used, or deletes the file.
        """
        self._delete_from_keyring()
        helpers.delete_file_safe(self.api_key_file)
    
    def is_valid(self, api_key):
        """Check if an API key is valid (48 characters)."""
        return bool(api_key) and len(api_key) == 48


class CacheConfig:
    """Manages cache configuration (TTL)."""
    
    CONFIG_FILE = "cache_config.json"
    
    def __init__(self):
        """Initialize the cache configuration manager."""
        self.config_dir = helpers.get_config_dir()
        self.config_file = self.config_dir / self.CONFIG_FILE
    
    def _read_config(self):
        """Read configuration from file."""
        return helpers.read_json_file(self.config_file)
    
    def _write_config(self, config):
        """Write configuration to file."""
        helpers.write_json_file(self.config_file, config, ensure_dir=True)
    
    def get_ttl_minutes(self):
        """Get the configured TTL in minutes, or None if not set."""
        config = self._read_config()
        return config.get('ttl_minutes')
    
    def set_ttl_minutes(self, minutes):
        """Set the TTL in minutes."""
        config = self._read_config()
        config['ttl_minutes'] = minutes
        self._write_config(config)

