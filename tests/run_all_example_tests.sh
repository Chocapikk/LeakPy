#!/bin/bash
# Script to run all documentation example tests

if [ -z "$LEAKPY_TEST_API_KEY" ]; then
    echo "============================================================"
    echo "ERROR: LEAKPY_TEST_API_KEY environment variable is not set."
    echo "============================================================"
    echo ""
    echo "To run the tests, set the environment variable:"
    echo ""
    echo "  export LEAKPY_TEST_API_KEY='your_48_character_api_key'"
    echo "  bash tests/run_all_example_tests.sh"
    echo ""
    echo "Or in one line:"
    echo "  LEAKPY_TEST_API_KEY='your_key' bash tests/run_all_example_tests.sh"
    echo ""
    echo "Note: The API key is used only in memory and will NOT overwrite"
    echo "      your local API key stored on disk."
    echo "============================================================"
    exit 1
fi

echo "============================================================"
echo "Running documentation example tests"
echo "============================================================"
echo ""

# Test 1: RST Documentation (docs/examples.rst, docs/quickstart.rst, docs/api.rst)
echo "Test 1/3: RST Documentation (docs/)"
echo "-----------------------------------"
python3 tests/doc_examples_test.py
RST_EXIT=$?

echo ""
echo ""

# Test 2: EXAMPLES.md
echo "Test 2/3: EXAMPLES.md"
echo "-----------------------------------"
python3 tests/examples_md_test.py
EXAMPLES_EXIT=$?

echo ""
echo ""

# Test 3: README.md
echo "Test 3/3: README.md"
echo "-----------------------------------"
python3 tests/readme_md_test.py
README_EXIT=$?

echo ""
echo "============================================================"
echo "SUMMARY"
echo "============================================================"
echo "RST Documentation: $([ $RST_EXIT -eq 0 ] && echo '✓ PASSED' || echo '✗ FAILED')"
echo "EXAMPLES.md:       $([ $EXAMPLES_EXIT -eq 0 ] && echo '✓ PASSED' || echo '✗ FAILED')"
echo "README.md:         $([ $README_EXIT -eq 0 ] && echo '✓ PASSED' || echo '✗ FAILED')"
echo "============================================================"

# Return an error code if at least one test failed
if [ $RST_EXIT -ne 0 ] || [ $EXAMPLES_EXIT -ne 0 ] || [ $README_EXIT -ne 0 ]; then
    exit 1
else
    exit 0
fi

