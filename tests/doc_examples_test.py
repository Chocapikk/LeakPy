#!/usr/bin/env python3
"""
Test all Python code examples from the documentation.

Note: This script uses a test API key but does NOT overwrite your local API key.
It uses the API key only in memory during test execution.

Usage:
    export LEAKPY_TEST_API_KEY='your_48_character_api_key_here'
    python3 tests/doc_examples_test.py

Or in one line:
    LEAKPY_TEST_API_KEY='your_key' python3 tests/doc_examples_test.py
"""

import os
import re
import sys
import traceback
from pathlib import Path
from typing import List, Tuple

# Test API key from environment variable (only used in memory, never saved)
# Set LEAKPY_TEST_API_KEY environment variable to run these tests
TEST_API_KEY = os.environ.get("LEAKPY_TEST_API_KEY", "")

def extract_python_blocks(content: str) -> List[Tuple[int, str]]:
    """Extract Python code blocks from RST content."""
    blocks = []
    lines = content.split('\n')
    in_python_block = False
    current_block = []
    start_line = 0
    
    for i, line in enumerate(lines, 1):
        # Check for Python code block start
        if re.match(r'^\s*\.\.\s+code-block::\s+python', line):
            in_python_block = True
            current_block = []
            start_line = i
            continue
        
        # Check for any code block start (might be python)
        if re.match(r'^\s*\.\.\s+code-block::', line):
            in_python_block = False
            continue
        
        # Check for end of code block
        if in_python_block and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
            # End of indented block
            if current_block:
                # Remove leading empty lines
                while current_block and not current_block[0].strip():
                    current_block.pop(0)
                # Remove trailing empty lines
                while current_block and not current_block[-1].strip():
                    current_block.pop()
                
                if current_block:
                    code = '\n'.join(current_block)
                    blocks.append((start_line, code))
                current_block = []
                in_python_block = False
            continue
        
        if in_python_block:
            # Remove leading indentation (usually 3 spaces in RST)
            # RST code blocks are indented with 3 spaces
            if line.startswith('   '):
                # Remove the 3-space RST indentation
                current_block.append(line[3:])
            elif line.startswith('\t'):
                # Handle tab indentation
                current_block.append(line[1:])
            elif not line.strip():
                # Preserve empty lines
                current_block.append('')
            elif line.strip() and not line.startswith(' '):
                # Line with content but no indentation - might be end of block
                # But only if it's not a continuation (check if previous line was code)
                if current_block and current_block[-1].strip():
                    # Previous line had content, this might be continuation
                    # Check if it looks like code (starts with common Python keywords/symbols)
                    if any(line.strip().startswith(kw) for kw in ['#', 'else:', 'elif', 'except', 'finally:']):
                        current_block.append(line.strip())
                    else:
                        # End of block
                        if current_block:
                            while current_block and not current_block[0].strip():
                                current_block.pop(0)
                            while current_block and not current_block[-1].strip():
                                current_block.pop()
                            if current_block:
                                code = '\n'.join(current_block)
                                blocks.append((start_line, code))
                            current_block = []
                            in_python_block = False
                else:
                    # Empty previous line, might be end
                    pass
    
    # Handle block at end of file
    if in_python_block and current_block:
        while current_block and not current_block[0].strip():
            current_block.pop(0)
        while current_block and not current_block[-1].strip():
            current_block.pop()
        if current_block:
            code = '\n'.join(current_block)
            blocks.append((start_line, code))
    
    return blocks

