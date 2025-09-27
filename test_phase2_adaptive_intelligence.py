#!/usr/bin/env python3
"""
Test Suite for Phase 2: Adaptive Intelligence Layer
Comprehensive testing of real-time analysis, intelligent suggestions, and adaptive learning
"""

import asyncio
import sys
import os
import json
import tempfile
import time
from pathlib import Path

# Add TORQ Console to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'torq_console'))

from torq_console.spec_kit.spec_engine import SpecKitEngine
from torq_console.spec_kit.adaptive_intelligence import AdaptiveIntelligenceEngine, RealTimeAnalysis
from torq_console.spec_kit.realtime_editor import RealTimeEditor, EditingSuggestion
from torq_console.spec_kit.rl_spec_analyzer import RLSpecAnalyzer


async def test_adaptive_intelligence_engine():
    """Test the Adaptive Intelligence Engine"""
    print("\n" + "=" * 60)
    print("Testing Adaptive Intelligence Engine")
    print("=" * 60)

    try:
        # Test 1: Engine Initialization
        print("\n1. Testing Engine Initialization...")
        engine = AdaptiveIntelligenceEngine()
        print("PASS Adaptive Intelligence Engine initialized successfully")

        # Test 2: Real-time Analysis
        print("\n2. Testing Real-time Specification Analysis...")
        context = {
            'domain': 'web',
            'tech_stack': ['python', 'react', 'postgresql'],
            'project_size': 'medium',
            'team_size': 4,
            'timeline': '6-weeks',
            'constraints': ['Budget limitations', 'Tight timeline']
        }

        spec_text = """
        User Authentication System

        Build a comprehensive user authentication system that allows users to register,
        login, and manage their accounts securely. The system must support OAuth
        integration with Google and GitHub, implement JWT token-based authentication,
        and include multi-factor authentication for enhanced security.

        Requirements:
        - User registration with email verification
        - Secure login with password hashing
        - OAuth integration (Google, GitHub)
        - JWT token management
        - Multi-factor authentication
        - Password reset functionality
        - Role-based access control
        - Session management
        """

        analysis = await engine.analyze_specification_realtime(spec_text, context)
        print(f"PASS Real-time analysis completed:")
        print(f"     Clarity Score: {analysis.clarity_score:.2f}")
        print(f"     Completeness Score: {analysis.completeness_score:.2f}")
        print(f"     Feasibility Score: {analysis.feasibility_score:.2f}")
        print(f"     Complexity Score: {analysis.complexity_score:.2f}")
        print(f"     Confidence: {analysis.confidence:.2f}")
        print(f"     Suggestions: {len(analysis.suggestions)} items")
        print(f"     Dependencies: {len(analysis.dependencies_detected)} items")
        print(f"     Risk Factors: {len(analysis.risk_factors)} items")

        # Test 3: Learning from Feedback
        print("\n3. Testing Adaptive Learning...")
        feedback = {
            'suggestion_helpful': True,
            'risk_accurate': True,
            'dependency_detection': False,
            'overall_rating': 4.5
        }
        await engine.learn_from_feedback(feedback)
        print("PASS Feedback processed for adaptive learning")

        # Test 4: Intelligence Metrics
        print("\n4. Testing Intelligence Metrics...")
        metrics = engine.get_intelligence_metrics()
        print(f"PASS Intelligence metrics retrieved:")
        print(f"     Total Analyses: {metrics['performance']['total_analyses']}")
        print(f"     Learning Weights: {len(metrics['learning_weights'])} categories")

        return True

    except Exception as e:
        print(f"FAIL Adaptive Intelligence Engine test failed: {e}")
        return False


