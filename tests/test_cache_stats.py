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

"""Unit tests for cache management and query statistics features."""

import unittest
import tempfile
import os
import time
from pathlib import Path

from leakpy.leakix import LeakIX
from leakpy.parser import l9event
from leakpy.cache import APICache
from leakpy.config import CacheConfig
from leakpy.stats import analyze_query_results, get_field_value


class TestCacheManagement(unittest.TestCase):
    """Tests for cache management methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.fake_api_key = "a" * 48
        self.client = LeakIX(api_key=self.fake_api_key, silent=True)
        # Clear cache before each test
        self.client.clear_cache()

    def tearDown(self):
        """Clean up after tests."""
        self.client.clear_cache()

    def test_get_cache_stats_empty(self):
        """Test getting cache stats when cache is empty."""
        stats = self.client.get_cache_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats['total_entries'], 0)
        self.assertEqual(stats['active_entries'], 0)
        self.assertEqual(stats['expired_entries'], 0)
        self.assertIn('ttl_minutes', stats)
        self.assertIn('cache_file_size', stats)
        self.assertIn('cache_file_path', stats)

    def test_get_cache_ttl_default(self):
        """Test getting default cache TTL."""
        ttl = self.client.get_cache_ttl()
        # Should return None if using default, or a number if configured
        self.assertTrue(ttl is None or isinstance(ttl, int))

    def test_set_cache_ttl(self):
        """Test setting cache TTL."""
        # Set TTL to 10 minutes
        self.client.set_cache_ttl(10)
        ttl = self.client.get_cache_ttl()
        self.assertEqual(ttl, 10)
        
        # Set TTL to 30 minutes
        self.client.set_cache_ttl(30)
        ttl = self.client.get_cache_ttl()
        self.assertEqual(ttl, 30)

    def test_set_cache_ttl_invalid(self):
        """Test setting invalid cache TTL raises ValueError."""
        with self.assertRaises(ValueError):
            self.client.set_cache_ttl(0)
        
        with self.assertRaises(ValueError):
            self.client.set_cache_ttl(-5)
        
        with self.assertRaises(ValueError):
            self.client.set_cache_ttl("10")  # Not an int

    def test_clear_cache(self):
        """Test clearing cache."""
        # Add some data to cache
        cache = APICache()
        cache.set("/test", {"q": "test"}, {"data": "test"})
        
        # Clear it
        self.client.clear_cache()
        
        # Verify it's empty
        stats = self.client.get_cache_stats()
        self.assertEqual(stats['total_entries'], 0)


class TestQueryStatistics(unittest.TestCase):
    """Tests for query statistics analysis."""

    def setUp(self):
        """Set up test fixtures."""
        self.fake_api_key = "a" * 48
        self.client = LeakIX(api_key=self.fake_api_key, silent=True)
        
        # Create test results with l9event objects
        self.test_results = [
            l9event({
                "ip": "1.2.3.4",
                "port": 80,
                "protocol": "http",
                "geoip": {"country_name": "France", "city_name": "Paris"}
            }),
            l9event({
                "ip": "5.6.7.8",
                "port": 443,
                "protocol": "https",
                "geoip": {"country_name": "France", "city_name": "Lyon"}
            }),
            l9event({
                "ip": "9.10.11.12",
                "port": 22,
                "protocol": "ssh",
                "geoip": {"country_name": "Germany", "city_name": "Berlin"}
            }),
        ]

    def test_analyze_query_stats_with_strings(self):
        """Test analyze_query_stats with string field paths."""
        stats = self.client.analyze_query_stats(
            self.test_results,
            fields="protocol,port",
            top=10
        )
        
        self.assertEqual(stats.total, 3)
        self.assertIsNotNone(stats.fields.protocol)
        self.assertIsNotNone(stats.fields.port)
        # Convert to dict for value access
        stats_dict = stats.to_dict()
        self.assertEqual(stats_dict['fields']['protocol']['http'], 1)
        self.assertEqual(stats_dict['fields']['protocol']['https'], 1)
        self.assertEqual(stats_dict['fields']['protocol']['ssh'], 1)

    def test_analyze_query_stats_with_callables_dict(self):
        """Test analyze_query_stats with callables (object-oriented approach)."""
        stats = self.client.analyze_query_stats(
            self.test_results,
            fields={
                'country': lambda leak: leak.geoip.country_name if leak.geoip else None,
                'protocol': lambda leak: leak.protocol,
                'port': lambda leak: leak.port
            },
            top=10
        )
        
        self.assertEqual(stats.total, 3)
        self.assertIsNotNone(stats.fields.country)
        self.assertIsNotNone(stats.fields.protocol)
        self.assertIsNotNone(stats.fields.port)
        # Test dot notation access
        self.assertEqual(stats.fields.country.France, 2)
        self.assertEqual(stats.fields.country.Germany, 1)

    def test_analyze_query_stats_with_named_functions(self):
        """Test analyze_query_stats with named functions."""
        def get_country(leak):
            return leak.geoip.country_name if leak.geoip else None
        
        def get_protocol(leak):
            return leak.protocol
        
        stats = self.client.analyze_query_stats(
            self.test_results,
            fields={
                'country': get_country,
                'protocol': get_protocol
            },
            top=10
        )
        
        self.assertEqual(stats.total, 3)
        self.assertIsNotNone(stats.fields.country)
        self.assertIsNotNone(stats.fields.protocol)
        self.assertEqual(stats.fields.country.France, 2)

    def test_analyze_query_stats_with_top_limit(self):
        """Test analyze_query_stats with top limit."""
        # Create many results
        many_results = [
            l9event({"protocol": f"http{i % 3}", "port": i})
            for i in range(20)
        ]
        
        stats = self.client.analyze_query_stats(
            many_results,
            fields="protocol",
            top=2
        )
        
        # Should only have top 2 protocols
        stats_dict = stats.to_dict()
        self.assertLessEqual(len(stats_dict['fields']['protocol']), 2)

    def test_analyze_query_stats_all_fields(self):
        """Test analyze_query_stats with all_fields=True (only works with dicts)."""
        # Convert to dicts for all_fields to work
        dict_results = [
            {"protocol": "http", "port": 80, "ip": "1.2.3.4"},
            {"protocol": "https", "port": 443, "ip": "5.6.7.8"},
        ]
        
        stats = self.client.analyze_query_stats(
            dict_results,
            all_fields=True,
            top=10
        )
        
        self.assertEqual(stats.total, 2)
        stats_dict = stats.to_dict()
        self.assertGreater(len(stats_dict['fields']), 0)

    def test_analyze_query_stats_empty_results(self):
        """Test analyze_query_stats with empty results."""
        stats = self.client.analyze_query_stats([], fields="protocol")
        
        self.assertEqual(stats.total, 0)
        stats_dict = stats.to_dict()
        self.assertEqual(len(stats_dict['fields']), 0)

    def test_analyze_query_stats_with_dict_results(self):
        """Test analyze_query_stats with dict results."""
        dict_results = [
            {"protocol": "http", "port": 80},
            {"protocol": "https", "port": 443},
        ]
        
        stats = self.client.analyze_query_stats(
            dict_results,
            fields="protocol,port"
        )
        
        self.assertEqual(stats.total, 2)
        self.assertIsNotNone(stats.fields.protocol)
        self.assertIsNotNone(stats.fields.port)

    def test_analyze_query_stats_complex_callable(self):
        """Test analyze_query_stats with complex callable logic."""
        def get_port_range(leak):
            if not leak.port:
                return None
            port = int(leak.port) if isinstance(leak.port, str) else leak.port
            if port < 1024:
                return "Well-known"
            elif port < 49152:
                return "Registered"
            else:
                return "Dynamic"
        
        stats = self.client.analyze_query_stats(
            self.test_results,
            fields={
                'port_range': get_port_range,
                'protocol': lambda leak: leak.protocol
            }
        )
        
        self.assertEqual(stats.total, 3)
        self.assertIsNotNone(stats.fields.port_range)
        self.assertIsNotNone(stats.fields.protocol)


class TestStatsHelpers(unittest.TestCase):
    """Tests for stats helper functions."""

    def test_get_field_value_with_l9event(self):
        """Test get_field_value with l9event object."""
        leak = l9event({
            "protocol": "http",
            "geoip": {"country_name": "France"}
        })
        
        # Test simple field
        value = get_field_value(leak, "protocol")
        self.assertEqual(value, "http")
        
        # Test nested field
        value = get_field_value(leak, "geoip.country_name")
        self.assertEqual(value, "France")
        
        # Test missing field
        value = get_field_value(leak, "nonexistent")
        self.assertIsNone(value)

    def test_get_field_value_with_callable(self):
        """Test get_field_value with callable."""
        leak = l9event({"protocol": "http", "port": 80})
        
        # Test with lambda
        value = get_field_value(leak, lambda l: l.protocol)
        self.assertEqual(value, "http")
        
        # Test with function
        def get_port(leak):
            return leak.port
        
        value = get_field_value(leak, get_port)
        self.assertEqual(value, 80)

    def test_get_field_value_with_dict(self):
        """Test get_field_value with dict."""
        data = {
            "protocol": "http",
            "geoip": {"country_name": "France"}
        }
        
        # Test simple field
        value = get_field_value(data, "protocol")
        self.assertEqual(value, "http")
        
        # Test nested field
        value = get_field_value(data, "geoip.country_name")
        self.assertEqual(value, "France")

    def test_analyze_query_results_with_callables(self):
        """Test analyze_query_results function directly with callables."""
        results = [
            l9event({"protocol": "http", "port": 80}),
            l9event({"protocol": "https", "port": 443}),
        ]
        
        stats = analyze_query_results(results, fields_to_analyze={
            'protocol': lambda leak: leak.protocol,
            'port': lambda leak: leak.port
        })
        
        self.assertEqual(stats.total, 2)
        self.assertIsNotNone(stats.fields.protocol)
        self.assertIsNotNone(stats.fields.port)


if __name__ == '__main__':
    unittest.main()

