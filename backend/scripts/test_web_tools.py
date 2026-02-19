#!/usr/bin/env python3
"""Test script for web tools."""

import sys
import time

def test_web_tools():
    """Test all web tools."""
    from app.agent.tools.web_tools import web_search, read_url, get_weather
    
    print("=" * 70)
    print("DevFlow Web Tools Test")
    print("=" * 70)
    
    # Test 1: Read URL
    print("\n1. Testing read_url...")
    try:
        result = read_url.invoke({"url": "https://example.com"})
        print(f"✅ Success: {result[:150]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Weather (without API key)
    print("\n2. Testing get_weather (no API key)...")
    try:
        result = get_weather.invoke({"location": "London"})
        print(f"Response: {result}")
        if "not configured" in result:
            print("✅ Correct error message for missing API key")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Web Search (may hit rate limit)
    print("\n3. Testing web_search (may hit rate limit)...")
    try:
        time.sleep(2)  # Avoid rate limit
        result = web_search.invoke({"query": "DevFlow project management", "max_results": 3})
        if "Error" in result or "Ratelimit" in result:
            print(f"⚠️ Rate limited (expected): {result[:100]}")
        else:
            print(f"✅ Success: {result[:150]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)
    print("\nNotes:")
    print("- Weather tool requires OPENWEATHER_API_KEY in .env")
    print("- Web search may be rate-limited by DuckDuckGo")
    print("- URL reader works for static HTML pages")

if __name__ == "__main__":
    test_web_tools()