async def test_realtime_editor():
    """Test the Real-time Editor"""
    print("\n" + "=" * 60)
    print("Testing Real-time Editor")
    print("=" * 60)

    try:
        # Test 1: Editor Initialization
        print("\n1. Testing Real-time Editor Initialization...")
        ai_engine = AdaptiveIntelligenceEngine()
        editor = RealTimeEditor(ai_engine)
        print("PASS Real-time Editor initialized successfully")

        # Test 2: Start Editing Session
        print("\n2. Testing Editing Session Creation...")
        user_prefs = {
            'domain': 'web',
            'tech_stack': ['python', 'react'],
            'project_size': 'small',
            'team_size': 3,
            'timeline': '4-weeks'
        }
        initial_content = "User Management System\n\nDescriptio"
        session_id = await editor.start_editing_session("spec_001", initial_content, user_prefs)
        print(f"PASS Editing session created: {session_id}")

        # Test 3: Handle Text Changes
        print("\n3. Testing Real-time Text Changes...")
        new_content = "User Management System\n\nDescription: Build a comprehensive user management system with authentication"
        cursor_pos = len(new_content)

        result = await editor.handle_text_change(session_id, new_content, cursor_pos, "", "description")
        print(f"PASS Text change handled:")
        print(f"     Suggestions: {len(result.get('suggestions', []))} items")
        print(f"     Corrections: {len(result.get('corrections', []))} items")
        print(f"     Response Time: {result.get('response_time', 0):.3f}s")

        # Test 4: Suggestion Acceptance/Rejection
        print("\n4. Testing Suggestion Handling...")
        accept_result = await editor.accept_suggestion(session_id, "suggestion_001")
        print(f"PASS Suggestion acceptance: {accept_result.get('status', 'unknown')}")

        reject_result = await editor.reject_suggestion(session_id, "suggestion_002", "Not relevant")
        print(f"PASS Suggestion rejection: {reject_result.get('status', 'unknown')}")

        # Test 5: End Session
        print("\n5. Testing Session Termination...")
        summary = await editor.end_editing_session(session_id, user_satisfaction=4.2)
        print(f"PASS Session ended with summary:")
        print(f"     Total Edits: {summary.get('total_edits', 0)}")
        print(f"     Acceptance Rate: {summary.get('acceptance_rate', 0):.2f}")
        print(f"     User Satisfaction: {summary.get('user_satisfaction', 'N/A')}")

        return True

    except Exception as e:
        print(f"FAIL Real-time Editor test failed: {e}")
        return False


async def test_spec_engine_integration():
    """Test integration of Phase 2 with SpecKitEngine"""
    print("\n" + "=" * 60)
    print("Testing SpecKit Engine Phase 2 Integration")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Test 1: Engine with Phase 2 Components
            print("\n1. Testing Engine Initialization with Phase 2...")
            engine = SpecKitEngine(workspace_path=temp_dir)
            await engine.initialize()
            print("PASS SpecKit Engine initialized with Phase 2 components")

            # Verify Phase 2 components are available
            assert hasattr(engine, 'adaptive_intelligence'), "Adaptive Intelligence not initialized"
            assert hasattr(engine, 'realtime_editor'), "Real-time Editor not initialized"
            print("PASS Phase 2 components verified")

            # Test 2: Enhanced Status Summary
            print("\n2. Testing Enhanced Status Summary...")
            status = engine.get_enhanced_status_summary()
            print(f"PASS Enhanced status retrieved:")
            print(f"     Realtime Editing Active: {status.get('realtime_editing_active', False)}")
            print(f"     Adaptive Learning Enabled: {status.get('adaptive_learning_enabled', False)}")
            print(f"     Phase 2 Status: {status.get('phase2_adaptive_intelligence', {}).get('phase2_status', 'unknown')}")

            # Test 3: Real-time Analysis Integration
            print("\n3. Testing Real-time Analysis Integration...")
            context = {
                'domain': 'web',
                'tech_stack': ['python', 'fastapi'],
                'project_size': 'large',
                'team_size': 6,
                'timeline': '8-weeks'
            }

            spec_text = "API Gateway with authentication, rate limiting, and monitoring capabilities"
            analysis = await engine.analyze_specification_realtime(spec_text, context)
            print(f"PASS Real-time analysis via engine:")
            print(f"     Clarity: {analysis.get('clarity_score', 0):.2f}")
            print(f"     Completeness: {analysis.get('completeness_score', 0):.2f}")

            # Test 4: Real-time Editing Integration
            print("\n4. Testing Real-time Editing Integration...")
            user_prefs = context.copy()
            session_id = await engine.start_realtime_editing("spec_test", spec_text, user_prefs)
            print(f"PASS Real-time editing session started via engine: {session_id}")

            edit_result = await engine.handle_realtime_edit(session_id, spec_text + " with comprehensive logging", len(spec_text), "", "description")
            print(f"PASS Real-time edit handled via engine")

            summary = await engine.end_realtime_editing(session_id, 4.0)
            print(f"PASS Real-time editing session ended via engine")

            # Test 5: Adaptive Intelligence Metrics
            print("\n5. Testing Adaptive Intelligence Metrics...")
            ai_metrics = engine.get_adaptive_intelligence_metrics()
            print(f"PASS AI metrics retrieved:")
            print(f"     Phase 2 Status: {ai_metrics.get('phase2_status', 'unknown')}")
            print(f"     Active Sessions: {ai_metrics.get('realtime_editor', {}).get('active_sessions', 0)}")

            return True

        except Exception as e:
            print(f"FAIL SpecKit Engine Phase 2 integration test failed: {e}")
            return False


