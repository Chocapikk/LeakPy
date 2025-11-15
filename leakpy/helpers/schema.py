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

from .decorators import handle_attribute_errors, handle_exceptions
from .constants import _PARSER_SEPARATOR, _PARSER_MODEL_ATTRS

# Constants for l9format schema extraction
try:
    from l9format import l9format
    
    _SCHEMA_FIELD_TO_MODEL_MAP = {
        'geoip': l9format.GeoLocation,
        'http': l9format.L9HttpEvent,
        'ssl': l9format.L9SSLEvent,
        'ssh': l9format.L9SSHEvent,
        'leak': l9format.L9LeakEvent,
        'service': l9format.L9ServiceEvent,
        'network': l9format.Network,
    }
    
    _SCHEMA_NESTED_FIELD_TO_MODEL_MAP = {
        'certificate': l9format.Certificate,
        'location': l9format.GeoPoint,
        'dataset': l9format.DatasetSummary,
        'header': None,  # Dict-like, extract keys dynamically
        'credentials': l9format.ServiceCredentials,
        'software': l9format.Software,
    }
except ImportError:
    l9format = None
    _SCHEMA_FIELD_TO_MODEL_MAP = {}
    _SCHEMA_NESTED_FIELD_TO_MODEL_MAP = {}


def _is_valid_schema_model(model_cls, current_class):
    """Check if a model class is valid (not self-reference)."""
    if not l9format:
        return False
    return model_cls != current_class and model_cls != l9format.L9Event


@handle_attribute_errors(default_return=None)
def _get_model_from_field_obj(field_obj, model_class):
    """Extract model from field object attributes (_model_cls or model)."""
    for attr_name in _PARSER_MODEL_ATTRS:
        if hasattr(field_obj, attr_name):
            model = getattr(field_obj, attr_name)
            if model and _is_valid_schema_model(model, model_class):
                return model
    return None


def _get_model_for_schema_field(field_name, prefix, field_obj, model_class):
    """Get the model class for a field, checking multiple sources."""
    # First, check if the field name itself maps to a known model
    if field_name in _SCHEMA_FIELD_TO_MODEL_MAP:
        return _SCHEMA_FIELD_TO_MODEL_MAP[field_name]
    
    # Check nested field map
    if prefix and field_name in _SCHEMA_NESTED_FIELD_TO_MODEL_MAP:
        nested_model = _SCHEMA_NESTED_FIELD_TO_MODEL_MAP[field_name]
        if nested_model:
            return nested_model
    
    # Try to get model from field object
    return _get_model_from_field_obj(field_obj, model_class)


def _is_model_already_visited(model_class, visited):
    """Check if model class has already been visited."""
    model_id = id(model_class)
    if model_id in visited:
        return True
    visited.add(model_id)
    return False


@handle_attribute_errors(default_return=[])
def extract_fields_from_l9format_schema(model_class, prefix="", visited=None):
    """Recursively extract fields from a model class.
    
    Args:
        model_class: The model class to extract fields from
        prefix: Current field path prefix
        visited: Set of already visited model classes to prevent infinite recursion
    """
    if not hasattr(model_class, '_fields'):
        return []
    
    visited = visited or set()
    if _is_model_already_visited(model_class, visited):
        return []  # Already processed, skip to avoid infinite recursion
    
    nested_fields = []
    for field_name, field_obj in model_class._fields.items():
        full_path = f"{prefix}{_PARSER_SEPARATOR}{field_name}" if prefix else field_name
        nested_fields.append(full_path)
        
        # Check if this field maps to a known model
        model_to_check = _get_model_for_schema_field(field_name, prefix, field_obj, model_class)
        
        if model_to_check and model_to_check != model_class:
            # Recursively extract nested fields
            deeper = extract_fields_from_l9format_schema(model_to_check, full_path, visited.copy())
            nested_fields.extend(deeper)
    
    return nested_fields

