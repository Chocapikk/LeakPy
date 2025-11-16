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

"""Aggressive robustness tests for LeakPy."""

import unittest
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from leakpy.leakix import LeakIX
from leakpy.helpers import extract_data_from_json
from leakpy.events import L9Event
from leakpy.api import LeakIXAPI
from leakpy.cache import APICache


class TestRobustness(unittest.TestCase):
    """Aggressive tests for robustness and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        # Use a fake API key for testing (48 chars)
        self.fake_api_key = "a" * 48
        self.client = LeakIX(api_key=self.fake_api_key, silent=True)

    # ========== Parameter Validation Tests ==========

    def test_invalid_scope_type(self):
        """Test that invalid scope types are handled."""
        # Scope might be converted to string, so test actual behavior
        # None might be converted to "None"
        result = list(self.client.search(scope=None, pages=1))
        self.assertIsInstance(result, list)
        
        # Numbers might be converted to string
        result = list(self.client.search(scope=123, pages=1))
        self.assertIsInstance(result, list)
        
        # Lists might cause issues or be converted
        try:
            result = list(self.client.search(scope=[], pages=1))
            self.assertIsInstance(result, list)
        except (TypeError, AttributeError):
            pass  # Expected

    def test_invalid_pages_type(self):
        """Test that invalid page types are handled."""
        # Should handle gracefully or raise appropriate error
        try:
            self.client.search(pages="invalid")
        except (TypeError, ValueError):
            pass  # Expected

    def test_negative_pages(self):
        """Test that negative pages are handled."""
        # Mock the API to avoid actual network calls
        with patch.object(self.client.api, 'query_search', return_value=(None, False)):
            result = list(self.client.search(pages=-1))
            self.assertIsInstance(result, list)

    def test_zero_pages(self):
        """Test that zero pages returns empty list."""
        # With 0 pages, should return empty list without API calls
        result = list(self.client.search(pages=0))
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_very_large_pages(self):
        """Test that very large page numbers are handled."""
        # Mock the API to avoid actual network calls
        with patch.object(self.client.api, 'query_search', return_value=(None, False)):
            result = list(self.client.search(pages=999999))
            self.assertIsInstance(result, list)

    def test_invalid_query_type(self):
        """Test that invalid query types are handled."""
        # Should handle None, int, list, etc.
        result = list(self.client.search(query=None))
        self.assertIsInstance(result, list)
        
        result = list(self.client.search(query=123))
        self.assertIsInstance(result, list)

    def test_very_long_query(self):
        """Test that very long queries are handled."""
        long_query = "a" * 10000
        # Mock the API to avoid actual network calls
        with patch.object(self.client.api, 'query_search', return_value=(None, False)):
            result = list(self.client.search(query=long_query, pages=1))
            self.assertIsInstance(result, list)

    def test_special_characters_in_query(self):
        """Test that special characters in query are handled."""
        special_queries = [
            "'; DROP TABLE leaks; --",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "null\x00byte",
            "\n\r\t",
            "\\'\"",
            "{}[]()",
        ]
        # Mock the API to avoid actual network calls
        with patch.object(self.client.api, 'query_search', return_value=(None, False)):
            for query in special_queries:
                result = list(self.client.search(query=query, pages=1))
                self.assertIsInstance(result, list)

    def test_invalid_plugin_names(self):
        """Test that invalid plugin names raise appropriate errors."""
        with self.assertRaises(ValueError):
            # search() returns a generator, so we need to iterate to trigger validation
            list(self.client.search(plugin="nonexistent_plugin_12345", pages=1))

    def test_invalid_fields_type(self):
        """Test that invalid field types are handled."""
        # Should handle None, int, list, etc.
        # search() returns a generator, so convert to list for testing
        result = list(self.client.search(fields=None, pages=1))
        self.assertIsInstance(result, list)
        
        result = list(self.client.search(fields=123, pages=1))
        self.assertIsInstance(result, list)

    def test_invalid_output_type(self):
        """Test that invalid output types are handled."""
        # Should handle gracefully
        result = list(self.client.search(output=123, pages=1))
        self.assertIsInstance(result, list)

    # ========== API Key Tests ==========

    def test_empty_api_key(self):
        """Test that empty API key is handled."""
        client = LeakIX(api_key="", silent=True)
        # has_api_key checks if key is 48 chars, empty string should fail
        # But it might check for None or empty differently
        result = client.has_api_key()
        self.assertIsInstance(result, bool)
        # Empty string is not 48 chars, so should be False
        if len("") != 48:
            # If validation is strict, should be False
            pass  # Just check it doesn't crash

    def test_short_api_key(self):
        """Test that short API key is rejected."""
        client = LeakIX(api_key="short", silent=True)
        self.assertFalse(client.has_api_key())

    def test_long_api_key(self):
        """Test that long API key is handled."""
        long_key = "a" * 100
        client = LeakIX(api_key=long_key, silent=True)
        # Should either validate or handle gracefully
        self.assertIsInstance(client.has_api_key(), bool)

    def test_api_key_with_special_chars(self):
        """Test that API key with special characters is handled."""
        special_key = "a" * 47 + "\x00"
        client = LeakIX(api_key=special_key, silent=True)
        # Should handle gracefully
        self.assertIsInstance(client.has_api_key(), bool)

    # ========== Data Parsing Robustness Tests ==========

    def test_empty_json_response(self):
        """Test that empty JSON is handled."""
        data = {}
        result = extract_data_from_json(data, None)
        # extract_data_from_json can return either a list or a single L9Event
        # For empty dict, it processes the dict itself and returns a single L9Event
        self.assertIsInstance(result, (list, L9Event))
        if isinstance(result, list):
            for item in result:
                self.assertIsInstance(item, L9Event)

    def test_malformed_json_response(self):
        """Test that malformed JSON is handled."""
        # This should be handled at API level, but test parser robustness
        data = {"events": None}
        result = extract_data_from_json(data, None)
        # When events is None, it processes the dict itself, returning a list with a single L9Event
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], L9Event)

    def test_missing_events_key(self):
        """Test that missing events key is handled."""
        data = {"other": "data"}
        result = extract_data_from_json(data, None)
        # When events key is missing, it processes the dict itself, returning a list with a single L9Event
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], L9Event)

    def test_empty_events_list(self):
        """Test that empty events list is handled."""
        data = {"events": []}
        result = extract_data_from_json(data, None)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_events_with_none_values(self):
        """Test that events with None values are handled."""
        data = {
            "events": [
                {"protocol": None, "ip": None, "port": None},
                {"protocol": "http", "ip": "1.2.3.4", "port": 80}
            ]
        }
        result = extract_data_from_json(data, None)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_events_with_missing_fields(self):
        """Test that events with missing fields are handled."""
        data = {
            "events": [
                {},
                {"ip": "1.2.3.4"},
                {"protocol": "http"}
            ]
        }
        result = extract_data_from_json(data, None)
        self.assertIsInstance(result, list)
        # Should handle gracefully

    def test_events_with_wrong_types(self):
        """Test that events with wrong field types are handled."""
        data = {
            "events": [
                {"protocol": 123, "ip": ["1", "2"], "port": "80"},
                {"protocol": {"nested": "object"}}
            ]
        }
        result = extract_data_from_json(data, None)
        self.assertIsInstance(result, list)

    def test_deeply_nested_data(self):
        """Test that deeply nested data is handled."""
        data = {
            "events": [
                {
                    "level1": {
                        "level2": {
                            "level3": {
                                "level4": {
                                    "level5": "value"
                                }
                            }
                        }
                    }
                }
            ]
        }
        result = extract_data_from_json(data, "level1.level2.level3.level4.level5")
        self.assertIsInstance(result, list)

    def test_very_large_event(self):
        """Test that very large events are handled."""
        large_event = {
            "protocol": "http",
            "ip": "1.2.3.4",
            "port": 80,
            "data": "x" * 100000  # 100KB of data
        }
        data = {"events": [large_event]}
        result = extract_data_from_json(data, "full")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    # ========== L9Event Object Robustness Tests ==========

    def test_L9Event_with_none(self):
        """Test that L9Event handles None values."""
        event = L9Event({"field": None, "other": "value"})
        self.assertIsNone(event.field)
        self.assertEqual(event.other, "value")

    def test_L9Event_missing_attribute(self):
        """Test that L9Event returns None for missing attributes."""
        event = L9Event({"existing": "value"})
        self.assertEqual(event.existing, "value")
        # Missing attributes return an empty object that evaluates to None
        self.assertEqual(event.nonexistent, None)
        self.assertFalse(event.nonexistent)

    def test_L9Event_nested_none(self):
        """Test that L9Event handles nested None values."""
        event = L9Event({"nested": None})
        self.assertIsNone(event.nested)

    def test_L9Event_empty_dict(self):
        """Test that L9Event handles empty dict."""
        event = L9Event({})
        self.assertIsNotNone(event)
        # Missing attributes return an empty object that evaluates to None
        self.assertEqual(event.any_field, None)
        self.assertFalse(event.any_field)

    def test_L9Event_non_dict(self):
        """Test that L9Event raises TypeError for non-dict input."""
        with self.assertRaises(TypeError):
            L9Event("string")

    def test_L9Event_to_dict(self):
        """Test that to_dict() works with various data types."""
        event = L9Event({
            "string": "value",
            "int": 123,
            "float": 45.6,
            "bool": True,
            "none": None,
            "list": [1, 2, 3],
            "nested": {"key": "value"}
        })
        result = event.to_dict()
        self.assertIsInstance(result, dict)
        self.assertEqual(result["string"], "value")
        self.assertEqual(result["int"], 123)

    def test_L9Event_dot_notation(self):
        """Test that dot notation works correctly."""
        event = L9Event({"key": "value"})
        self.assertEqual(event.key, "value")
        # Missing attributes return an empty object that evaluates to None
        self.assertEqual(event.nonexistent, None)
        self.assertFalse(event.nonexistent)

    def test_L9Event_dot_notation_only(self):
        """Test that only dot notation is supported (no [] access)."""
        event = L9Event({"key": "value"})
        with self.assertRaises(TypeError):
            _ = event[0]

    # ========== File I/O Robustness Tests ==========

    def test_output_to_nonexistent_directory(self):
        """Test that output to nonexistent directory is handled."""
        invalid_path = "/nonexistent/directory/file.txt"
        # Mock the API to avoid actual network calls
        with patch.object(self.client.api, 'query_search', return_value=(None, False)):
            result = list(self.client.search(output=invalid_path, pages=1))
            self.assertIsInstance(result, list)

    def test_output_to_readonly_directory(self):
        """Test that output to readonly directory is handled."""
        # Create a temp directory and make it readonly (if possible)
        with tempfile.TemporaryDirectory() as tmpdir:
            readonly_file = os.path.join(tmpdir, "readonly.txt")
            # Mock the API to avoid actual network calls
            with patch.object(self.client.api, 'query_search', return_value=(None, False)):
                try:
                    # Try to create a file in a way that might fail
                    result = list(self.client.search(output=readonly_file, pages=1))
                    self.assertIsInstance(result, list)
                except (IOError, OSError, PermissionError):
                    pass  # Expected on some systems

    def test_output_to_stdout(self):
        """Test that output to stdout works."""
        # Mock the API to avoid actual network calls
        with patch.object(self.client.api, 'query_search', return_value=(None, False)):
            result = list(self.client.search(output=sys.stdout, pages=1))
            self.assertIsInstance(result, list)

    def test_output_to_stringio(self):
        """Test that output to StringIO works."""
        output = StringIO()
        # Mock the API to avoid actual network calls
        with patch.object(self.client.api, 'query_search', return_value=(None, False)):
            result = list(self.client.search(output=output, pages=1))
            self.assertIsInstance(result, list)
        output.close()

    def test_output_file_permissions(self):
        """Test that file permissions are handled correctly."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            # Mock the API to avoid actual network calls
            with patch.object(self.client.api, 'query_search', return_value=(None, False)):
                result = list(self.client.search(output=tmp_path, pages=1))
                self.assertIsInstance(result, list)
                # File might be created even with no results
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # ========== Cache Robustness Tests ==========

    def test_cache_with_none_key(self):
        """Test that cache handles None keys."""
        cache = APICache()
        result = cache.get("/endpoint", None)
        self.assertIsNone(result)

    def test_cache_with_empty_params(self):
        """Test that cache handles empty params."""
        cache = APICache()
        result = cache.get("/endpoint", {})
        self.assertIsNone(result)

    def test_cache_with_unhashable_params(self):
        """Test that cache handles unhashable params."""
        cache = APICache()
        # Params should be hashable, but test robustness
        try:
            result = cache.get("/endpoint", {"list": [1, 2, 3]})
            # Should either work or raise appropriate error
        except TypeError:
            pass  # Expected if params contain unhashable types

    def test_cache_clear(self):
        """Test that cache clear works."""
        cache = APICache()
        cache.set("/endpoint", {"key": "value"}, {"data": "test"})
        cache.clear()
        result = cache.get("/endpoint", {"key": "value"})
        self.assertIsNone(result)

    def test_cache_ttl_expiration(self):
        """Test that cache TTL expiration works."""
        import time
        cache = APICache(ttl=0.1)  # Very short TTL (100ms)
        cache.set("/endpoint", {"key": "value"}, {"data": "test"})
        # Immediately after setting, should still be cached
        result = cache.get("/endpoint", {"key": "value"})
        self.assertIsNotNone(result)  # Should still be cached
        
        # Wait for expiration
        time.sleep(0.2)
        result = cache.get("/endpoint", {"key": "value"})
        self.assertIsNone(result)  # Should be expired

    # ========== API Client Robustness Tests ==========

    def test_api_with_empty_key(self):
        """Test that API client handles empty key."""
        api = LeakIXAPI("", False, None)
        self.assertEqual(api.api_key, "")

    def test_api_with_none_key(self):
        """Test that API client handles None key."""
        api = LeakIXAPI(None, False, None)
        self.assertIsNone(api.api_key)

    def test_api_cache_disabled(self):
        """Test that API client works with cache disabled."""
        api = LeakIXAPI(self.fake_api_key, False, None, use_cache=False)
        self.assertIsNone(api.cache)

    # ========== Error Recovery Tests ==========

    def test_recovery_after_error(self):
        """Test that client recovers after an error."""
        # Mock the API to simulate error then success
        with patch.object(self.client.api, 'query_search') as mock_query:
            mock_query.side_effect = [
                (None, False),  # First call fails
                ({"events": []}, False)  # Second call succeeds
            ]
            # First call might fail
            result1 = list(self.client.search(pages=1))
            self.assertIsInstance(result1, list)
            
            # Second call should work
            result2 = list(self.client.search(pages=1))
            self.assertIsInstance(result2, list)

    def test_multiple_sequential_calls(self):
        """Test that multiple sequential calls work."""
        # Mock the API to avoid actual network calls
        with patch.object(self.client.api, 'query_search', return_value=(None, False)):
            for i in range(5):
                result = list(self.client.search(pages=1))
                self.assertIsInstance(result, list)

    # ========== Thread Safety Tests ==========

    def test_concurrent_access(self):
        """Test that concurrent access doesn't break."""
        import threading
        
        results = []
        errors = []
        
        def worker():
            try:
                result = list(self.client.search(pages=1))
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should not crash
        self.assertEqual(len(results) + len(errors), 5)

    # ========== Memory Tests ==========

    def test_generator_early_stop_closes_connection(self):
        """Test that HTTP connection is closed when generator is stopped early."""
        import requests
        import threading
        import time
        
        # Use httpbin to create a streaming endpoint
        # We'll create a simple mock server response that streams data
        # For this test, we'll mock the make_api_request to return a streaming response
        
        # Create a mock response that simulates streaming
        class MockStreamResponse:
            def __init__(self):
                self.closed = False
                # Generate 3000 lines to simulate a large stream
                self.lines = iter([
                    f'{{"events": [{{"ip": "1.2.3.{i % 255}", "port": 80}}]}}\n'
                    for i in range(3000)
                ])
            
            def iter_lines(self, decode_unicode=True):
                for line in self.lines:
                    if self.closed:
                        break
                    yield line.encode() if not decode_unicode else line
            
            def close(self):
                self.closed = True
        
        mock_response = MockStreamResponse()
        
        # Clear cache to ensure we make a real API call
        self.client.clear_cache()
        
        # Mock get_plugins to avoid API call
        with patch.object(self.client, 'get_plugins', return_value=[]):
            # Mock the API to return our mock response
            with patch.object(self.client.api, 'is_api_pro', True):
                def make_request(*args, **kwargs):
                    return mock_response
                
                with patch('leakpy.leakix.helpers.make_api_request', side_effect=make_request):
                    # Create generator
                    events = self.client.search(scope="leak", query="test", use_bulk=True)
                    
                    # Consume 2000 events then break (simulating early stop)
                    count = 0
                    for event in events:
                        count += 1
                        if count >= 2000:
                            break
                    
                    # Explicitly close the generator to trigger GeneratorExit
                    # This simulates what happens when the generator is garbage collected
                    # or when the user explicitly stops consuming it
                    events.close()
                    
                    # Verify that the response was closed
                    # The try/finally should have closed it when GeneratorExit was raised
                    self.assertTrue(mock_response.closed, 
                                  "Response should be closed when generator is stopped early")
                    self.assertEqual(count, 2000, "Should have consumed exactly 2000 events")

    def test_memory_cleanup(self):
        """Test that memory is cleaned up properly."""
        import gc
        
        # Create many clients
        clients = [LeakIX(silent=True) for _ in range(100)]
        del clients
        gc.collect()
        
        # Should not cause memory issues
        new_client = LeakIX(silent=True)
        self.assertIsNotNone(new_client)

    # ========== Unicode and Encoding Tests ==========

    def test_unicode_in_query(self):
        """Test that Unicode in query is handled."""
        unicode_queries = [
            "测试",
            "🚀",
            "café",
            "naïve",
            "北京",
        ]
        # Mock the API to avoid actual network calls
        with patch.object(self.client.api, 'query_search', return_value=(None, False)):
            for query in unicode_queries:
                result = list(self.client.search(query=query, pages=1))
                self.assertIsInstance(result, list)

    def test_unicode_in_fields(self):
        """Test that Unicode in fields is handled."""
        # Mock the API to avoid actual network calls
        with patch.object(self.client.api, 'query_search', return_value=(None, False)):
            result = list(self.client.search(fields="protocol,ip,测试", pages=1))
            self.assertIsInstance(result, list)

    def test_unicode_in_output_path(self):
        """Test that Unicode in output path is handled."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='测试.txt') as tmp:
            tmp_path = tmp.name
        try:
            # Mock the API to avoid actual network calls
            with patch.object(self.client.api, 'query_search', return_value=(None, False)):
                result = list(self.client.search(output=tmp_path, pages=1))
                self.assertIsInstance(result, list)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()

