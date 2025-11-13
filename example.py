#!/usr/bin/env python3
"""
Simple example script demonstrating LeakPy usage.

This example shows:
- How to initialize the scraper
- How to handle missing API keys
- Basic search operations
- Field extraction
"""

from leakpy import LeakIXScraper


def main():
    # Initialize scraper
    # If no API key is provided, it will try to load from config file
    scraper = LeakIXScraper(verbose=True)
    
    # Check if API key is available
    if not scraper.has_api_key():
        print("⚠️  API key is missing!")
        print("Please set your API key using one of these methods:")
        print("1. Run: leakpy -r (then enter your key when prompted)")
        print("2. Or set it programmatically:")
        print("   scraper.save_api_key('your_48_character_api_key_here')")
        return
    
    print("✓ API key found and valid")
    print()
    
    # Example 1: List available plugins
    print("Example 1: Listing available plugins...")
    plugins = scraper.get_plugins()
    print(f"Found {len(plugins)} plugins")
    if plugins:
        print(f"First 5 plugins: {plugins[:5]}")
    print()
    
    # Example 2: Basic search with default fields
    print("Example 2: Basic search (default: protocol, ip, port)...")
    print("Note: This will make actual API calls. Uncomment to run:")
    print()
    # results = scraper.run(
    #     scope="leak",
    #     pages=2,
    #     query='+country:"France"',
    #     fields=None  # Uses default: protocol, ip, port
    # )
    # for result in results[:3]:  # Show first 3 results
    #     print(f"  {result}")
    print()
    
    # Example 3: Search with custom fields
    print("Example 3: Search with custom fields...")
    print("Note: This will make actual API calls. Uncomment to run:")
    print()
    # results = scraper.run(
    #     scope="leak",
    #     pages=2,
    #     query='+country:"France"',
    #     fields="protocol,ip,port,host"
    # )
    # for result in results[:3]:
    #     print(f"  IP: {result.get('ip')}, Port: {result.get('port')}")
    print()
    
    # Example 4: Get complete JSON
    print("Example 4: Get complete JSON (fields='full')...")
    print("Note: This will make actual API calls. Uncomment to run:")
    print()
    # results = scraper.run(
    #     scope="leak",
    #     pages=1,
    #     query='+country:"France"',
    #     fields="full"
    # )
    # if results:
    #     print(f"  First result keys: {list(results[0].keys())}")
    print()
    
    # Example 5: Save results to file
    print("Example 5: Save results to file...")
    print("Note: This will make actual API calls. Uncomment to run:")
    print()
    # scraper.run(
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

