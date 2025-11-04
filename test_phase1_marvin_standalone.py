"""
Phase 1 Test Suite: Marvin Integration Foundation (Standalone)

Tests the Marvin integration layer without importing full TORQ Console.
This validates all Phase 1 components before proceeding to Phase 2.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Prevent imports of full TORQ Console
sys.modules['torq_console'] = None


def test_module_structure():
    """Test that marvin_integration module structure is correct."""
    marvin_path = os.path.join(os.path.dirname(__file__), 'torq_console', 'marvin_integration')

    # Check directory exists
    assert os.path.isdir(marvin_path), "marvin_integration directory should exist"

    # Check all required files exist
    required_files = [
        '__init__.py',
        'core.py',
        'models.py',
        'agents.py',
    ]

    for filename in required_files:
        filepath = os.path.join(marvin_path, filename)
        assert os.path.isfile(filepath), f"{filename} should exist"

    print("✓ Module structure is correct")


def test_imports_direct():
    """Test that direct imports work without full TORQ."""
    # Import directly from module files
    import importlib.util
    import sys

    base_path = os.path.join(os.path.dirname(__file__), 'torq_console', 'marvin_integration')

    # Test core module
    core_spec = importlib.util.spec_from_file_location(
        "marvin_integration.core",
        os.path.join(base_path, "core.py")
    )
    core_module = importlib.util.module_from_spec(core_spec)
    core_spec.loader.exec_module(core_module)

    assert hasattr(core_module, 'TorqMarvinIntegration'), "TorqMarvinIntegration should be defined"
    assert hasattr(core_module, 'logger'), "logger should be defined"

    print("✓ Core module imports successfully")

    # Test models module
    models_spec = importlib.util.spec_from_file_location(
        "marvin_integration.models",
        os.path.join(base_path, "models.py")
    )
    models_module = importlib.util.module_from_spec(models_spec)
    models_spec.loader.exec_module(models_module)

    assert hasattr(models_module, 'TorqSpecAnalysis'), "TorqSpecAnalysis should be defined"
    assert hasattr(models_module, 'TorqCodeReview'), "TorqCodeReview should be defined"
    assert hasattr(models_module, 'TorqResearchFindings'), "TorqResearchFindings should be defined"
    assert hasattr(models_module, 'TorqTaskBreakdown'), "TorqTaskBreakdown should be defined"
    assert hasattr(models_module, 'IntentClassification'), "IntentClassification should be defined"

    print("✓ Models module imports successfully")

    # Test agents module
    agents_spec = importlib.util.spec_from_file_location(
        "marvin_integration.agents",
        os.path.join(base_path, "agents.py")
    )
    agents_module = importlib.util.module_from_spec(agents_spec)
    agents_spec.loader.exec_module(agents_module)

    assert hasattr(agents_module, 'create_spec_analyzer'), "create_spec_analyzer should be defined"
    assert hasattr(agents_module, 'create_code_reviewer'), "create_code_reviewer should be defined"
    assert hasattr(agents_module, 'create_research_agent'), "create_research_agent should be defined"
    assert hasattr(agents_module, 'get_agent'), "get_agent should be defined"
    assert hasattr(agents_module, 'AGENT_REGISTRY'), "AGENT_REGISTRY should be defined"

    print("✓ Agents module imports successfully")


def test_pydantic_models():
    """Test Pydantic models validate correctly."""
    import importlib.util

    base_path = os.path.join(os.path.dirname(__file__), 'torq_console', 'marvin_integration')

    # Load models module
    models_spec = importlib.util.spec_from_file_location(
        "marvin_integration.models",
        os.path.join(base_path, "models.py")
    )
    models_module = importlib.util.module_from_spec(models_spec)
    models_spec.loader.exec_module(models_module)

    # Test TorqSpecAnalysis
    TorqSpecAnalysis = models_module.TorqSpecAnalysis
    AnalysisConfidence = models_module.AnalysisConfidence

    analysis = TorqSpecAnalysis(
        clarity_score=0.85,
        completeness_score=0.70,
        feasibility_score=0.90,
        confidence=AnalysisConfidence.HIGH,
        missing_requirements=["Error handling not defined"],
        recommendations=["Add error handling requirements"],
        technical_risks=["Database scalability"],
        strengths=["Clear API structure"],
        summary="Good foundation, needs error handling details"
    )

    assert analysis.clarity_score == 0.85
    assert analysis.completeness_score == 0.70
    assert analysis.confidence == AnalysisConfidence.HIGH

    print("✓ TorqSpecAnalysis validates correctly")

    # Test CodeIssue and TorqCodeReview
    CodeIssue = models_module.CodeIssue
    TorqCodeReview = models_module.TorqCodeReview
    Severity = models_module.Severity

    issue = CodeIssue(
        severity=Severity.WARNING,
        line_number=42,
        description="Potential division by zero",
        suggestion="Add zero check",
        category="safety"
    )

    review = TorqCodeReview(
        quality_score=7.5,
        issues=[issue],
        summary="Good code",
        positive_aspects=["Clean"],
        security_concerns=[],
        performance_notes=[],
        maintainability_score=8.0,
        test_coverage_assessment="Good"
    )

    assert review.quality_score == 7.5
    assert len(review.issues) == 1

    print("✓ TorqCodeReview validates correctly")

    # Test enums
    IntentClassification = models_module.IntentClassification
    Priority = models_module.Priority

    assert IntentClassification.SPEC_CREATE.value == "spec_create"
    assert Priority.HIGH.value == "high"

    print("✓ Enum classifications work correctly")


def test_torq_marvin_integration_class():
    """Test TorqMarvinIntegration class structure."""
    import importlib.util

    base_path = os.path.join(os.path.dirname(__file__), 'torq_console', 'marvin_integration')

    # Load core module
    core_spec = importlib.util.spec_from_file_location(
        "marvin_integration.core",
        os.path.join(base_path, "core.py")
    )
    core_module = importlib.util.module_from_spec(core_spec)
    core_spec.loader.exec_module(core_module)

    TorqMarvinIntegration = core_module.TorqMarvinIntegration

    # Test initialization
    integration = TorqMarvinIntegration()

    assert hasattr(integration, 'model'), "Should have model attribute"
    assert hasattr(integration, 'metrics'), "Should have metrics attribute"
    assert hasattr(integration, 'extract'), "Should have extract method"
    assert hasattr(integration, 'cast'), "Should have cast method"
    assert hasattr(integration, 'classify'), "Should have classify method"
    assert hasattr(integration, 'generate'), "Should have generate method"
    assert hasattr(integration, 'run'), "Should have run method"
    assert hasattr(integration, 'create_agent'), "Should have create_agent method"

    # Test default model
    assert integration.model == "anthropic/claude-sonnet-4-20250514"

    # Test metrics initialization
    assert integration.metrics['extractions'] == 0
    assert integration.metrics['casts'] == 0
    assert integration.metrics['classifications'] == 0
    assert integration.metrics['generations'] == 0
    assert integration.metrics['task_runs'] == 0

    print("✓ TorqMarvinIntegration class structure is correct")

    # Test get_metrics
    metrics = integration.get_metrics()
    assert isinstance(metrics, dict)
    assert 'extractions' in metrics

    print("✓ get_metrics() works correctly")

    # Test reset_metrics
    integration.metrics['extractions'] = 10
    integration.reset_metrics()
    assert integration.metrics['extractions'] == 0

    print("✓ reset_metrics() works correctly")


def test_agent_factories():
    """Test agent factory functions."""
    import importlib.util
    import marvin

    base_path = os.path.join(os.path.dirname(__file__), 'torq_console', 'marvin_integration')

    # Load agents module
    agents_spec = importlib.util.spec_from_file_location(
        "marvin_integration.agents",
        os.path.join(base_path, "agents.py")
    )
    agents_module = importlib.util.module_from_spec(agents_spec)
    agents_spec.loader.exec_module(agents_module)

    # Test create_spec_analyzer
    create_spec_analyzer = agents_module.create_spec_analyzer
    agent = create_spec_analyzer()

    assert isinstance(agent, marvin.Agent)
    assert agent.name == "Spec Analyzer"
    assert "specification" in agent.instructions.lower()

    print("✓ create_spec_analyzer() works correctly")

    # Test create_code_reviewer
    create_code_reviewer = agents_module.create_code_reviewer
    agent = create_code_reviewer()

    assert isinstance(agent, marvin.Agent)
    assert agent.name == "Code Reviewer"

    print("✓ create_code_reviewer() works correctly")

    # Test create_research_agent
    create_research_agent = agents_module.create_research_agent
    agent = create_research_agent()

    assert isinstance(agent, marvin.Agent)
    assert agent.name == "Research Specialist"

    print("✓ create_research_agent() works correctly")

    # Test get_agent
    get_agent = agents_module.get_agent
    agent = get_agent("spec_analyzer")

    assert isinstance(agent, marvin.Agent)
    assert agent.name == "Spec Analyzer"

    print("✓ get_agent() works correctly")

    # Test invalid agent type
    try:
        get_agent("nonexistent_agent")
        assert False, "Should raise ValueError for invalid agent type"
    except ValueError as e:
        assert "Unknown agent type" in str(e)

    print("✓ get_agent() raises ValueError for invalid types")

    # Test AGENT_REGISTRY
    AGENT_REGISTRY = agents_module.AGENT_REGISTRY
    assert "spec_analyzer" in AGENT_REGISTRY
    assert "code_reviewer" in AGENT_REGISTRY
    assert "research_agent" in AGENT_REGISTRY
    assert "task_planner" in AGENT_REGISTRY
    assert "spec_kit_orchestrator" in AGENT_REGISTRY

    print("✓ AGENT_REGISTRY contains all expected agents")


def test_marvin_dependency():
    """Test that Marvin is installed and accessible."""
    try:
        import marvin
        print(f"✓ Marvin is installed (version: {marvin.__version__})")

        # Test basic Marvin components
        assert hasattr(marvin, 'extract'), "Marvin should have extract"
        assert hasattr(marvin, 'cast'), "Marvin should have cast"
        assert hasattr(marvin, 'classify'), "Marvin should have classify"
        assert hasattr(marvin, 'generate'), "Marvin should have generate"
        assert hasattr(marvin, 'run'), "Marvin should have run"
        assert hasattr(marvin, 'Agent'), "Marvin should have Agent"
        assert hasattr(marvin, 'Thread'), "Marvin should have Thread"

        print("✓ All Marvin core components are available")

    except ImportError as e:
        print(f"✗ Marvin import failed: {e}")
        raise


def test_pydantic_dependency():
    """Test that Pydantic is installed and working."""
    try:
        from pydantic import BaseModel, Field

        class TestModel(BaseModel):
            score: float = Field(ge=0.0, le=1.0)
            name: str

        model = TestModel(score=0.5, name="test")
        assert model.score == 0.5
        assert model.name == "test"

        print("✓ Pydantic is working correctly")

    except ImportError as e:
        print(f"✗ Pydantic import failed: {e}")
        raise


def run_all_tests():
    """Run all Phase 1 standalone tests."""
    print("=" * 70)
    print("PHASE 1 TEST SUITE: Marvin Integration Foundation (Standalone)")
    print("=" * 70)
    print()

    tests = [
        ("Module Structure", test_module_structure),
        ("Direct Imports", test_imports_direct),
        ("Pydantic Models", test_pydantic_models),
        ("TorqMarvinIntegration Class", test_torq_marvin_integration_class),
        ("Agent Factories", test_agent_factories),
        ("Marvin Dependency", test_marvin_dependency),
        ("Pydantic Dependency", test_pydantic_dependency),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        print("-" * 70)
        try:
            test_func()
            passed += 1
            print(f"✅ {test_name} PASSED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()

    print()
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 70)

    if failed == 0:
        print("✅ PHASE 1 TESTS PASSED - Ready to proceed to Phase 2")
        return 0
    else:
        print("❌ PHASE 1 TESTS FAILED - Fix issues before proceeding")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
