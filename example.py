#!/usr/bin/env python3
"""
Simple example script demonstrating LeakPy usage.

This example shows:
- How to initialize the scraper
- How to handle missing API keys
- Basic search operations
- Field extraction
"""

from leakpy import LeakIX


def main():
    # Initialize client
    # If no API key is provided, it will try to load from config file
    client = LeakIX(silent=False)
    
    # Check if API key is available
    if not client.has_api_key():
        print("⚠️  API key is missing!")
        print("Please set your API key using one of these methods:")
        print("1. Run: leakpy config set (then enter your key when prompted)")
        print("2. Or set it programmatically:")
        print("   from leakpy.config import APIKeyManager")
        print("   APIKeyManager().save('your_48_character_api_key_here')")
        return
    
    print("✓ API key found and valid")
    print()
    
    # Example 1: List available plugins
    print("Example 1: Listing available plugins...")
    plugins = client.get_plugins()
    print(f"Found {len(plugins)} plugins")
    if plugins:
        print(f"First 5 plugins: {plugins[:5]}")
    print()
    
    # Example 2: Basic search with default fields
    print("Example 2: Basic search (default: protocol, ip, port)...")
    print("Note: This will make actual API calls. Uncomment to run:")
    print()
    # results = client.search(
    #     scope="leak",
    #     pages=2,
    #     query='+country:"France"',
    #     fields="protocol,ip,port"  # Default fields
    # )
    # for result in results[:3]:  # Show first 3 results
    #     print(f"  {result.ip}:{result.port} ({result.protocol})")
    print()
    
    # Example 3: Search with custom fields
    print("Example 3: Search with custom fields...")
    print("Note: This will make actual API calls. Uncomment to run:")
    print()
    # results = client.search(
    #     scope="leak",
    #     pages=2,
    #     query='+country:"France"',
    #     fields="protocol,ip,port,host"
    # )
    # for result in results[:3]:
    #     print(f"  IP: {result.ip}, Port: {result.port}, Host: {result.host}")
    print()
    
    # Example 4: Get complete JSON
    print("Example 4: Get complete JSON (fields='full')...")
    print("Note: This will make actual API calls. Uncomment to run:")
    print()
    # results = client.search(
    #     scope="leak",
    #     pages=1,
    #     query='+country:"France"',
    #     fields="full"
    # )
    # if results:
    #     result_dict = results[0].to_dict()
    #     print(f"  First result keys: {list(result_dict.keys())[:10]}")
    print()
    
    # Example 5: Save results to file
    print("Example 5: Save results to file...")
    print("Note: This will make actual API calls. Uncomment to run:")
    print()
    # client.search(
    #     scope="leak",
    #     pages=3,
    #     query='+country:"France"',
    #     output="results.txt"
    # )
    # print("  Results saved to results.txt")
    print()
    
    print("✅ Examples completed!")
    print()
    print("For more examples, see EXAMPLES.md")


if __name__ == "__main__":
    main()

