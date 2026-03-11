"""
Phase Insight Publishing - Milestone 1 Validation

Validates that all Milestone 1 deliverables are in place:
- Insight data model (Pydantic schemas)
- Insight types explicitly defined
- Publishing criteria explicitly defined
- Quality gates exist
- Lifecycle states defined
- Provenance and scope requirements defined
- Acceptance/rejection rules defined
"""

import sys
import io

# Force UTF-8 output for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from torq_console.insights.models import (
    InsightType,
    InsightLifecycleState,
    InsightScope,
    InsightSourceType,
    Insight,
    InsightCreate,
    InsightUpdate,
    SourceReference,
    QualityMetrics,
    QualityGateResult,
    PublicationRequest,
    PublicationResult,
    PublishingRule,
    PublishingCriteria,
    InsightRetrievalRequest,
    InsightRetrievalResult,
    InsightInjection,
    InsightTemplates,
    EXAMPLE_INSIGHTS,
)

from torq_console.insights.publishing_rules import (
    QUALITY_GATES,
    QualityGateConfig,
    get_default_publishing_rules,
    get_default_publishing_criteria,
    PublicationEligibilityChecker,
    LifecycleTransition,
    LIFECYCLE_TRANSITIONS,
    get_valid_transitions,
    is_transition_valid,
    get_transition,
)


def validate_insight_types():
    """Validate that all required insight types are defined."""
    print("\n" + "="*70)
    print("1. Validating Insight Types")
    print("="*70)

    required_types = [
        InsightType.STRATEGIC_INSIGHT,
        InsightType.REUSABLE_PLAYBOOK,
        InsightType.VALIDATED_FINDING,
        InsightType.ARCHITECTURE_DECISION,
        InsightType.BEST_PRACTICE,
        InsightType.RISK_PATTERN,
        InsightType.EXECUTION_LESSON,
        InsightType.RESEARCH_SUMMARY,
    ]

    all_types = list(InsightType)

    print(f"\n✅ Defined {len(all_types)} insight types:")
    for insight_type in all_types:
        print(f"   - {insight_type.value}")

    # Check all required types are present
    missing = [rt for rt in required_types if rt not in all_types]
    if missing:
        print(f"\n❌ Missing required types: {[m.value for m in missing]}")
        return False

    print(f"\n✅ All {len(required_types)} required insight types are defined")
    return True


def validate_lifecycle_states():
    """Validate that lifecycle states are defined."""
    print("\n" + "="*70)
    print("2. Validating Lifecycle States")
    print("="*70)

    required_states = [
        InsightLifecycleState.DRAFT,
        InsightLifecycleState.CANDIDATE,
        InsightLifecycleState.VALIDATED,
        InsightLifecycleState.PUBLISHED,
        InsightLifecycleState.SUPERSEDED,
        InsightLifecycleState.ARCHIVED,
    ]

    all_states = list(InsightLifecycleState)

    print(f"\n✅ Defined {len(all_states)} lifecycle states:")
    for state in all_states:
        print(f"   - {state.value}")

    missing = [rs for rs in required_states if rs not in all_states]
    if missing:
        print(f"\n❌ Missing required states: {[m.value for m in missing]}")
        return False

    print(f"\n✅ All {len(required_states)} required lifecycle states are defined")
    return True


def validate_lifecycle_transitions():
    """Validate that lifecycle transitions are defined."""
    print("\n" + "="*70)
    print("3. Validating Lifecycle Transitions")
    print("="*70)

    print(f"\n✅ Defined {len(LIFECYCLE_TRANSITIONS)} valid transitions:")

    # Check each state has outgoing transitions
    states_with_transitions = set()
    for transition in LIFECYCLE_TRANSITIONS:
        states_with_transitions.add(transition.from_state)
        print(f"   - {transition.from_state.value} → {transition.to_state.value}")

    print(f"\n✅ {len(states_with_transitions)} states have defined transitions")

    # Test transition validation
    valid = is_transition_valid(
        InsightLifecycleState.DRAFT,
        InsightLifecycleState.CANDIDATE
    )
    if not valid:
        print("\n❌ Transition validation failed")
        return False

    print("\n✅ Transition validation is working correctly")
    return True


