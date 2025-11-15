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

import json
from functools import wraps
from ..api import LeakIXAPI

# ============================================================================
# DECORATORS
# ============================================================================

def handle_exceptions(default_return=None, exception_types=(Exception,)):
    """Decorator to handle specific exceptions with default return."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types:
                return default_return
        return wrapper
    return decorator


# Specialized exception handlers using handle_exceptions
handle_file_errors = lambda default_return=None: handle_exceptions(default_return, (IOError, OSError, json.JSONDecodeError))
handle_key_errors = lambda default_return=None: handle_exceptions(default_return, (KeyError, TypeError))
handle_attribute_errors = lambda default_return=None: handle_exceptions(default_return, (AttributeError,))


def ensure_api_initialized(api, api_key, log_func):
    """Ensure API client is initialized."""
    return api or LeakIXAPI(api_key, False, log_func)


def require_api_key(func):
    """Decorator to require valid API key before executing method."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.has_api_key():
            raise ValueError("A valid API key is required.")
        if not self.api:
            self.api = ensure_api_initialized(self.api, self.api_key, self.log)
        return func(self, *args, **kwargs)
    return wrapper

