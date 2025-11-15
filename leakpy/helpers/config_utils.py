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

import json
import os
from pathlib import Path
from .decorators import handle_file_errors
from .constants import _ENCODING_UTF8

# ============================================================================
# CONFIGURATION UTILITIES
# ============================================================================

def get_config_dir():
    """Get the configuration directory for the current OS."""
    if os.name == "nt":  # Windows
        base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home())
        config_dir = Path(base) / "LeakPy"
    else:  # Linux, macOS, etc.
        base = os.getenv("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        config_dir = Path(base) / "LeakPy"
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@handle_file_errors(default_return={})
def read_json_file(file_path):
    """Read JSON data from a file."""
    if not file_path.exists():
        return {}
    with open(file_path, 'r', encoding=_ENCODING_UTF8) as f:
        return json.load(f)


@handle_file_errors()
def write_json_file(file_path, data, ensure_dir=True):
    """Write JSON data to a file."""
    if ensure_dir:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding=_ENCODING_UTF8) as f:
        json.dump(data, f, indent=2)

