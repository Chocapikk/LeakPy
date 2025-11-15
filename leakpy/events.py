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

"""LeakIX event data models and wrappers."""

from l9format import l9format

from . import helpers


# ============================================================================
# CLASSES
# ============================================================================

class _EmptyL9Event:
    """Empty L9Event that allows chaining and evaluates to None.
    
    Allows chaining like leak.geoip.country_name even if geoip doesn't exist.
    Simple and direct - no if checks needed!
    """
    
    def __getattr__(self, name):
        """Return self to allow chaining, but it evaluates to None."""
        return self
    
    def __bool__(self):
        """Evaluate to False (None-like behavior)."""
        return False
    
    def __eq__(self, other):
        """Compare equal to None."""
        return other is None
    
    def __str__(self):
        """String representation - returns empty string for clean output."""
        return ""
    
    def __repr__(self):
        """String representation - returns empty string for clean output."""
        return ""


class L9Event:
    """
    Wrapper class for leak data using the official l9format library.
    Provides simple dot notation access - no need for if checks!
    
    Example:
        leak = L9Event({"protocol": "http", "ip": "1.2.3.4"})
        print(leak.protocol)  # "http"
        print(leak.ip)         # "1.2.3.4"
        print(leak.geoip.country_name)  # None (no error, works directly!)
    """
    
    # Class constants
    _empty = _EmptyL9Event()
    
    # ========================================================================
    # INITIALIZATION
    # ========================================================================
    
    def __init__(self, data):
        """
        Initialize L9Event with a dictionary using the official l9format library.
        
        Args:
            data (dict): Dictionary containing leak data from LeakIX API.
        """
        if not isinstance(data, dict):
            raise TypeError("L9Event requires a dictionary")
        
        # Try to use L9Event.from_dict() first
        @helpers.handle_exceptions(default_return=None, exception_types=(Exception,))
        def _try_create_l9event():
            return l9format.L9Event.from_dict(data)
        
        self._l9event = _try_create_l9event()
        if self._l9event is None:
            # If validation fails, create a simple wrapper with dot notation
            # This handles cases where API data doesn't match the exact L9Event schema
            self._set_attributes_from_dict(data)
    
    # ========================================================================
    # PRIVATE: INITIALIZATION HELPERS
    # ========================================================================
    
    def _set_attributes_from_dict(self, data):
        """Set attributes from dictionary, recursively converting nested dicts."""
        for key, value in data.items():
            setattr(self, key, L9Event(value) if isinstance(value, dict) else value)
    
    # ========================================================================
    # PRIVATE: ATTRIBUTE ACCESS HELPERS
    # ========================================================================
    
    def _get_l9event_attr(self, name):
        """Get attribute from _l9event if available, otherwise return empty."""
        if self._l9event is None:
            return self._empty
        
        @helpers.handle_attribute_errors(default_return=self._empty)
        def _get_value():
            value = getattr(self._l9event, name)
            return self._empty if value is None else value
        
        return _get_value()
    
    def _get_dict_attrs(self):
        """Get dictionary attributes (excluding private ones)."""
        from .helpers.constants import _PRIVATE_PREFIX
        prefix = _PRIVATE_PREFIX
        return {k: v for k, v in self.__dict__.items() if not k.startswith(prefix)}
    
    @helpers.handle_attribute_errors(default_return=None)
    def _get_l9event_dict(self):
        """Get dictionary from _l9event if available, otherwise None."""
        return self._l9event.to_dict() if self._l9event is not None else None
    
    @helpers.handle_attribute_errors(default_return={})
    def _get_dict_representation(self):
        """Get dictionary representation, from _l9event or dict attrs."""
        return self._get_l9event_dict() or self._get_dict_attrs()
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    @helpers.handle_attribute_errors(default_return={})
    def to_dict(self):
        """Return dictionary representation."""
        l9event_dict = self._get_l9event_dict()
        if l9event_dict is not None:
            return l9event_dict
        
        result = {}
        for key, value in self._get_dict_attrs().items():
            result[key] = helpers.to_dict_if_l9event(value)
        return result
    
    # ========================================================================
    # MAGIC METHODS
    # ========================================================================
    
    def __getattr__(self, name):
        """
        Return None for missing attributes, but allow chaining.
        This allows direct access like leak.geoip.country_name to work
        even if geoip doesn't exist - it just returns None.
        Simple and direct - no need for if checks!
        """
        return self._get_l9event_attr(name)
    
    def __repr__(self):
        """String representation of the L9Event."""
        return f"L9Event({self._get_dict_representation()})"






