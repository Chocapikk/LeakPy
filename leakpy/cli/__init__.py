"""CLI module for LeakPy."""

# Import main from the parent cli.py file using importlib to avoid circular import
import importlib.util
from pathlib import Path

# Get the path to the parent cli.py file
parent_dir = Path(__file__).parent.parent
cli_py_path = parent_dir / "cli.py"

# Load the module directly from the file path
spec = importlib.util.spec_from_file_location("leakpy.cli_module", cli_py_path)
cli_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli_module)

# Export main function
main = cli_module.main

__all__ = ['main']