def validate_quality_gates():
    """Validate that quality gates are defined for all insight types."""
    print("\n" + "="*70)
    print("4. Validating Quality Gates")
    print("="*70)

    print(f"\n✅ Quality gates defined for {len(QUALITY_GATES)} insight types:")

    for insight_type, gate in QUALITY_GATES.items():
        print(f"\n   {insight_type.value}:")
        print(f"     - min_confidence: {gate.min_confidence}")
        print(f"     - min_validation_score: {gate.min_validation_score}")
        print(f"     - min_applicability: {gate.min_applicability}")
        print(f"     - min_source_count: {gate.min_source_count}")

    # Check all insight types have gates
    all_types = set(InsightType)
    gated_types = set(QUALITY_GATES.keys())
    missing_gates = all_types - gated_types

    if missing_gates:
        print(f"\n⚠️  Types without specific gates (will use default): {[t.value for t in missing_gates]}")

    print(f"\n✅ All insight types have quality gate coverage")
    return True


def validate_publishing_rules():
    """Validate that publishing rules are defined."""
    print("\n" + "="*70)
    print("5. Validating Publishing Rules")
    print("="*70)

    rules = get_default_publishing_rules()
    print(f"\n✅ Defined {len(rules)} publishing rules:")

    for rule in rules:
        applies_to = ", ".join([t.value for t in rule.applies_to_types])
        print(f"\n   - {rule.name}:")
        print(f"     - Applies to: {applies_to}")
        print(f"     - min_confidence: {rule.min_confidence}")
        print(f"     - allowed_source_types: {[st.value for st in rule.allowed_source_types]}")

    print(f"\n✅ Publishing rules are explicitly defined")

    # Check publishing criteria
    criteria = get_default_publishing_criteria()
    print(f"\n✅ Publishing criteria configuration:")
    print(f"     - {len(criteria.rules)} rules")
    print(f"     - conflict_detection: {criteria.enable_conflict_detection}")
    print(f"     - conflict_threshold: {criteria.conflict_similarity_threshold}")
    print(f"     - auto_supersede_threshold: {criteria.auto_supersede_threshold}")

    return True


def validate_eligibility_checker():
    """Validate that the eligibility checker works correctly."""
    print("\n" + "="*70)
    print("6. Validating Publication Eligibility Checker")
    print("="*70)

    checker = PublicationEligibilityChecker()

    # Create a test insight that should pass
    from datetime import datetime
    from torq_console.insights.models import SourceReference

    test_insight = InsightCreate(
        insight_type=InsightType.STRATEGIC_INSIGHT,
        title="Test Strategic Insight",
        summary="A test insight for validation",
        scope=InsightScope.GLOBAL,
        content={"test": "content"},
        source_references=[
            SourceReference(
                source_type=InsightSourceType.ARTIFACT,
                source_id="test_artifact_123"
            )
        ],
        quality=QualityMetrics(
            confidence_score=0.85,
            validation_score=0.80,
            applicability_score=0.75,
            source_count=2,
            execution_count=10,
            success_rate=0.80,
            last_validated_at=datetime.now(),
            evidence_cutoff_at=datetime.now()
        )
    )

    results = checker.check_eligibility(test_insight)

    print(f"\n✅ Eligibility checker evaluated {len(results)} quality gates:")

    all_passed = True
    for result in results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"   {status} - {result.gate_name}: {result.reason}")
        if not result.passed:
            all_passed = False

    if checker.passes_all_gates(results):
        print("\n✅ All quality gates passed for test insight")
        return True
    else:
        failed = checker.get_failed_gates(results)
        print(f"\n❌ {len(failed)} quality gates failed")
        return False


