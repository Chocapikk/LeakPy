# Configuration file for the Sphinx documentation builder.

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath('..'))

# Project information
project = 'LeakPy'
copyright = f'{datetime.now().year}, LeakPy Contributors'
author = 'Valentin Lobstein'

# Get version from package
version_file = os.path.join(os.path.dirname(__file__), '..', 'leakpy', '__init__.py')
version = '1.0.0'
if os.path.exists(version_file):
    with open(version_file, 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                version = line.split('=')[1].strip().strip('"').strip("'")
                break

release = version

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'myst_parser',
]

# Templates
templates_path = ['_templates']

# Exclude patterns
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'README.md']

# HTML theme
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Custom CSS to override theme defaults with LeakIX colors
html_css_files = ['custom.css']

# Autodoc settings
autodoc_member_order = 'bysource'
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}

# Napoleon settings (for Google/NumPy style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'requests': ('https://requests.readthedocs.io/en/latest/', None),
}