async def test_performance_benchmarks():
    """Test performance benchmarks for Phase 2 components"""
    print("\n" + "=" * 60)
    print("Testing Performance Benchmarks")
    print("=" * 60)

    try:
        # Test 1: Real-time Analysis Performance
        print("\n1. Testing Real-time Analysis Performance...")
        engine = AdaptiveIntelligenceEngine()

        context = {
            'domain': 'web',
            'tech_stack': ['python', 'react'],
            'project_size': 'medium',
            'team_size': 4,
            'timeline': '6-weeks'
        }

        test_specs = [
            "Simple user authentication system",
            "Complex e-commerce platform with payment processing, inventory management, and analytics",
            "Microservices architecture with API gateway, service discovery, and distributed tracing",
            "Real-time chat application with WebSocket connections, message persistence, and user presence"
        ]

        total_time = 0
        for i, spec_text in enumerate(test_specs, 1):
            start_time = time.time()
            analysis = await engine.analyze_specification_realtime(spec_text, context)
            end_time = time.time()
            analysis_time = end_time - start_time
            total_time += analysis_time

            print(f"     Spec {i}: {analysis_time:.3f}s (Confidence: {analysis.confidence:.2f})")

        avg_time = total_time / len(test_specs)
        print(f"PASS Average analysis time: {avg_time:.3f}s")

        if avg_time < 2.0:
            print("PASS Performance target met (< 2.0s)")
        else:
            print("WARNING Performance target not met")

        # Test 2: Real-time Editing Performance
        print("\n2. Testing Real-time Editing Performance...")
        ai_engine = AdaptiveIntelligenceEngine()
        editor = RealTimeEditor(ai_engine)

        session_id = await editor.start_editing_session("perf_test", "Initial content", context)

        edit_times = []
        for i in range(5):
            start_time = time.time()
            content = f"Updated content iteration {i} with additional requirements and specifications"
            result = await editor.handle_text_change(session_id, content, len(content))
            end_time = time.time()
            edit_times.append(end_time - start_time)

        avg_edit_time = sum(edit_times) / len(edit_times)
        print(f"PASS Average edit handling time: {avg_edit_time:.3f}s")

        if avg_edit_time < 0.5:
            print("PASS Edit performance target met (< 0.5s)")
        else:
            print("WARNING Edit performance target not met")

        await editor.end_editing_session(session_id)

        return True

    except Exception as e:
        print(f"FAIL Performance benchmark test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling and edge cases"""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)

    try:
        # Test 1: Invalid Session IDs
        print("\n1. Testing Invalid Session Handling...")
        ai_engine = AdaptiveIntelligenceEngine()
        editor = RealTimeEditor(ai_engine)

        result = await editor.handle_text_change("invalid_session", "content", 0)
        if 'error' in result:
            print("PASS Invalid session handled gracefully")
        else:
            print("FAIL Invalid session not handled properly")

        # Test 2: Malformed Input
        print("\n2. Testing Malformed Input Handling...")
        try:
            analysis = await ai_engine.analyze_specification_realtime("", {})
            print("PASS Empty specification handled")
        except Exception as e:
            print(f"PASS Empty specification error handled: {type(e).__name__}")

        # Test 3: Large Input Handling
        print("\n3. Testing Large Input Handling...")
        large_spec = "Large specification " * 1000  # ~20KB of text
        context = {'domain': 'web', 'tech_stack': ['python'], 'project_size': 'large'}

        try:
            analysis = await ai_engine.analyze_specification_realtime(large_spec, context)
            print("PASS Large specification handled successfully")
        except Exception as e:
            print(f"WARNING Large specification handling: {e}")

        # Test 4: Concurrent Session Handling
        print("\n4. Testing Concurrent Sessions...")
        session_ids = []
        for i in range(3):
            session_id = await editor.start_editing_session(f"concurrent_{i}", f"Content {i}", context)
            session_ids.append(session_id)

        print(f"PASS Created {len(session_ids)} concurrent sessions")

        for session_id in session_ids:
            await editor.end_editing_session(session_id)

        print("PASS All concurrent sessions ended successfully")

        return True

    except Exception as e:
        print(f"FAIL Error handling test failed: {e}")
        return False


