# Building the Documentation

## Prerequisites

Install the documentation dependencies:

```bash
pip install -r requirements-docs.txt
```

Or install with the package:

```bash
pip install -e .[docs]
```

## Building Locally

To build the HTML documentation:

```bash
cd docs
make html
```

Or directly with sphinx-build:

```bash
cd docs
sphinx-build -b html . _build/html
```

The documentation will be generated in `docs/_build/html/`.

To view it:

```bash
# Linux/macOS
open _build/html/index.html

# Or use a simple HTTP server
python -m http.server --directory _build/html
```

## Building on Read the Docs

The documentation is automatically built on Read the Docs when you push to the repository.

Make sure to:

1. Connect your GitHub repository to Read the Docs
2. The `.readthedocs.yml` file is in the root directory
3. The documentation will be built automatically on each push

## Structure

- `conf.py` - Sphinx configuration
- `index.rst` - Main documentation index
- `installation.rst` - Installation instructions
- `quickstart.rst` - Quick start guide
- `cli.rst` - CLI documentation
- `api.rst` - API reference
- `examples.rst` - Usage examples
- `contributing.rst` - Contributing guidelines

