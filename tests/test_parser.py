"""Unit tests for parser module."""

import unittest
from leakpy.helpers import extract_data_from_json, process_and_format_data
from leakpy.helpers import get_all_fields_from_dict


class TestParser(unittest.TestCase):
    """Test cases for parser functions."""

    def test_extract_data_default_fields(self):
        """Test extraction with default fields (protocol, ip, port)."""
        data = {
            "events": [
                {"protocol": "http", "ip": "1.2.3.4", "port": 80}
            ]
        }
        result = extract_data_from_json(data, None)
        self.assertEqual(len(result), 1)
        # Default fields return protocol, ip, port, and url
        self.assertEqual(result[0].to_dict(), {"protocol": "http", "ip": "1.2.3.4", "port": 80, "url": "http://1.2.3.4:80"})

    def test_extract_data_custom_fields(self):
        """Test extraction with custom fields."""
        data = {
            "events": [
                {"protocol": "http", "ip": "1.2.3.4", "port": 80, "host": "example.com"}
            ]
        }
        result = extract_data_from_json(data, "protocol,host")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].to_dict(), {"protocol": "http", "host": "example.com"})

    def test_extract_data_full(self):
        """Test extraction with 'full' option."""
        data = {
            "events": [
                {"protocol": "http", "ip": "1.2.3.4", "port": 80, "extra": "data"}
            ]
        }
        result = extract_data_from_json(data, "full")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].to_dict(), {"protocol": "http", "ip": "1.2.3.4", "port": 80, "extra": "data"})

    def test_extract_data_nested_fields(self):
        """Test extraction with nested fields."""
        data = {
            "events": [
                {"nested": {"field": "value"}, "simple": "test"}
            ]
        }
        result = extract_data_from_json(data, "nested.field,simple")
        self.assertEqual(len(result), 1)
        # With nested structure, dataset.field becomes dataset.field nested
        self.assertEqual(result[0].simple, "test")
        self.assertEqual(result[0].nested.field, "value")

    def test_extract_data_missing_fields(self):
        """Test extraction with missing fields."""
        data = {
            "events": [
                {"protocol": "http", "ip": "1.2.3.4"}
            ]
        }
        result = extract_data_from_json(data, "protocol,port,missing")
        self.assertEqual(result[0].protocol, "http")
        self.assertEqual(result[0].port, "N/A")
        self.assertEqual(result[0].missing, "N/A")

    def test_get_all_fields(self):
        """Test getting all fields from nested dictionary."""
        data = {
            "protocol": "http",
            "nested": {
                "field": "value",
                "another": "data"
            }
        }
        fields = get_all_fields_from_dict(data)
        expected = ["nested.another", "nested.field", "protocol"]
        self.assertEqual(fields, expected)

    def test_get_all_fields_empty(self):
        """Test getting fields from empty dict."""
        fields = get_all_fields_from_dict({})
        self.assertEqual(fields, [])

    def test_get_all_fields_non_dict(self):
        """Test getting fields from non-dict."""
        fields = get_all_fields_from_dict("not a dict")
        self.assertEqual(fields, [])

    def test_process_and_format_data(self):
        """Test process_and_format_data function."""
        data = {
            "events": [
                {"protocol": "http", "ip": "1.2.3.4", "port": 80}
            ]
        }
        result = process_and_format_data(data, "protocol,ip")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].protocol, "http")
        self.assertEqual(result[0].ip, "1.2.3.4")

    def test_process_and_format_data_full(self):
        """Test process_and_format_data with full option."""
        data = {
            "events": [
                {"protocol": "http", "ip": "1.2.3.4", "port": 80}
            ]
        }
        result = process_and_format_data(data, "full")
        self.assertEqual(len(result), 1)
        # Check that attributes exist using hasattr or direct access
        self.assertIsNotNone(result[0].protocol)
        self.assertIsNotNone(result[0].ip)
        self.assertIsNotNone(result[0].port)


if __name__ == "__main__":
    unittest.main()


