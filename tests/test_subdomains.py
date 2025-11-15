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

"""Unit tests for subdomains functionality."""

import unittest
from unittest.mock import Mock, patch, MagicMock

from leakpy.leakix import LeakIX
from leakpy.api import LeakIXAPI


class TestSubdomains(unittest.TestCase):
    """Tests for subdomains functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.fake_api_key = "a" * 48
        self.client = LeakIX(api_key=self.fake_api_key, silent=True)

    def test_get_subdomains_structure(self):
        """Test that get_subdomains returns correct structure."""
        # Mock API response
        mock_data = [
            {
                "subdomain": "www.example.com",
                "distinct_ips": 1,
                "last_seen": "2023-01-20T11:25:41.243Z"
            },
            {
                "subdomain": "blog.example.com",
                "distinct_ips": 2,
                "last_seen": "2023-01-20T11:23:03.404Z"
            }
        ]
        
        with patch.object(self.client.api, 'get_subdomains', return_value=(mock_data, False)):
            result = self.client.get_subdomains("example.com")
            
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 2)
            self.assertIsNotNone(result[0].subdomain)
            self.assertIsNotNone(result[0].distinct_ips)
            self.assertIsNotNone(result[0].last_seen)

    def test_get_subdomains_empty(self):
        """Test get_subdomains when no subdomains found."""
        with patch.object(self.client.api, 'get_subdomains', return_value=(None, False)):
            result = self.client.get_subdomains("example.com")
            
            self.assertEqual(result, [])

    def test_get_subdomains_empty_list(self):
        """Test get_subdomains with empty list."""
        mock_data = []
        
        with patch.object(self.client.api, 'get_subdomains', return_value=(mock_data, False)):
            result = self.client.get_subdomains("example.com")
            
            self.assertEqual(result, [])

    def test_get_subdomains_api_method(self):
        """Test the API method get_subdomains."""
        api = LeakIXAPI(self.fake_api_key, verbose=False)
        
        # Mock the _make_request method
        mock_response = Mock()
        mock_response.text = '[{"subdomain": "www.example.com", "distinct_ips": 1, "last_seen": "2023-01-20T11:25:41.243Z"}]'
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.headers = {}
        
        with patch('leakpy.helpers.fetch.make_api_request', return_value=mock_response):
            with patch.object(api, 'cache', None):  # Disable cache for test
                result, cached = api.get_subdomains("example.com", suppress_logs=True)
                
                # API method returns raw dicts, client.get_subdomains() converts to DotNotationObject
                self.assertIsNotNone(result)
                self.assertIsInstance(result, list)
                self.assertEqual(len(result), 1)
                self.assertIn('subdomain', result[0])  # API returns dicts
                self.assertFalse(cached)

    def test_get_subdomains_rate_limited(self):
        """Test get_subdomains when rate limited - API handles it automatically."""
        api = LeakIXAPI(self.fake_api_key, verbose=False)
        
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'x-limited-for': '60'}
        mock_response.raise_for_status = Mock()
        
        with patch('leakpy.helpers.fetch.make_api_request', return_value=mock_response):
            with patch.object(api, 'cache', None):
                result, cached = api.get_subdomains("example.com", suppress_logs=True)
                
                # API returns special marker for rate limit
                self.assertIsNotNone(result)
                self.assertIn('_rate_limited', result)
                self.assertEqual(result['_wait_seconds'], 60)
                self.assertFalse(cached)

    def test_get_subdomains_with_output_file(self):
        """Test get_subdomains with output file."""
        import tempfile
        import os
        
        mock_data = [
            {
                "subdomain": "www.example.com",
                "distinct_ips": 1,
                "last_seen": "2023-01-20T11:25:41.243Z"
            }
        ]
        
        with patch.object(self.client.api, 'get_subdomains', return_value=(mock_data, False)):
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                temp_file = f.name
            
            try:
                result = self.client.get_subdomains("example.com", output=temp_file)
                
                # Check that file was created and has content
                self.assertTrue(os.path.exists(temp_file))
                with open(temp_file, 'r') as f:
                    content = f.read()
                    self.assertIn('www.example.com', content)
                
                self.assertIsNotNone(result)
                self.assertEqual(len(result), 1)
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

    def test_get_subdomains_invalid_response(self):
        """Test get_subdomains with invalid response format."""
        api = LeakIXAPI(self.fake_api_key, verbose=False)
        
        # Mock response that's not a list
        mock_response = Mock()
        mock_response.text = '{"error": "invalid"}'
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.headers = {}
        
        with patch('leakpy.helpers.fetch.make_api_request', return_value=mock_response):
            with patch.object(api, 'cache', None):
                result, cached = api.get_subdomains("example.com", suppress_logs=True)
                
                self.assertIsNone(result)
                self.assertFalse(cached)


if __name__ == '__main__':
    unittest.main()

