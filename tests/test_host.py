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

"""Unit tests for host details functionality."""

import unittest
from unittest.mock import Mock, patch, MagicMock

from leakpy.leakix import LeakIX
from leakpy.api import LeakIXAPI
from leakpy.events import L9Event


class TestHostDetails(unittest.TestCase):
    """Tests for host details functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.fake_api_key = "a" * 48
        self.client = LeakIX(api_key=self.fake_api_key, silent=True)

    def test_get_host_structure(self):
        """Test that get_host returns correct structure."""
        # Mock API response
        mock_data = {
            "Services": [
                {
                    "ip": "1.2.3.4",
                    "port": 80,
                    "protocol": "http",
                    "host": "example.com"
                }
            ],
            "Leaks": None
        }
        
        with patch.object(self.client.api, 'get_host_details', return_value=(mock_data, False)):
            result = self.client.get_host("1.2.3.4")
            
            self.assertIsNotNone(result)
            self.assertIsNotNone(result.services)
            self.assertIsNone(result.leaks)

    def test_get_host_with_services_and_leaks(self):
        """Test get_host with both services and leaks."""
        mock_data = {
            "Services": [
                {"ip": "1.2.3.4", "port": 80, "protocol": "http"}
            ],
            "Leaks": [
                {"ip": "1.2.3.4", "leak": {"type": "database", "severity": "high"}}
            ]
        }
        
        with patch.object(self.client.api, 'get_host_details', return_value=(mock_data, False)):
            result = self.client.get_host("1.2.3.4")
            
            self.assertIsNotNone(result.services)
            self.assertIsNotNone(result.leaks)
            self.assertEqual(len(result.services), 1)
            self.assertEqual(len(result.leaks), 1)

    def test_get_host_no_data(self):
        """Test get_host when no data is found."""
        with patch.object(self.client.api, 'get_host_details', return_value=(None, False)):
            result = self.client.get_host("1.2.3.4")
            
            self.assertIsNotNone(result)
            self.assertIsNone(result.services)
            self.assertIsNone(result.leaks)

    def test_get_host_empty_services_and_leaks(self):
        """Test get_host with empty services and leaks."""
        mock_data = {
            "Services": None,
            "Leaks": None
        }
        
        with patch.object(self.client.api, 'get_host_details', return_value=(mock_data, False)):
            result = self.client.get_host("1.2.3.4")
            
            self.assertIsNone(result.services)
            self.assertIsNone(result.leaks)

    def test_get_host_with_fields(self):
        """Test get_host with specific fields."""
        mock_data = {
            "Services": [
                {"ip": "1.2.3.4", "port": 80, "protocol": "http", "host": "example.com"}
            ],
            "Leaks": None
        }
        
        with patch.object(self.client.api, 'get_host_details', return_value=(mock_data, False)):
            result = self.client.get_host("1.2.3.4", fields="protocol,ip,port")
            
            self.assertIsNotNone(result.services)
            # Services should be processed with specified fields
            self.assertIsInstance(result.services, list)

    def test_get_host_api_method(self):
        """Test the API method get_host_details."""
        api = LeakIXAPI(self.fake_api_key, verbose=False)
        
        # Mock the _make_request method
        mock_response = Mock()
        mock_response.text = '{"Services": [{"ip": "1.2.3.4"}], "Leaks": null}'
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.headers = {}
        
        with patch('leakpy.helpers.fetch.make_api_request', return_value=mock_response):
            with patch.object(api, 'cache', None):  # Disable cache for test
                result, cached = api.get_host_details("1.2.3.4", suppress_logs=True)
                
                self.assertIsNotNone(result)
                self.assertIn('Services', result)
                self.assertIn('Leaks', result)
                self.assertFalse(cached)

    def test_get_host_rate_limited(self):
        """Test get_host when rate limited - API handles it automatically."""
        api = LeakIXAPI(self.fake_api_key, verbose=False)
        
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'x-limited-for': '60'}
        mock_response.raise_for_status = Mock()
        
        with patch('leakpy.helpers.fetch.make_api_request', return_value=mock_response):
            with patch.object(api, 'cache', None):
                result, cached = api.get_host_details("1.2.3.4", suppress_logs=True)
                
                # API returns special marker for rate limit
                self.assertIsNotNone(result)
                self.assertIn('_rate_limited', result)
                self.assertEqual(result['_wait_seconds'], 60)
                self.assertFalse(cached)

    def test_get_host_with_output_file(self):
        """Test get_host with output file."""
        import tempfile
        import os
        
        mock_data = {
            "Services": [
                {"ip": "1.2.3.4", "port": 80, "protocol": "http"}
            ],
            "Leaks": None
        }
        
        with patch.object(self.client.api, 'get_host_details', return_value=(mock_data, False)):
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                temp_file = f.name
            
            try:
                result = self.client.get_host("1.2.3.4", output=temp_file)
                
                # Check that file was created and has content
                self.assertTrue(os.path.exists(temp_file))
                with open(temp_file, 'r') as f:
                    content = f.read()
                    self.assertIn('1.2.3.4', content)
                
                self.assertIsNotNone(result)
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()

