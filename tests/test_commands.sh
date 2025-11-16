#!/bin/bash

# Test script for all commands with and without --raw and --silent

# Function to execute a command and limit output if necessary
# This function checks the return code without biasing the tests
run_test() {
    local cmd="$1"
    local max_lines=10
    
    # Execute the command and capture output and return code
    local output
    local exit_code
    output=$(eval "$cmd" 2>&1)
    exit_code=$?
    
    # Check return code first
    if [ $exit_code -ne 0 ]; then
        echo "$output"
        return $exit_code
    fi
    
    # Count the number of lines
    local line_count=$(echo "$output" | wc -l)
    
    # If too many lines, display only the first ones with a message
    if [ $line_count -gt $max_lines ]; then
        echo "$output" | head -n $max_lines
        echo "... (${line_count} lines total, truncated for display)"
    else
        echo "$output"
    fi
    
    return $exit_code
}

echo "=========================================="
echo "TEST 1: search without --raw/--silent"
echo "=========================================="
leakpy cache clear > /dev/null 2>&1
run_test "leakpy search -q 'plugin:TraccarPlugin' -p 1"

echo ""
echo "=========================================="
echo "TEST 2: search with --raw"
echo "=========================================="
leakpy cache clear > /dev/null 2>&1
run_test "leakpy --raw search -q 'plugin:TraccarPlugin' -p 1"

echo ""
echo "=========================================="
echo "TEST 3: search with --silent"
echo "=========================================="
leakpy cache clear > /dev/null 2>&1
run_test "leakpy --silent search -q 'plugin:TraccarPlugin' -p 1"

echo ""
echo "=========================================="
echo "TEST 4: search with --raw --silent"
echo "=========================================="
leakpy cache clear > /dev/null 2>&1
run_test "leakpy --raw --silent search -q 'plugin:TraccarPlugin' -p 1"

echo ""
echo "=========================================="
echo "TEST 5: list plugins without --raw/--silent"
echo "=========================================="
run_test "leakpy list plugins"

echo ""
echo "=========================================="
echo "TEST 6: list plugins with --raw"
echo "=========================================="
run_test "leakpy --raw list plugins"

echo ""
echo "=========================================="
echo "TEST 7: list plugins with --silent"
echo "=========================================="
run_test "leakpy --silent list plugins"

echo ""
echo "=========================================="
echo "TEST 8: list plugins with --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent list plugins"

echo ""
echo "=========================================="
echo "TEST 9: list fields without --raw/--silent"
echo "=========================================="
run_test "leakpy list fields -q 'plugin:TraccarPlugin'"

echo ""
echo "=========================================="
echo "TEST 10: list fields with --raw"
echo "=========================================="
run_test "leakpy --raw list fields -q 'plugin:TraccarPlugin'"

echo ""
echo "=========================================="
echo "TEST 11: list fields with --silent"
echo "=========================================="
run_test "leakpy --silent list fields -q 'plugin:TraccarPlugin'"

echo ""
echo "=========================================="
echo "TEST 12: list fields with --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent list fields -q 'plugin:TraccarPlugin'"

echo ""
echo "=========================================="
echo "TEST 13: lookup host without --raw/--silent"
echo "=========================================="
leakpy cache clear > /dev/null 2>&1
run_test "leakpy lookup host 8.8.8.8 --limit 5"

echo ""
echo "=========================================="
echo "TEST 14: lookup host with --raw"
echo "=========================================="
leakpy cache clear > /dev/null 2>&1
run_test "leakpy --raw lookup host 8.8.8.8 --limit 5"

echo ""
echo "=========================================="
echo "TEST 15: lookup host with --silent"
echo "=========================================="
leakpy cache clear > /dev/null 2>&1
run_test "leakpy --silent lookup host 8.8.8.8 --limit 5"

echo ""
echo "=========================================="
echo "TEST 16: lookup host with --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent lookup host 8.8.8.8 --limit 5"

echo ""
echo "=========================================="
echo "TEST 17: lookup domain without --raw/--silent"
echo "=========================================="
run_test "leakpy lookup domain leakix.net --limit 5"

echo ""
echo "=========================================="
echo "TEST 18: lookup domain with --raw"
echo "=========================================="
run_test "leakpy --raw lookup domain leakix.net --limit 5"

echo ""
echo "=========================================="
echo "TEST 19: lookup domain with --silent"
echo "=========================================="
run_test "leakpy --silent lookup domain leakix.net --limit 5"

echo ""
echo "=========================================="
echo "TEST 20: lookup domain with --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent lookup domain leakix.net --limit 5"

echo ""
echo "=========================================="
echo "TEST 21: lookup subdomains without --raw/--silent"
echo "=========================================="
run_test "leakpy lookup subdomains leakix.net"

echo ""
echo "=========================================="
echo "TEST 22: lookup subdomains with --raw"
echo "=========================================="
run_test "leakpy --raw lookup subdomains leakix.net"

echo ""
echo "=========================================="
echo "TEST 23: lookup subdomains with --silent"
echo "=========================================="
run_test "leakpy --silent lookup subdomains leakix.net"

echo ""
echo "=========================================="
echo "TEST 24: lookup subdomains with --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent lookup subdomains leakix.net"

echo ""
echo "=========================================="
echo "TEST 25: stats query without --raw/--silent"
echo "=========================================="
run_test "leakpy stats query -q 'country:France' -p 1"

echo ""
echo "=========================================="
echo "TEST 26: stats query with --raw"
echo "=========================================="
run_test "leakpy --raw stats query -q 'country:France' -p 1"

echo ""
echo "=========================================="
echo "TEST 27: stats query with --silent"
echo "=========================================="
run_test "leakpy --silent stats query -q 'country:France' -p 1"

echo ""
echo "=========================================="
echo "TEST 28: stats query with --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent stats query -q 'country:France' -p 1"

echo ""
echo "=========================================="
echo "TEST 29: stats cache without --raw/--silent"
echo "=========================================="
run_test "leakpy stats cache"

echo ""
echo "=========================================="
echo "TEST 30: stats cache with --raw"
echo "=========================================="
run_test "leakpy --raw stats cache"

echo ""
echo "=========================================="
echo "TEST 31: stats cache with --silent"
echo "=========================================="
run_test "leakpy --silent stats cache"

echo ""
echo "=========================================="
echo "TEST 32: stats cache with --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent stats cache"

echo ""
echo "=========================================="
echo "TEST 37: cache clear without --raw/--silent"
echo "=========================================="
run_test "leakpy cache clear"

echo ""
echo "=========================================="
echo "TEST 38: cache clear with --raw"
echo "=========================================="
run_test "leakpy --raw cache clear"

echo ""
echo "=========================================="
echo "TEST 39: cache clear with --silent"
echo "=========================================="
run_test "leakpy --silent cache clear"

echo ""
echo "=========================================="
echo "TEST 40: cache clear with --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent cache clear"

echo ""
echo "=========================================="
echo "TEST 41: cache show-ttl without --raw/--silent"
echo "=========================================="
run_test "leakpy cache show-ttl"

echo ""
echo "=========================================="
echo "TEST 42: cache show-ttl with --raw"
echo "=========================================="
run_test "leakpy --raw cache show-ttl"

echo ""
echo "=========================================="
echo "TEST 43: cache show-ttl with --silent"
echo "=========================================="
run_test "leakpy --silent cache show-ttl"

echo ""
echo "=========================================="
echo "TEST 44: cache show-ttl with --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent cache show-ttl"