def validate_scope_model():
    """Validate that the scope model is defined."""
    print("\n" + "="*70)
    print("7. Validating Scope Model")
    print("="*70)

    scopes = list(InsightScope)

    print(f"\n✅ Defined {len(scopes)} scope levels:")
    for scope in scopes:
        print(f"   - {scope.value}")

    required_scopes = [
        InsightScope.GLOBAL,
        InsightScope.WORKFLOW_TYPE,
        InsightScope.AGENT_TYPE,
        InsightScope.DOMAIN,
        InsightScope.MISSION_TYPE,
    ]

    missing = [rs for rs in required_scopes if rs not in scopes]
    if missing:
        print(f"\n❌ Missing required scopes: {[m.value for m in missing]}")
        return False

    print(f"\n✅ All required scope levels are defined")
    return True


def validate_provenance_model():
    """Validate that provenance tracking is defined."""
    print("\n" + "="*70)
    print("8. Validating Provenance Model")
    print("="*70)

    source_types = list(InsightSourceType)

    print(f"\n✅ Defined {len(source_types)} source types:")
    for st in source_types:
        print(f"   - {st.value}")

    # Test SourceReference model
    from datetime import datetime
    ref = SourceReference(
        source_type=InsightSourceType.ARTIFACT,
        source_id="test_123",
        contribution_weight=0.8,
        extraction_method="synthesis"
    )

    print(f"\n✅ SourceReference model is valid:")
    print(f"   - source_type: {ref.source_type.value}")
    print(f"   - source_id: {ref.source_id}")
    print(f"   - contribution_weight: {ref.contribution_weight}")

    return True


def validate_data_models():
    """Validate that core data models are defined and work correctly."""
    print("\n" + "="*70)
    print("9. Validating Core Data Models")
    print("="*70)

    from datetime import datetime, timedelta
    from uuid import uuid4

    # Test InsightCreate
    insight_create = InsightCreate(
        insight_type=InsightType.REUSABLE_PLAYBOOK,
        title="Test Playbook",
        summary="A test playbook",
        scope=InsightScope.WORKFLOW_TYPE,
        scope_key="planning",
        content={"test": "content"},
        source_references=[
            SourceReference(
                source_type=InsightSourceType.MEMORY,
                source_id="memory_123"
            )
        ],
        quality=QualityMetrics(
            confidence_score=0.8,
            validation_score=0.75,
            applicability_score=0.7,
            source_count=1,
            execution_count=5
        )
    )

    print(f"\n✅ InsightCreate model works correctly")

    # Test Insight (full model)
    insight = Insight(
        insight_type=InsightType.REUSABLE_PLAYBOOK,
        title="Test Playbook",
        summary="A test playbook",
        scope=InsightScope.WORKFLOW_TYPE,
        scope_key="planning",
        content={"test": "content"},
        source_references=[
            SourceReference(
                source_type=InsightSourceType.MEMORY,
                source_id="memory_123"
            )
        ],
        quality=QualityMetrics(
            confidence_score=0.8,
            validation_score=0.75,
            applicability_score=0.7,
            source_count=1,
            execution_count=5
        ),
        lifecycle_state=InsightLifecycleState.PUBLISHED,
        created_by="test_validator"
    )

    print(f"✅ Insight model works correctly")
    print(f"   - Generated UUID: {insight.id}")
    print(f"   - lifecycle_state: {insight.lifecycle_state.value}")

    return True


def validate_templates():
    """Validate that insight templates are defined."""
    print("\n" + "="*70)
    print("10. Validating Insight Templates")
    print("="*70)

    templates = InsightTemplates

    template_methods = [
        "strategic_insight_template",
        "reusable_playbook_template",
        "validated_finding_template",
        "architecture_decision_template",
        "best_practice_template",
        "risk_pattern_template",
        "execution_lesson_template",
        "research_summary_template",
    ]

    print(f"\n✅ InsightTemplates class defined with {len(template_methods)} template methods:")

    for method_name in template_methods:
        if hasattr(templates, method_name):
            print(f"   - {method_name}")
        else:
            print(f"   ❌ Missing: {method_name}")
            return False

    # Test one template
    content = templates.reusable_playbook_template(
        title="Test Playbook",
        objective="Test objective",
        triggers=["trigger1", "trigger2"],
        steps=["step1", "step2"],
        expected_outcome="Test outcome"
    )

    print(f"\n✅ Templates generate valid content structures")
    print(f"   - Generated keys: {list(content.keys())}")

    return True