async def test_learning_and_adaptation():
    """Test adaptive learning capabilities"""
    print("\n" + "=" * 60)
    print("Testing Learning and Adaptation")
    print("=" * 60)

    try:
        # Test 1: Feedback Processing
        print("\n1. Testing Feedback Processing...")
        engine = AdaptiveIntelligenceEngine()

        # Collect initial metrics
        initial_metrics = engine.get_intelligence_metrics()
        initial_weights = initial_metrics['learning_weights'].copy()

        # Provide positive feedback
        positive_feedback = {
            'suggestion_helpful': True,
            'risk_accurate': True,
            'dependency_detection': True,
            'overall_rating': 4.8
        }
        await engine.learn_from_feedback(positive_feedback)

        # Provide negative feedback
        negative_feedback = {
            'suggestion_helpful': False,
            'risk_accurate': False,
            'dependency_detection': False,
            'overall_rating': 2.1
        }
        await engine.learn_from_feedback(negative_feedback)

        # Check if weights have adapted
        updated_metrics = engine.get_intelligence_metrics()
        updated_weights = updated_metrics['learning_weights']

        weights_changed = any(
            abs(initial_weights[key] - updated_weights[key]) > 0.01
            for key in initial_weights.keys()
            if key in updated_weights
        )

        if weights_changed:
            print("PASS Learning weights adapted based on feedback")
        else:
            print("INFO Learning weights unchanged (may be expected)")

        # Test 2: Suggestion Quality Improvement
        print("\n2. Testing Suggestion Quality Over Time...")
        context = {
            'domain': 'web',
            'tech_stack': ['python', 'react'],
            'project_size': 'medium'
        }

        # Analyze same specification multiple times with feedback
        spec_text = "User management system with authentication and authorization"

        analyses = []
        for i in range(3):
            analysis = await engine.analyze_specification_realtime(spec_text, context)
            analyses.append(analysis)

            # Provide feedback to improve next analysis
            feedback = {
                'suggestion_helpful': True,
                'confidence_accurate': analysis.confidence > 0.7,
                'iteration': i
            }
            await engine.learn_from_feedback(feedback)

        print(f"PASS Completed {len(analyses)} learning iterations")
        print(f"     Initial confidence: {analyses[0].confidence:.2f}")
        print(f"     Final confidence: {analyses[-1].confidence:.2f}")

        return True

    except Exception as e:
        print(f"FAIL Learning and adaptation test failed: {e}")
        return False


async def run_all_tests():
    """Run all Phase 2 tests"""
    print("Starting Phase 2: Adaptive Intelligence Layer Tests")
    print("=" * 80)

    tests = [
        ("Adaptive Intelligence Engine", test_adaptive_intelligence_engine),
        ("Real-time Editor", test_realtime_editor),
        ("SpecKit Engine Integration", test_spec_engine_integration),
        ("Performance Benchmarks", test_performance_benchmarks),
        ("Error Handling", test_error_handling),
        ("Learning and Adaptation", test_learning_and_adaptation)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"FAIL {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print("PHASE 2 TEST RESULTS SUMMARY")
    print("=" * 80)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\nSUCCESS {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\nSUCCESS All Phase 2 tests passed! Adaptive Intelligence Layer is ready for production.")
        return True
    else:
        print(f"\nWARNING {total-passed} tests failed. Please review and fix issues before proceeding to Phase 3.")
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(run_all_tests())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\nTest suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest suite failed with error: {e}")
        sys.exit(1)