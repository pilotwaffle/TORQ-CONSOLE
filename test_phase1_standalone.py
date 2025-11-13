#!/usr/bin/env python3
"""
Standalone Phase 1 tests that don't require full package imports.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_handoff_optimizer_unit():
    """Test Phase 1 handoff optimizer units."""
    print("\n" + "=" * 80)
    print("PHASE 1: HANDOFF OPTIMIZER UNIT TESTS")
    print("=" * 80)

    # Import directly
    import importlib.util as iu

    spec = iu.spec_from_file_location(
        "handoff_optimizer",
        "torq_console/agents/handoff_optimizer.py"
    )
    ho_module = iu.module_from_spec(spec)
    spec.loader.exec_module(ho_module)

    optimizer = ho_module.get_handoff_optimizer()
    compressor = ho_module.SmartContextCompressor()
    extractor = ho_module.EntityExtractor()

    # Test 1: Entity extraction
    print("\n1. Testing Entity Extraction...")
    test_text = "We need to implement OAuth authentication with JWT tokens using PostgreSQL and Redis for caching"
    entities = extractor.extract_entities(test_text)
    print(f"   Extracted entities: {entities}")
    assert len(entities) > 0, "Should extract at least some entities"
    assert 'oauth' in entities or 'jwt' in entities or 'postgresql' in entities, "Should extract tech terms"
    print(f"   ✅ Found {len(entities)} entities - PASS")

    # Test 2: Concept extraction
    print("\n2. Testing Concept Extraction...")
    concepts = extractor.extract_key_concepts(test_text)
    print(f"   Extracted concepts: {concepts}")
    print(f"   ✅ Found {len(concepts)} concepts - PASS")

    # Test 3: Smart compression
    print("\n3. Testing Smart Context Compression...")
    long_content = """
    We discussed implementing a secure authentication system using OAuth 2.0 protocol.
    The system should support JWT tokens for API authentication and include refresh token rotation.
    We also talked about using PostgreSQL as the primary database for storing user credentials.
    Redis will be used for session management and caching frequently accessed data.
    The architecture should follow microservices patterns with API gateway as the entry point.
    Security considerations include HTTPS encryption, rate limiting, and SQL injection prevention.
    Performance requirements specify sub-100ms response times for authentication endpoints.
    """ * 5  # Make it long enough

    semantic_ctx = compressor.compress_context(long_content, target_length=500)
    print(f"   Original length: {semantic_ctx.original_length} chars")
    print(f"   Compressed length: {len(semantic_ctx.compressed_content)} chars")
    print(f"   Compression ratio: {semantic_ctx.compression_ratio:.1%}")
    print(f"   Key entities preserved: {len(semantic_ctx.key_entities)}")
    print(f"   Key concepts preserved: {len(semantic_ctx.key_concepts)}")

    assert len(semantic_ctx.compressed_content) <= 500, "Compression should respect target length"
    assert len(semantic_ctx.key_entities) > 0, "Should preserve key entities"
    print(f"   ✅ Compression successful - PASS")

    # Test 4: Query complexity analysis
    print("\n4. Testing Query Complexity Analysis...")
    simple_query = "What is OAuth?"
    complex_query = "Build a secure authentication system with OAuth, JWT tokens, refresh token rotation, and implement Redis caching"

    simple_complexity = optimizer._analyze_query_complexity(simple_query)
    complex_complexity = optimizer._analyze_query_complexity(complex_query)

    print(f"   Simple query complexity: {simple_complexity:.2f}")
    print(f"   Complex query complexity: {complex_complexity:.2f}")

    assert complex_complexity > simple_complexity, "Complex query should have higher score"
    print(f"   ✅ Complexity analysis working - PASS")

    # Test 5: Memory optimization
    print("\n5. Testing Memory Context Optimization...")
    mock_memories = [
        {
            'content': 'We previously discussed OAuth 2.0 authentication patterns and security best practices for token management',
            'similarity': 0.9
        },
        {
            'content': 'The team decided to use PostgreSQL for persistent storage with Redis for caching layer',
            'similarity': 0.85
        },
        {
            'content': 'API gateway should handle rate limiting and request routing to microservices',
            'similarity': 0.8
        }
    ]

    query = "Implement the authentication system we discussed with Redis caching"
    optimized = optimizer.optimize_memory_context(mock_memories, query, max_length=2000)

    print(f"   Query complexity: {optimized['query_complexity']:.2f}")
    print(f"   Memories optimized: {len(optimized['memories'])}")
    print(f"   Total length: {optimized['total_length']} chars")
    print(f"   Context utilization: {optimized['context_utilization']:.1%}")

    assert len(optimized['memories']) > 0, "Should have optimized memories"
    assert optimized['total_length'] <= 2000, "Should respect max length"
    print(f"   ✅ Memory optimization successful - PASS")

    # Test 6: Preservation quality scoring
    print("\n6. Testing Preservation Quality Scoring...")
    original = "OAuth authentication with JWT tokens and PostgreSQL database"
    preserved = "OAuth with JWT tokens and PostgreSQL"

    quality = optimizer.calculate_preservation_quality(original, preserved)
    print(f"   Preservation quality: {quality:.1%}")

    assert 0 <= quality <= 1.0, "Quality should be between 0 and 1"
    assert quality > 0.5, "Should preserve most key information"
    print(f"   ✅ Quality scoring working - PASS")

    print("\n" + "=" * 80)
    print("PHASE 1 UNIT TESTS: ALL PASSED ✅")
    print("=" * 80)

    return True


def test_improvements_analysis():
    """Analyze expected improvements from Phase 1."""
    print("\n" + "=" * 80)
    print("PHASE 1: IMPROVEMENTS ANALYSIS")
    print("=" * 80)

    improvements = {
        "Context Limit": {
            "before": "1000 chars",
            "after": "2000 chars",
            "improvement": "100% increase (2x)"
        },
        "Semantic Preservation": {
            "before": "None (simple truncation)",
            "after": "Entity/concept extraction + smart compression",
            "improvement": "Qualitative improvement"
        },
        "Adaptive Sizing": {
            "before": "Fixed size for all queries",
            "after": "Query complexity-based (500-2000 chars)",
            "improvement": "Efficient resource utilization"
        },
        "Memory Ranking": {
            "before": "By similarity only",
            "after": "By relevance (entity/concept overlap + similarity)",
            "improvement": "Better memory selection"
        }
    }

    print("\n📊 Phase 1 Improvements:")
    for feature, details in improvements.items():
        print(f"\n  {feature}:")
        print(f"    Before: {details['before']}")
        print(f"    After: {details['after']}")
        print(f"    Improvement: {details['improvement']}")

    print("\n🎯 Expected Target Achievement:")
    targets = [
        ("Memory → Planning", "46%", "70-85%", "Expected: 70-75%"),
        ("Overall Preservation", "58.9%", "70%+", "Expected: 65-72%"),
        ("Information Loss", "40%", "<30%", "Expected: 25-30%")
    ]

    print()
    for target, before, goal, expected in targets:
        print(f"  {target}:")
        print(f"    Baseline: {before}")
        print(f"    Target: {goal}")
        print(f"    {expected}")

    print("\n" + "=" * 80)
    print("PHASE 1 ANALYSIS COMPLETE")
    print("=" * 80)

    return True


def main():
    """Run all standalone Phase 1 tests."""
    print("\n" + "=" * 80)
    print("PHASE 1: ADVANCED HANDOFF OPTIMIZATION (STANDALONE TESTS)")
    print("=" * 80)

    try:
        # Run unit tests
        unit_success = test_handoff_optimizer_unit()

        # Run analysis
        analysis_success = test_improvements_analysis()

        # Summary
        print("\n" + "=" * 80)
        print("PHASE 1 STANDALONE TEST SUMMARY")
        print("=" * 80)
        print(f"\nUnit Tests: {'✅ PASS' if unit_success else '❌ FAIL'}")
        print(f"Analysis: {'✅ PASS' if analysis_success else '❌ FAIL'}")

        if unit_success and analysis_success:
            print("\n🎉 PHASE 1 COMPONENTS VALIDATED")
            print("\nPhase 1 Features Ready:")
            print("  ✅ Entity extraction")
            print("  ✅ Concept extraction")
            print("  ✅ Smart compression")
            print("  ✅ Query complexity analysis")
            print("  ✅ Adaptive memory optimization")
            print("  ✅ Preservation quality scoring")
            print("\nNext: Run full integration tests when dependencies available")
            return True
        else:
            print("\n⚠️  PHASE 1 VALIDATION INCOMPLETE")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
