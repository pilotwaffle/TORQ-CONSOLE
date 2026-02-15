#!/usr/bin/env python3
"""
Test Enhanced Prince API locally before Vercel deployment

This script validates that the API works correctly before deploying to Vercel.
Run this to catch issues early.
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required imports work."""
    print("Testing imports...")
    
    try:
        import fastapi
        print("✅ fastapi")
    except ImportError as e:
        print(f"❌ fastapi: {e}")
        return False
        
    try:
        import pydantic
        print("✅ pydantic")
    except ImportError as e:
        print(f"❌ pydantic: {e}")
        return False
        
    try:
        import anthropic
        print("✅ anthropic")
    except ImportError as e:
        print("⚠️  anthropic: Optional, but recommended")
        
    try:
        import openai
        print("✅ openai")
    except ImportError as e:
        print("⚠️  openai: Optional, but recommended")
    
    try:
        from torq_console.agents import create_prince_flowers_agent
        print("✅ torq_console.agents")
    except ImportError as e:
        print(f"❌ torq_console.agents: {e}")
        return False
    
    return True


def test_api_module():
    """Test that the API module can be imported."""
    print("\nTesting API module...")
    
    try:
        import enhanced_prince_api
        print("✅ enhanced_prince_api module imports")
        
        # Check that app is defined
        if hasattr(enhanced_prince_api, 'app'):
            print("✅ FastAPI app is defined")
        else:
            print("❌ FastAPI app not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to import API module: {e}")
        return False


def test_environment():
    """Test environment configuration."""
    print("\nTesting environment...")
    
    import os
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if anthropic_key:
        print(f"✅ ANTHROPIC_API_KEY configured (length: {len(anthropic_key)})")
    else:
        print("⚠️  ANTHROPIC_API_KEY not set")
        
    if openai_key:
        print(f"✅ OPENAI_API_KEY configured (length: {len(openai_key)})")
    else:
        print("⚠️  OPENAI_API_KEY not set")
        
    if not anthropic_key and not openai_key:
        print("❌ No API keys configured!")
        print("   Set at least one: ANTHROPIC_API_KEY or OPENAI_API_KEY")
        return False
        
    return True


async def test_prince_agent():
    """Test creating a Prince Flowers agent."""
    print("\nTesting Prince Flowers agent...")
    
    try:
        from torq_console.agents import create_prince_flowers_agent
        
        # Try to create agent
        agent = create_prince_flowers_agent()
        print("✅ Prince Flowers agent created")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_endpoints():
    """Test that API endpoints can be created."""
    print("\nTesting API endpoints...")
    
    try:
        from enhanced_prince_api import app
        
        # Get routes
        routes = [route.path for route in app.routes]
        
        expected_routes = ["/", "/health", "/chat", "/feedback"]
        
        for route in expected_routes:
            if route in routes:
                print(f"✅ Route {route} registered")
            else:
                print(f"❌ Route {route} missing")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Failed to test endpoints: {e}")
        return False


def main():
    """Run all tests."""
    print("="*80)
    print("TORQ Console - Vercel Deployment Validation")
    print("="*80)
    print()
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
        print("\n❌ Import tests failed")
    
    # Test API module
    if not test_api_module():
        all_passed = False
        print("\n❌ API module tests failed")
    
    # Test environment
    if not test_environment():
        all_passed = False
        print("\n❌ Environment tests failed")
    
    # Test Prince agent (async)
    try:
        if not asyncio.run(test_prince_agent()):
            all_passed = False
            print("\n❌ Prince agent tests failed")
    except Exception as e:
        print(f"\n❌ Prince agent tests failed: {e}")
        all_passed = False
    
    # Test endpoints (async)
    try:
        if not asyncio.run(test_api_endpoints()):
            all_passed = False
            print("\n❌ Endpoint tests failed")
    except Exception as e:
        print(f"\n❌ Endpoint tests failed: {e}")
        all_passed = False
    
    print("\n" + "="*80)
    
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print()
        print("Your API is ready for Vercel deployment!")
        print()
        print("Next steps:")
        print("  1. Run: vercel --prod")
        print("  2. Set environment variables in Vercel")
        print("  3. Test deployed API")
        print()
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print()
        print("Fix the issues above before deploying to Vercel.")
        print()
        print("Common fixes:")
        print("  • Install dependencies: pip install -r requirements.txt")
        print("  • Set API keys: export ANTHROPIC_API_KEY=your_key")
        print("  • Install torq_console: pip install -e .")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
