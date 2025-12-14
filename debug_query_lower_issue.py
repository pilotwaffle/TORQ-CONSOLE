#!/usr/bin/env python3
"""
Debug script to isolate the query_lower variable scope issue
"""

import asyncio
import sys
import os
import traceback
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from torq_console.agents.marvin_query_router import MarvinQueryRouter
from torq_console.marvin_integration.core import TorqMarvinIntegration

async def debug_query_lower_issue():
    """Debug the query_lower variable scope issue step by step."""

    print("=" * 80)
    print("DEBUG: Query Lower Variable Scope Issue")
    print("=" * 80)

    try:
        # Initialize Marvin integration
        print("1. Initializing Marvin integration...")
        marvin = TorqMarvinIntegration()

        # Initialize router
        print("2. Initializing Marvin Query Router...")
        router = MarvinQueryRouter(marvin)
        print("   Router initialized successfully")

        # Test the _infer_capabilities method directly
        print("3. Testing _infer_capabilities method directly...")

        # Import required enums
        from torq_console.agents.marvin_query_router import IntentClassification

        query = "What is Azure?"
        print(f"   Query: {query}")

        # Call _infer_capabilities directly
        try:
            capabilities = router._infer_capabilities(query, IntentClassification.CHAT)
            print(f"   Capabilities: {capabilities}")
            print("   ✓ _infer_capabilities works correctly")
        except Exception as e:
            print(f"   ✗ Error in _infer_capabilities: {e}")
            traceback.print_exc()
            return False

        # Test analyze_query method
        print("4. Testing analyze_query method...")
        try:
            analysis = await router.analyze_query(query)
            print(f"   Analysis: {analysis}")
            print("   ✓ analyze_query works correctly")
        except Exception as e:
            print(f"   ✗ Error in analyze_query: {e}")
            traceback.print_exc()
            return False

        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED - No query_lower scope issue found")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_query_lower_issue())
    sys.exit(0 if success else 1)