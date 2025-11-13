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

import os
from pathlib import Path

# Try to import keyring for secure storage
try:
    import keyring  # type: ignore
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    keyring = None  # type: ignore


def get_config_dir():
    """Get the configuration directory for the current OS."""
    if os.name == "nt":  # Windows
        base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home())
        config_dir = Path(base) / "LeakPy"
    else:  # Linux, macOS, etc.
        base = os.getenv("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        config_dir = Path(base) / "LeakPy"
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


class APIKeyManager:
    """Manages API key storage and retrieval with secure storage support."""
    
    SERVICE_NAME = "LeakPy"
    USERNAME = "api_key"
    
    def __init__(self):
        """Initialize the API key manager."""
        config_dir = get_config_dir()
        self.api_key_file = config_dir / "api_key.txt"
        self._use_keyring = KEYRING_AVAILABLE
    
    def _delete_file_safe(self, file_path):
        """Safely delete a file, ignoring errors."""
        try:
            if file_path.exists():
                file_path.unlink()
        except (IOError, OSError):
            pass
    
    def _read_file_safe(self, file_path):
        """Safely read a file, returning None on error."""
        try:
            if not file_path.exists():
                return None
            return file_path.read_text(encoding="utf-8").strip()
        except (IOError, OSError):
            return None
    
    def _write_file_safe(self, file_path, content):
        """Safely write content to a file with restrictive permissions."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        if os.name != "nt":
            file_path.chmod(0o600)
    
    def _try_keyring_operation(self, operation, *args, **kwargs):
        """
        Try a keyring operation, falling back to file storage if it fails.
        
        Args:
            operation: Function to call (e.g., keyring.set_password, keyring.get_password)
            *args, **kwargs: Arguments to pass to the operation
            
        Returns:
            Result of the operation, or None if it fails.
        """
        if not self._use_keyring:
            return None
        
        try:
            return operation(*args, **kwargs)
        except Exception:
            # If keyring fails, disable it and fall back to file storage
            self._use_keyring = False
            return None
    
    def _remove_old_file_storage(self):
        """Remove old file-based storage when using keyring."""
        self._delete_file_safe(self.api_key_file)
    
    def save(self, api_key):
        """
        Save the API key securely.
        
        Uses keyring if available (secure system keychain), otherwise falls back
        to file storage with restrictive permissions.
        """
        # Try keyring first
        if self._try_keyring_operation(
            keyring.set_password, self.SERVICE_NAME, self.USERNAME, api_key
        ) is not None:
            self._remove_old_file_storage()
            return
        
        # Fallback to file storage
        self._write_file_safe(self.api_key_file, api_key)
    
    def read(self):
        """
        Retrieve the API key from secure storage.
        
        Tries keyring first, then falls back to file storage.
        """
        # Try keyring first
        if self._use_keyring:
            key = self._try_keyring_operation(
                keyring.get_password, self.SERVICE_NAME, self.USERNAME
            )
            if key:
                return key.strip()
        
        # Fallback to file storage
        return self._read_file_safe(self.api_key_file)
    
    def migrate_old_location(self):
        """Migrate API key from old location (~/.local/.api.txt) to new location."""
        old_path = Path.home() / ".local" / ".api.txt"
        old_key = self._read_file_safe(old_path)
        if old_key:
            self.save(old_key)
            return old_key
        return None
    
    def delete(self):
        """
        Delete the stored API key from secure storage.
        
        Removes from keyring if used, or deletes the file.
        """
        # Try to delete from keyring
        if self._use_keyring:
            try:
                keyring.delete_password(self.SERVICE_NAME, self.USERNAME)
            except (keyring.errors.PasswordDeleteError, Exception):
                pass
        
        # Also try to delete file-based storage
        self._delete_file_safe(self.api_key_file)
    
    def is_valid(self, api_key):
        """Check if an API key is valid (48 characters)."""
        return bool(api_key) and len(api_key) == 48


class CacheConfig:
    """Manages cache configuration (TTL)."""
    
    CONFIG_FILE = "cache_config.json"
    
    def __init__(self):
        """Initialize the cache configuration manager."""
        self.config_dir = get_config_dir()
        self.config_file = self.config_dir / self.CONFIG_FILE
    
    def _read_config(self):
        """Read configuration from file."""
        try:
            if self.config_file.exists():
                import json
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError):
            pass
        return {}
    
    def _write_config(self, config):
        """Write configuration to file."""
        try:
            import json
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except (IOError, OSError):
            pass
    
    def get_ttl_minutes(self):
        """Get the configured TTL in minutes, or None if not set."""
        config = self._read_config()
        return config.get('ttl_minutes')
    
    def set_ttl_minutes(self, minutes):
        """Set the TTL in minutes."""
        config = self._read_config()
        config['ttl_minutes'] = minutes
        self._write_config(config)