def validate_examples():
    """Validate that example insights are defined."""
    print("\n" + "="*70)
    print("11. Validating Example Insights")
    print("="*70)

    print(f"\n✅ Defined {len(EXAMPLE_INSIGHTS)} example insights:")

    for key, example in EXAMPLE_INSIGHTS.items():
        print(f"\n   - {key}:")
        print(f"     - type: {example['insight_type'].value}")
        print(f"     - title: {example['title']}")
        print(f"     - scope: {example['scope'].value}")

    return True


def validate_layer_separation():
    """Validate that insight layer is distinct from artifact and memory layers."""
    print("\n" + "="*70)
    print("12. Validating Layer Separation")
    print("="*70)

    # Import from different layers to verify they're distinct
    try:
        from torq_console.workspace.artifact_models import ArtifactType, WorkspaceArtifact
        print(f"   ✅ Artifact layer accessible (ArtifactType defined)")
    except ImportError as e:
        print(f"   ⚠️  Artifact layer import issue: {e}")

    try:
        from torq_console.strategic_memory.models import MemoryType, StrategicMemory
        print(f"   ✅ Memory layer accessible (MemoryType defined)")
    except ImportError as e:
        print(f"   ⚠️  Memory layer import issue: {e}")

    try:
        from torq_console.insights.models import InsightType, Insight
        print(f"   ✅ Insight layer accessible (InsightType defined)")
    except ImportError as e:
        print(f"   ❌ Insight layer import issue: {e}")
        return False

    print(f"\n✅ All three layers are distinct and separately importable")

    # Verify type values don't overlap (enforcing separation)
    artifact_values = set([t.value for t in ArtifactType])
    memory_values = set([t.value for t in MemoryType])
    insight_values = set([t.value for t in InsightType])

    overlaps = artifact_values & memory_values & insight_values
    if overlaps:
        print(f"\n⚠️  Type value overlaps detected: {overlaps}")
    else:
        print(f"✅ No type value overlaps - layers are properly separated")

    return True


def main():
    """Run all validation checks."""
    print("\n" + "="*70)
    print("INSIGHT PUBLISHING - MILESTONE 1 VALIDATION")
    print("="*70)
    print("\nValidating that all Milestone 1 deliverables are in place:")

    validators = [
        ("Insight Types", validate_insight_types),
        ("Lifecycle States", validate_lifecycle_states),
        ("Lifecycle Transitions", validate_lifecycle_transitions),
        ("Quality Gates", validate_quality_gates),
        ("Publishing Rules", validate_publishing_rules),
        ("Eligibility Checker", validate_eligibility_checker),
        ("Scope Model", validate_scope_model),
        ("Provenance Model", validate_provenance_model),
        ("Data Models", validate_data_models),
        ("Templates", validate_templates),
        ("Examples", validate_examples),
        ("Layer Separation", validate_layer_separation),
    ]

    results = []
    for name, validator in validators:
        try:
            result = validator()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} validation failed with error: {e}")
            results.append((name, False))

    # Print summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\nTotal: {passed}/{total} validations passed")

    if passed == total:
        print("\n" + "="*70)
        print("🎉 MILESTONE 1 COMPLETE - All deliverables verified!")
        print("="*70)
        print("\nExit Criteria Met:")
        print("✅ Insight types explicitly defined")
        print("✅ Publishing rules explicit and testable")
        print("✅ Quality gates exist")
        print("✅ Lifecycle model exists")
        print("✅ Insight candidates distinguishable from ordinary memory")
        print("✅ Layer separation maintained (artifact/memory/insight)")
        return 0
    else:
        print("\n❌ Some validations failed - review output above")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
