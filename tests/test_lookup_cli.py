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
OUT OF OR IN CONNECTION WITH THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

"""Tests for lookup CLI commands."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from leakpy.helpers import display_host_info, display_domain_info
from leakpy.events import L9Event


class TestLookupCLI(unittest.TestCase):
    """Test lookup CLI display functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fake_api_key = "fake_api_key_for_testing"
    
    def test_display_host_info_with_limit(self):
        """Test _display_host_info with limit parameter."""
        # Create mock host info with more than 50 services
        services = [L9Event({
            'protocol': 'http',
            'port': 80 + i,
            'host': f'host{i}.example.com',
            'service': {
                'software': {
                    'name': 'Apache',
                    'version': '2.4'
                }
            },
            'http': {'status': 200}
        }) for i in range(60)]
        
        leaks = [L9Event({
            'Ip': '1.2.3.4',
            'resource_id': f'leak{i}.example.com',
            'events': [{
                'event_source': 'TestPlugin',
                'leak': {
                    'type': '',
                    'severity': 'high',
                    'dataset': {'size': 100}
                },
                'host': f'leak{i}.example.com',
                'port': '80'
            }]
        }) for i in range(60)]
        
        # Convert to DotNotationObject format
        from leakpy.leakix import DotNotationObject
        host_info = DotNotationObject({
            'Services': services,
            'Leaks': leaks
        })
        
        # Test with default limit (50)
        with patch('leakpy.helpers.lookup.Console') as mock_console_class:
            mock_console = MagicMock()
            mock_console_class.return_value = mock_console
            
            display_host_info(host_info, '1.2.3.4', limit=50)
            
            # Verify console.print was called (table was displayed)
            self.assertGreater(mock_console.print.call_count, 0)
    
    def test_display_host_info_with_all(self):
        """Test _display_host_info with --all (limit=0)."""
        services = [L9Event({
            'protocol': 'http',
            'port': 80 + i,
            'host': f'host{i}.example.com',
            'service': {
                'software': {
                    'name': 'Apache',
                    'version': '2.4'
                }
            },
            'http': {'status': 200}
        }) for i in range(10)]
        
        leaks = [L9Event({
            'Ip': '1.2.3.4',
            'resource_id': f'leak{i}.example.com',
            'events': [{
                'event_source': 'TestPlugin',
                'leak': {
                    'type': '',
                    'severity': 'high',
                    'dataset': {'size': 100}
                },
                'host': f'leak{i}.example.com',
                'port': '80'
            }]
        }) for i in range(10)]
        
        # Convert to DotNotationObject format
        from leakpy.leakix import DotNotationObject
        host_info = DotNotationObject({
            'Services': services,
            'Leaks': leaks
        })
        
        # Test with limit=0 (all)
        with patch('leakpy.helpers.lookup.Console') as mock_console_class:
            mock_console = MagicMock()
            mock_console_class.return_value = mock_console
            
            display_host_info(host_info, '1.2.3.4', limit=0)
            
            # Verify console.print was called
            self.assertGreater(mock_console.print.call_count, 0)
    
    def test_display_domain_info_with_limit(self):
        """Test _display_domain_info with limit parameter."""
        services = [L9Event({
            'protocol': 'http',
            'port': 80 + i,
            'host': f'host{i}.example.com',
            'ip': '1.2.3.4',
            'service': {
                'software': {
                    'name': 'Apache',
                    'version': '2.4'
                }
            },
            'http': {'status': 200}
        }) for i in range(60)]
        
        leaks = [L9Event({
            'Ip': '1.2.3.4',
            'resource_id': f'leak{i}.example.com',
            'events': [{
                'event_source': 'TestPlugin',
                'leak': {
                    'type': '',
                    'severity': 'high',
                    'dataset': {'size': 100}
                },
                'host': f'leak{i}.example.com',
                'ip': '1.2.3.4',
                'port': '80'
            }]
        }) for i in range(60)]
        
        # Convert to DotNotationObject format
        from leakpy.leakix import DotNotationObject
        domain_info = DotNotationObject({
            'Services': services,
            'Leaks': leaks
        })
        
        # Test with limit=20
        with patch('leakpy.helpers.lookup.Console') as mock_console_class:
            mock_console = MagicMock()
            mock_console_class.return_value = mock_console
            
            display_domain_info(domain_info, 'example.com', limit=20)
            
            # Verify console.print was called
            self.assertGreater(mock_console.print.call_count, 0)
    
    def test_display_domain_info_with_all(self):
        """Test _display_domain_info with --all (limit=0)."""
        services = [L9Event({
            'protocol': 'http',
            'port': 80 + i,
            'host': f'host{i}.example.com',
            'ip': '1.2.3.4',
            'service': {
                'software': {
                    'name': 'Apache',
                    'version': '2.4'
                }
            },
            'http': {'status': 200}
        }) for i in range(10)]
        
        leaks = [L9Event({
            'Ip': '1.2.3.4',
            'resource_id': f'leak{i}.example.com',
            'events': [{
                'event_source': 'TestPlugin',
                'leak': {
                    'type': '',
                    'severity': 'high',
                    'dataset': {'size': 100}
                },
                'host': f'leak{i}.example.com',
                'ip': '1.2.3.4',
                'port': '80'
            }]
        }) for i in range(10)]
        
        # Convert to DotNotationObject format
        from leakpy.leakix import DotNotationObject
        domain_info = DotNotationObject({
            'Services': services,
            'Leaks': leaks
        })
        
        # Test with limit=0 (all)
        with patch('leakpy.helpers.lookup.Console') as mock_console_class:
            mock_console = MagicMock()
            mock_console_class.return_value = mock_console
            
            display_domain_info(domain_info, 'example.com', limit=0)
            
            # Verify console.print was called
            self.assertGreater(mock_console.print.call_count, 0)


if __name__ == '__main__':
    unittest.main()


