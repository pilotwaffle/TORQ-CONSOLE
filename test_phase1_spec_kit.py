#!/usr/bin/env python3
"""
Test Suite for Phase 1: Intelligent Spec-Driven Foundation
Comprehensive testing of Spec-Kit integration with TORQ Console
"""

import asyncio
import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

# Add TORQ Console to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'torq_console'))

from torq_console.spec_kit.spec_engine import SpecKitEngine, SpecificationContext
from torq_console.spec_kit.spec_commands import SpecKitCommands
from torq_console.spec_kit.rl_spec_analyzer import RLSpecAnalyzer
from torq_console.core.console import TorqConsole
from torq_console.core.config import TorqConfig


async def test_spec_kit_engine():
    """Test the core Spec-Kit Engine functionality"""
    print("\n" + "=" * 60)
    print("Testing Spec-Kit Engine")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Test 1: Engine Initialization
        print("\n1. Testing Engine Initialization...")
        try:
            engine = SpecKitEngine(workspace_path=temp_dir)
            await engine.initialize()
            print("PASS Engine initialized successfully")
        except Exception as e:
            print(f"FAIL Engine initialization failed: {e}")
            return False

        # Test 2: Constitution Creation
        print("\n2. Testing Constitution Creation...")
        try:
            constitution = await engine.create_constitution(
                name="TestApp",
                purpose="Build an amazing test application",
                principles=["Quality first", "User-centered design", "Maintainable code"],
                constraints=["Budget 50k", "Timeline 3 months", "Team size 5"],
                success_criteria=["1000+ users", "4.5+ rating", "Zero critical bugs"],
                stakeholders=["Development team", "Product owner", "End users"]
            )
            print(f"PASS Constitution created: {constitution.name}")
            print(f"     Purpose: {constitution.purpose}")
            print(f"     Principles: {len(constitution.principles)} items")
        except Exception as e:
            print(f"FAIL Constitution creation failed: {e}")
            return False

        # Test 3: Specification Creation with RL Analysis
        print("\n3. Testing Specification Creation with RL Analysis...")
        try:
            spec = await engine.create_specification(
                title="User Authentication System",
                description="Implement secure user login and registration with JWT tokens",
                requirements=[
                    "Users can register with email and password",
                    "Users can login securely",
                    "Password reset functionality",
                    "JWT token-based authentication",
                    "Role-based access control"
                ],
                acceptance_criteria=[
                    "All authentication tests pass",
                    "Security audit completed",
                    "Performance benchmarks met",
                    "UI/UX approved by design team"
                ],
                dependencies=["Database setup", "Email service", "Frontend framework"],
                tech_stack=["python", "jwt", "postgresql", "react", "redux"],
                timeline="3-weeks",
                complexity="medium",
                priority="high"
            )
            print(f"PASS Specification created: {spec.id} - {spec.title}")
            print(f"     Requirements: {len(spec.requirements)} items")
            print(f"     Tech Stack: {', '.join(spec.tech_stack)}")

            if spec.analysis:
                print(f"     RL Analysis:")
                print(f"       - Clarity: {spec.analysis.clarity_score:.2f}")
                print(f"       - Completeness: {spec.analysis.completeness_score:.2f}")
                print(f"       - Feasibility: {spec.analysis.feasibility_score:.2f}")
                print(f"       - Complexity: {spec.analysis.complexity_score:.2f}")
                print(f"       - Confidence: {spec.analysis.confidence:.2f}")
                print(f"       - Recommendations: {len(spec.analysis.recommendations)} items")
        except Exception as e:
            print(f"FAIL Specification creation failed: {e}")
            return False

        # Test 4: Task Plan Generation
        print("\n4. Testing Task Plan Generation...")
        try:
            task_plan = await engine.generate_task_plan(spec.id)
            print(f"PASS Task plan generated for {spec.id}")
            print(f"     Tasks: {len(task_plan.tasks)} items")
            print(f"     Milestones: {len(task_plan.milestones)} items")
            print(f"     Estimated Hours: {task_plan.resource_requirements.get('estimated_total_hours', 'N/A')}")
            print(f"     Recommended Team Size: {task_plan.resource_requirements.get('recommended_team_size', 'N/A')}")
            print(f"     Risk Mitigation: {len(task_plan.risk_mitigation)} strategies")
        except Exception as e:
            print(f"FAIL Task plan generation failed: {e}")
            return False

        # Test 5: Status and Search
        print("\n5. Testing Status and Search...")
        try:
            status = engine.get_status_summary()
            print(f"PASS Status retrieved:")
            print(f"     Constitutions: {status['constitutions']}")
            print(f"     Specifications: {status['specifications']}")
            print(f"     Task Plans: {status['task_plans']}")
            print(f"     RL Analyzer Active: {status['rl_analyzer_active']}")

            # Test search
            search_results = engine.search_specifications("authentication")
            print(f"     Search Results: {len(search_results)} found for 'authentication'")
        except Exception as e:
            print(f"FAIL Status/Search test failed: {e}")
            return False

    return True