def test_code_block(file_path: str, line_num: int, code: str, test_num: int) -> Tuple[bool, str]:
    """Test a single code block."""
    # Replace placeholder API key with test key
    code = code.replace("your_48_character_api_key_here", TEST_API_KEY)
    code = code.replace('"your_48_character_api_key_here"', f'"{TEST_API_KEY}"')
    code = code.replace("'your_48_character_api_key_here'", f"'{TEST_API_KEY}'")
    
    # Skip examples that require user input
    if 'input(' in code or 'api_key = input' in code:
        return True, "SKIPPED (requires user input)"
    
    # Skip examples with invalid queries (they're meant to show error handling)
    if 'invalid query syntax' in code or 'invalid_key' in code:
        return True, "SKIPPED (error handling example)"
    
    # IMPORTANT: Prevent save_api_key from overwriting user's local API key
    # We'll monkey-patch save_api_key to prevent saving to disk
    # But first, ensure API key is passed to constructor if needed
    if 'save_api_key' in code and 'LeakIX()' in code and TEST_API_KEY not in code:
        # Replace LeakIX() with LeakIX(api_key=...) to use test key without saving
        code = code.replace('LeakIX()', f'LeakIX(api_key="{TEST_API_KEY}")')
    
    # Create a safe execution environment
    safe_globals = {
        '__builtins__': __builtins__,
        'LeakIX': None,  # Will be imported
    }
    
    try:
        # Import LeakIX
        from leakpy import LeakIX
        safe_globals['LeakIX'] = LeakIX
        
        # Monkey-patch save_api_key to prevent overwriting user's key
        original_save_api_key = LeakIX.save_api_key
        def noop_save_api_key(self, api_key):
            """No-op version that doesn't save to disk."""
            # Only update in-memory, don't save to disk
            self.api_key = api_key
            # Reinitialize API client with new key
            from leakpy.helpers import ensure_api_initialized
            self.api = ensure_api_initialized(None, self.api_key, self.log)
        
        # Temporarily replace save_api_key
        LeakIX.save_api_key = noop_save_api_key
        
        try:
            # Execute the code
            exec(code, safe_globals)
            return True, "OK"
        finally:
            # Restore original save_api_key
            LeakIX.save_api_key = original_save_api_key
            
    except Exception as e:
        error_msg = f"ERROR: {type(e).__name__}: {str(e)}"
        return False, error_msg

def test_documentation_file(file_path: str) -> Tuple[int, int, List[str]]:
    """Test all Python examples in a documentation file."""
    print(f"\n{'='*80}")
    print(f"Testing: {file_path}")
    print(f"{'='*80}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = extract_python_blocks(content)
    
    if not blocks:
        print("No Python code blocks found.")
        return 0, 0, []
    
    print(f"Found {len(blocks)} Python code block(s)\n")
    
    passed = 0
    failed = 0
    errors = []
    
    for i, (line_num, code) in enumerate(blocks, 1):
        print(f"  Test {i} (line {line_num}): ", end='', flush=True)
        
        # Skip very long examples (they might be interactive)
        if len(code.split('\n')) > 50:
            print("SKIPPED (too long, likely interactive example)")
            continue
        
        success, message = test_code_block(file_path, line_num, code, i)
        
        if success:
            print(f"✓ {message}")
            passed += 1
        else:
            print(f"✗ {message}")
            failed += 1
            errors.append(f"{file_path}:{line_num} - {message}")
            # Print first few lines of code for context
            code_lines = code.split('\n')[:5]
            print(f"    Code preview:")
            for cl in code_lines:
                print(f"      {cl}")
    
    return passed, failed, errors

def main():
    """Main test function."""
    # Check if test API key is provided
    if not TEST_API_KEY:
        print("=" * 80)
        print("ERROR: LEAKPY_TEST_API_KEY environment variable is not set.")
        print("=" * 80)
        print("\nTo run documentation example tests, set the environment variable:")
        print("\n  export LEAKPY_TEST_API_KEY='your_48_character_api_key_here'")
        print("  python3 tests/doc_examples_test.py")
        print("\nOr in one line:")
        print("  LEAKPY_TEST_API_KEY='your_key' python3 tests/doc_examples_test.py")
        print("\nNote: The API key is only used in memory and will NOT overwrite")
        print("      your local API key stored on disk.")
        print("=" * 80)
        return 1
    
    docs_dir = Path(__file__).parent.parent / "docs"
    
    # Files to test
    test_files = [
        "examples.rst",
        "quickstart.rst",
        "api.rst",
    ]
    
    total_passed = 0
    total_failed = 0
    all_errors = []
    
    for filename in test_files:
        file_path = docs_dir / filename
        if not file_path.exists():
            print(f"Warning: {file_path} not found, skipping...")
            continue
        
        passed, failed, errors = test_documentation_file(str(file_path))
        total_passed += passed
        total_failed += failed
        all_errors.extend(errors)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total passed: {total_passed}")
    print(f"Total failed: {total_failed}")
    
    if all_errors:
        print(f"\nErrors found:")
        for error in all_errors:
            print(f"  - {error}")
    
    return 0 if total_failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

