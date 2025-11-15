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

from .constants import _ENCODING_UTF8, _MODE_WRITE
from .data_utils import to_dict_if_needed
from .decorators import handle_file_errors
from pathlib import Path
import json
import os

@handle_file_errors()
def delete_file_safe(file_path):
    """Safely delete a file, ignoring errors."""
    file_path.unlink(missing_ok=True)


@handle_file_errors(default_return=None)
def read_file_safe(file_path, encoding=None):
    """Safely read a file, returning None on error."""
    encoding = encoding or _ENCODING_UTF8
    if not file_path.exists():
        return None
    return file_path.read_text(encoding=encoding).strip()


@handle_file_errors()
def write_file_safe(file_path, content, encoding=None, restrict_permissions=False):
    """Safely write content to a file with optional restrictive permissions."""
    encoding = encoding or _ENCODING_UTF8
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding=encoding)
    if restrict_permissions and os.name != "nt":
        file_path.chmod(0o600)

# ============================================================================
# FILE INPUT UTILITIES
# ============================================================================

def load_lines_from_file(file_path, skip_comments=True, skip_empty=True):
    """Load lines from a text file.
    
    Args:
        file_path: Path to the file (str or Path)
        skip_comments: Whether to skip lines starting with '#' (default: True)
        skip_empty: Whether to skip empty lines (default: True)
    
    Returns:
        list: List of non-empty lines (stripped)
    
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    with open(file_path, 'r', encoding=_ENCODING_UTF8) as f:
        return [
            stripped for line in f
            if (stripped := line.strip()) and (not skip_empty or stripped) and (not skip_comments or not stripped.startswith('#'))
        ]


@handle_file_errors(default_return=[])
def load_results_from_file(file_path):
    """Load results from a JSON file."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding=_ENCODING_UTF8) as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    
    for key in ('events', 'results'):
        if key in data and isinstance(data[key], list):
            return data[key]
    
    for value in data.values():
        if isinstance(value, list):
            return value
    return []

# ============================================================================
# FILE OUTPUT UTILITIES
# ============================================================================

@handle_file_errors(default_return=(None, False))
def open_output_file(output_path, silent, log_func):
    """Open output file and return file handle and close flag."""
    output_file = open(output_path, _MODE_WRITE, encoding=_ENCODING_UTF8)
    if not silent:
        log_func(f"Writing results to {output_path}...", "info")
    return output_file, True


def get_output_file(output, silent, log_func):
    """Get output file handle from output parameter (string path or file object)."""
    if not output:
        return None, False
    
    if isinstance(output, str):
        return open_output_file(output, silent, log_func)
    else:
        # It's already a file object (e.g., sys.stdout)
        if not silent:
            log_func("Writing results to stdout...", "info")
        return output, False


def write_json_line(file_handle, obj):
    """Write object as JSON line to file."""
    obj_dict = to_dict_if_needed(obj)
    file_handle.write(f"{json.dumps(obj_dict)}\n")
    file_handle.flush()


def write_result_item(file_handle, result, fields):
    """Write a single result item to file."""
    if not fields:
        # Use dot notation to access url field
        url = getattr(result, 'url', None)
        if not url:
            result_dict = to_dict_if_needed(result)
            url = result_dict.get('url') if isinstance(result_dict, dict) else None
        if url:
            file_handle.write(f"{url}\n")
        else:
            result_dict = to_dict_if_needed(result)
            file_handle.write(f"{json.dumps(result_dict)}\n")
    else:
        write_json_line(file_handle, result)
    file_handle.flush()