async def test_spec_kit_commands():
    """Test the Spec-Kit command interface"""
    print("\n" + "=" * 60)
    print("Testing Spec-Kit Commands")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Initialize engine and commands
            engine = SpecKitEngine(workspace_path=temp_dir)
            await engine.initialize()
            commands = SpecKitCommands(engine)

            # Test 1: Help Command
            print("\n1. Testing Help Command...")
            help_result = await commands.handle_torq_spec_command("help", [])
            print(f"PASS Help command executed: {len(help_result)} characters")

            # Test 2: Constitution Commands
            print("\n2. Testing Constitution Commands...")
            const_result = await commands.handle_torq_spec_command("constitution", [
                "create", "TestProject", "Build awesome software",
                "--principles=Quality,Speed,Security",
                "--constraints=Time,Budget",
                "--criteria=Performance,Usability"
            ])
            print(f"PASS Constitution command executed: {'PASS' in const_result}")

            # Test 3: Specification Commands
            print("\n3. Testing Specification Commands...")
            spec_result = await commands.handle_torq_spec_command("specify", [
                "create", "API Gateway", "Central API management system",
                "--requirements=Authentication,Rate limiting,Logging",
                "--tech=python,fastapi,redis",
                "--complexity=large",
                "--priority=high"
            ])
            print(f"PASS Specification command executed: {'PASS' in spec_result}")

            # Test 4: Plan Generation
            print("\n4. Testing Plan Generation...")
            plan_result = await commands.handle_torq_spec_command("plan", ["generate", "spec_0001"])
            print(f"PASS Plan generation executed: {'PASS' in plan_result}")

            # Test 5: Status Commands
            print("\n5. Testing Status Commands...")
            status_result = await commands.handle_torq_spec_command("status", [])
            print(f"PASS Status command executed: {len(status_result)} characters")

            # Test 6: List Commands
            print("\n6. Testing List Commands...")
            list_result = await commands.handle_torq_spec_command("specify", ["list"])
            print(f"PASS List command executed: {len(list_result)} characters")

        except Exception as e:
            print(f"FAIL Command interface test failed: {e}")
            return False

    return True


async def test_rl_spec_analyzer():
    """Test the RL-powered specification analyzer"""
    print("\n" + "=" * 60)
    print("Testing RL Specification Analyzer")
    print("=" * 60)

    try:
        # Test 1: Analyzer Initialization
        print("\n1. Testing Analyzer Initialization...")
        analyzer = RLSpecAnalyzer()
        print("PASS RL Analyzer initialized")

        # Test 2: Specification Analysis
        print("\n2. Testing Specification Analysis...")
        context = SpecificationContext(
            domain="web",
            tech_stack=["python", "react", "postgresql"],
            project_size="medium",
            team_size=4,
            timeline="6-weeks",
            constraints=["Budget limitations", "Tight timeline"]
        )

        spec_text = """
        User Management System

        Build a comprehensive user management system that allows administrators
        to create, update, and delete user accounts. The system must include
        role-based access control, audit logging, and integration with external
        authentication providers like OAuth and SAML.

        Requirements:
        - User registration and login
        - Password reset functionality
        - Role and permission management
        - Audit trail for all user actions
        - OAuth/SAML integration
        - Multi-factor authentication
        - User profile management
        """

        analysis = await analyzer.analyze_specification(spec_text, context)
        print(f"PASS Specification analyzed:")
        print(f"     Clarity Score: {analysis.clarity_score:.2f}")
        print(f"     Completeness Score: {analysis.completeness_score:.2f}")
        print(f"     Feasibility Score: {analysis.feasibility_score:.2f}")
        print(f"     Complexity Score: {analysis.complexity_score:.2f}")
        print(f"     Confidence: {analysis.confidence:.2f}")
        print(f"     Recommendations: {len(analysis.recommendations)} items")
        print(f"     Risk Factors: {len(analysis.risk_assessment)} categories")

        # Test 3: Analysis Insights
        print("\n3. Testing Analysis Insights...")
        insights = analyzer.get_analysis_insights()
        print(f"PASS Analysis insights retrieved:")
        print(f"     Total Analyses: {insights.get('total_analyses', 0)}")

    except Exception as e:
        print(f"FAIL RL Analyzer test failed: {e}")
        return False

    return True


