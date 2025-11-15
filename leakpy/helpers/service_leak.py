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

def _safe_getattr(obj, attr, default=''):
    """Safely get attribute with default value."""
    return getattr(obj, attr, default) or default


def extract_software_info(service):
    """Extract software information from a service object.
    
    Args:
        service: Service object with potential software information
    
    Returns:
        str: Software name and version, or "N/A" if not available
    """
    if not (hasattr(service, 'service') and service.service and 
            hasattr(service.service, 'software') and service.service.software):
        return "N/A"
    software = service.service.software
    software_name = _safe_getattr(software, 'name')
    software_version = _safe_getattr(software, 'version')
    if software_name:
        return f"{software_name} {software_version}".strip() if software_version else software_name
    return software_version if software_version else "N/A"


def extract_http_status(service):
    """Extract HTTP status from a service object.
    
    Args:
        service: Service object with potential HTTP information
    
    Returns:
        str: HTTP status code, or "N/A" if not available
    """
    return str(service.http.status) if service.http and service.http.status else "N/A"


def extract_leak_info(leak, include_ip=False):
    """Extract leak information from a leak object.
    
    Args:
        leak: Leak object
        include_ip: Whether to include IP address in the result
    
    Returns:
        dict with keys: type, host, port, severity, size, and optionally ip
    """
    defaults = _get_leak_defaults(leak, include_ip)
    if not _has_events(leak):
        return _build_leak_result(defaults, include_ip)
    
    first_event = leak.events[0]
    if isinstance(first_event, dict):
        return _extract_from_dict_event(first_event, defaults, include_ip)
    return _extract_from_l9event(first_event, defaults, include_ip)


def _get_leak_defaults(leak, include_ip):
    """Get default leak values."""
    host = _safe_getattr(leak, 'resource_id')
    if not host and include_ip:
        host = _safe_getattr(leak, 'Ip')
    host = host or "N/A"
    return {
        'type': "N/A",
        'host': host,
        'ip': _safe_getattr(leak, 'Ip') or "N/A" if include_ip else None,
        'port': "N/A",
        'severity': "N/A",
        'size': "N/A"
    }


def _has_events(leak):
    """Check if leak has events."""
    return hasattr(leak, 'events') and leak.events and isinstance(leak.events, list) and len(leak.events) > 0


def _extract_from_dict_event(event, defaults, include_ip):
    """Extract leak info from dict event."""
    leak_info = event.get('leak', {})
    defaults['type'] = leak_info.get('type', '') or event.get('event_source', '') or "N/A"
    defaults['severity'] = leak_info.get('severity', '') or "N/A"
    dataset_info = leak_info.get('dataset', {})
    if dataset_info and dataset_info.get('size'):
        defaults['size'] = str(dataset_info['size'])
    defaults['host'] = event.get('host', '') or defaults['host']
    if include_ip:
        defaults['ip'] = event.get('ip', '') or defaults['ip']
    defaults['port'] = event.get('port', '') or defaults['port']
    return _build_leak_result(defaults, include_ip)


def _extract_from_l9event(event, defaults, include_ip):
    """Extract leak info from L9Event."""
    if hasattr(event, 'leak') and event.leak:
        leak = event.leak
        defaults['type'] = _safe_getattr(leak, 'type') or _safe_getattr(event, 'event_source') or "N/A"
        defaults['severity'] = _safe_getattr(leak, 'severity') or "N/A"
        if hasattr(leak, 'dataset') and leak.dataset:
            size = getattr(leak.dataset, 'size', 0)
            defaults['size'] = str(size) if size else "N/A"
    defaults['host'] = _safe_getattr(event, 'host') or defaults['host']
    if include_ip:
        defaults['ip'] = _safe_getattr(event, 'ip') or defaults['ip']
    port = getattr(event, 'port', '')
    defaults['port'] = str(port) if port else defaults['port']
    return _build_leak_result(defaults, include_ip)


def _build_leak_result(defaults, include_ip):
    """Build final leak result dict."""
    result = {k: v for k, v in defaults.items() if k != 'ip'}
    if include_ip:
        result['ip'] = defaults['ip']
    return result