async def test_torq_console_integration():
    """Test integration with TORQ Console"""
    print("\n" + "=" * 60)
    print("Testing TORQ Console Integration")
    print("=" * 60)

    try:
        # Test 1: Console Initialization with Spec-Kit
        print("\n1. Testing Console Initialization with Spec-Kit...")
        config = TorqConfig.create_default()
        console = TorqConsole(
            config=config,
            repo_path=Path.cwd(),
            model="test-model"
        )
        await console.initialize_async()
        print("PASS Console initialized with Spec-Kit integration")

        # Test 2: Spec-Kit Command Processing
        print("\n2. Testing Spec-Kit Command Processing...")

        # Test help command
        help_result = await console.process_command("/torq-spec")
        print(f"PASS Help command processed: {len(help_result)} characters")

        # Test constitution command
        const_cmd = "/torq-spec constitution create TestApp 'Build amazing software'"
        const_result = await console.process_command(const_cmd)
        print(f"PASS Constitution command processed: {'PASS' in const_result}")

        # Test specification command
        spec_cmd = "/torq-spec specify create 'User Auth' 'Authentication system' --tech=python,jwt --priority=high"
        spec_result = await console.process_command(spec_cmd)
        print(f"PASS Specification command processed: {'PASS' in spec_result}")

        # Test status command
        status_result = await console.process_command("/torq-spec status")
        print(f"PASS Status command processed: {len(status_result)} characters")

        # Test 3: Engine Access
        print("\n3. Testing Engine Access...")
        if hasattr(console, 'spec_engine'):
            engine_status = console.spec_engine.get_status_summary()
            print(f"PASS Engine accessible: {engine_status['constitutions']} constitutions")
        else:
            print("FAIL Engine not accessible through console")
            return False

    except Exception as e:
        print(f"FAIL Console integration test failed: {e}")
        return False

    return True


async def test_error_handling():
    """Test error handling and edge cases"""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            engine = SpecKitEngine(workspace_path=temp_dir)
            await engine.initialize()
            commands = SpecKitCommands(engine)

            # Test 1: Invalid Commands
            print("\n1. Testing Invalid Commands...")
            invalid_result = await commands.handle_torq_spec_command("invalid", [])
            print(f"PASS Invalid command handled gracefully: {len(invalid_result)} characters")

            # Test 2: Missing Arguments
            print("\n2. Testing Missing Arguments...")
            missing_result = await commands.handle_torq_spec_command("constitution", ["create"])
            print(f"PASS Missing arguments handled: {'Usage:' in missing_result}")

            # Test 3: Non-existent Specification
            print("\n3. Testing Non-existent Specification...")
            nonexist_result = await commands.handle_torq_spec_command("plan", ["generate", "spec_9999"])
            print(f"PASS Non-existent spec handled: {'not found' in nonexist_result}")

        except Exception as e:
            print(f"FAIL Error handling test failed: {e}")
            return False

    return True


async def test_file_persistence():
    """Test file persistence and data integrity"""
    print("\n" + "=" * 60)
    print("Testing File Persistence")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Test 1: Create and Save Data
            print("\n1. Testing Data Creation and Persistence...")
            engine1 = SpecKitEngine(workspace_path=temp_dir)
            await engine1.initialize()

            # Create constitution
            await engine1.create_constitution(
                name="PersistTest",
                purpose="Test persistence",
                principles=["Test principle"],
                constraints=["Test constraint"],
                success_criteria=["Test criteria"],
                stakeholders=["Test stakeholder"]
            )

            # Create specification
            spec = await engine1.create_specification(
                title="Persistence Test Spec",
                description="Test specification persistence",
                requirements=["Test requirement"],
                acceptance_criteria=["Test criteria"],
                dependencies=[],
                tech_stack=["python"],
                timeline="1-week",
                complexity="small",
                priority="low"
            )

            print("PASS Data created and saved")

            # Test 2: Load Data in New Engine Instance
            print("\n2. Testing Data Loading...")
            engine2 = SpecKitEngine(workspace_path=temp_dir)
            await engine2.initialize()

            if "PersistTest" in engine2.constitutions:
                print("PASS Constitution persisted and loaded")
            else:
                print("FAIL Constitution not persisted")
                return False

            if spec.id in engine2.specifications:
                print("PASS Specification persisted and loaded")
            else:
                print("FAIL Specification not persisted")
                return False

            # Test 3: File Structure
            print("\n3. Testing File Structure...")
            spec_dir = Path(temp_dir) / ".torq-specs"
            if spec_dir.exists():
                files = list(spec_dir.glob("*.json"))
                print(f"PASS Spec directory created with {len(files)} files")
            else:
                print("FAIL Spec directory not created")
                return False

        except Exception as e:
            print(f"FAIL File persistence test failed: {e}")
            return False

    return True


async def run_all_tests():
    """Run all Phase 1 tests"""
    print("Starting Phase 1: Intelligent Spec-Driven Foundation Tests")
    print("=" * 80)

    tests = [
        ("Spec-Kit Engine", test_spec_kit_engine),
        ("Spec-Kit Commands", test_spec_kit_commands),
        ("RL Specification Analyzer", test_rl_spec_analyzer),
        ("TORQ Console Integration", test_torq_console_integration),
        ("Error Handling", test_error_handling),
        ("File Persistence", test_file_persistence)
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
    print("PHASE 1 TEST RESULTS SUMMARY")
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
        print("\nSUCCESS All Phase 1 tests passed! Ready for Phase 2 implementation.")
        return True
    else:
        print(f"\nWARNING {total-passed} tests failed. Please review and fix issues before proceeding to Phase 2.")
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