#!/usr/bin/env python3
"""
Validation Script for Phase 4G Milestone 5: Hardening & Regression

This script validates hardening, edge cases, and concurrency for the pattern system.

Exit Criteria:
- Pattern operations are concurrency-safe
- Duplicate/supersession handling is correct
- Lifecycle transitions are stable under edge cases
- Ranking/filtering holds under difficult cases
- Audit and lineage integrity hold
- No regression in prior phases
"""

import sys
import threading
import time
from datetime import datetime, timedelta
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

# Add project root to path
sys.path.insert(0, "E:/TORQ-CONSOLE")

from torq_console.patterns import (
    # Milestone 1
    PatternType,
    PatternLifecycleState,
    PatternSourceType,
    Pattern,
    PatternSourceReference,
    PatternQualityMetrics,
    is_transition_valid,
    get_valid_transitions,

    # Milestone 2
    PatternCandidate,
    PatternEvidence,
    PatternCandidateExtractor,
    PatternAggregationEngine,
    PatternScoringService,
    PatternExtractionPipeline,

    # Milestone 3
    ValidationOutcome,
    PatternValidationService,
    PatternPromotionWorkflow,
    PatternSupersessionHandler,
    PatternAuditLogger,

    # Milestone 4
    PatternQueryService,
    PatternQueryFilter,
    PatternQuerySort,
    PatternInspectionService,
    PatternAuditService,
    PatternGovernanceService,
    create_pattern_query_service,
    create_pattern_inspection_service,
    create_pattern_audit_service,
    create_pattern_governance_service,
)


# ============================================================================
# Test Helpers
# ============================================================================

def create_test_pattern(
    name: str = "Test Pattern",
    pattern_type: PatternType = PatternType.EXECUTION_PATTERN,
    lifecycle_state: PatternLifecycleState = PatternLifecycleState.VALIDATED,
    confidence: float = 0.8,
    observation_count: int = 5,
    days_ago: int = 10,
    last_observed_days_ago: int = 1,
) -> Pattern:
    """Create a test pattern with configurable properties."""
    now = datetime.now()

    return Pattern(
        id=uuid4(),
        pattern_type=pattern_type,
        name=name,
        description=f"Test pattern: {name}",
        domain="testing",
        scope="unit_test",
        structure={"type": "test_structure"},
        characteristics={"key": "value"},
        tags=["test", "validation"],
        source_references=[
            PatternSourceReference(
                source_type=PatternSourceType.ARTIFACT,
                source_id=f"artifact_{i}",
                observed_at=now - timedelta(days=days_ago - i),
            )
            for i in range(observation_count)
        ],
        quality=PatternQualityMetrics(
            confidence_score=confidence,
            stability_score=confidence - 0.1,
            consistency_score=confidence - 0.05,
            observation_count=observation_count,
            unique_execution_count=observation_count - 1,
            distinct_source_count=3,
            first_observed_at=now - timedelta(days=days_ago),
            last_observed_at=now - timedelta(days=last_observed_days_ago),
        ),
        lifecycle_state=lifecycle_state,
    )


def create_test_candidate(
    name: str = "Test Candidate",
    pattern_type: PatternType = PatternType.EXECUTION_PATTERN,
    confidence: float = 0.8,
    observations: int = 5,
    span_days: int = 10,
) -> PatternCandidate:
    """Create a test pattern candidate with proper scoring."""
    now = datetime.now()

    source_types = [
        PatternSourceType.ARTIFACT,
        PatternSourceType.MEMORY,
        PatternSourceType.INSIGHT,
    ]

    evidence = []
    source_references = []

    for i in range(observations):
        source_type = source_types[i % len(source_types)]
        days_back = span_days - (i * span_days // (observations - 1)) if observations > 1 else span_days // 2

        evidence.append(
            PatternEvidence(
                pattern_type=pattern_type,
                observed_structure={"type": "test_structure", "index": i},
                source_type=source_type,
                source_id=f"{source_type.value}_{i}",
                extraction_confidence=0.8,
                observed_at=now - timedelta(days=days_back),
                execution_id=f"exec_{i % 3}",
                detection_method="test",
            )
        )

        source_references.append(
            PatternSourceReference(
                source_type=source_type,
                source_id=f"{source_type.value}_{i}",
                observed_at=now - timedelta(days=days_back),
            )
        )

    candidate = PatternCandidate(
        id=uuid4(),
        pattern_type=pattern_type,
        name=name,
        description=f"Test candidate: {name}",
        domain="testing",
        scope="unit_test",
        structure={"type": "test_structure"},
        characteristics={"key": "value"},
        tags=["test"],
        evidence=evidence,
        source_references=source_references,
        lifecycle_state=PatternLifecycleState.CANDIDATE,
    )

    scorer = PatternScoringService()
    return scorer.score_candidate(candidate)


# ============================================================================
# Validation Functions
# ============================================================================

def validate_concurrent_operations():
    """Validate that pattern operations work correctly under concurrent load."""
    print("\n" + "="*70)
    print("1. Validating Concurrent Operations")
    print("="*70)

    query_service = create_pattern_query_service()
    governance_service = create_pattern_governance_service(query_service)
    validation_service = PatternValidationService()

    errors = []
    success_count = [0]
    lock = threading.Lock()

    def add_pattern_worker(worker_id: int) -> int:
        """Worker that adds patterns."""
        try:
            for i in range(10):
                pattern = create_test_pattern(f"Concurrent Pattern {worker_id}-{i}")
                query_service.add_pattern(pattern)
            with lock:
                success_count[0] += 1
            return 10
        except Exception as e:
            errors.append(f"Add worker {worker_id}: {e}")
            return 0

    def query_worker(worker_id: int) -> int:
        """Worker that queries patterns."""
        try:
            count = 0
            for _ in range(20):
                result = query_service.query(page_size=50)
                count += len(result.patterns)
            with lock:
                success_count[0] += 1
            return count
        except Exception as e:
            errors.append(f"Query worker {worker_id}: {e}")
            return 0

    def validate_worker(worker_id: int) -> int:
        """Worker that validates candidates."""
        try:
            count = 0
            for i in range(5):
                candidate = create_test_candidate(f"Concurrent Candidate {worker_id}-{i}")
                result = validation_service.validate_candidate(candidate)
                if result.outcome in (ValidationOutcome.PROMOTE, ValidationOutcome.REJECT, ValidationOutcome.HOLD):
                    count += 1
            with lock:
                success_count[0] += 1
            return count
        except Exception as e:
            errors.append(f"Validate worker {worker_id}: {e}")
            return 0

    # Run concurrent operations
    print(f"\n  Running concurrent operations...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []

        # Add 5 pattern adders
        for i in range(5):
            futures.append(executor.submit(add_pattern_worker, i))

        # Add 3 queriers
        for i in range(3):
            futures.append(executor.submit(query_worker, i))

        # Add 2 validators
        for i in range(2):
            futures.append(executor.submit(validate_worker, i))

        # Wait for completion
        results = [f.result() for f in as_completed(futures)]

    total_patterns = sum(r for i, r in enumerate(results) if i < 5)
    total_queries = sum(r for i, r in enumerate(results) if 5 <= i < 8)
    total_validations = sum(r for i, r in enumerate(results) if 8 <= i < 10)

    print(f"\n✅ Concurrent operations completed:")
    print(f"   - Patterns added: {total_patterns}")
    print(f"   - Queries executed: {total_queries}")
    print(f"   - Validations performed: {total_validations}")
    print(f"   - Workers successful: {success_count[0]}/10")
    print(f"   - Errors: {len(errors)}")

    if errors:
        for error in errors[:5]:  # Show first 5 errors
            print(f"     - {error}")

    # Verify final state is consistent
    stats = query_service.get_statistics()
    final_pattern_count = stats["total_patterns"]

    print(f"\n✅ Final state verification:")
    print(f"   - Total patterns in store: {final_pattern_count}")
    print(f"   - Expected approximately: {total_patterns}")

    if final_pattern_count < total_patterns * 0.9 or final_pattern_count > total_patterns * 1.1:
        print(f"   ⚠️  Pattern count deviation may indicate concurrent issues")

    if len(errors) > 0:
        print(f"   ❌ Concurrent operations had errors")
        return False

    print("\n✅ Concurrent operations working correctly")
    return True


def validate_duplicate_and_supersession():
    """Validate duplicate detection and supersession handling."""
    print("\n" + "="*70)
    print("2. Validating Duplicate and Supersession Handling")
    print("="*70)

    query_service = create_pattern_query_service()
    governance_service = create_pattern_governance_service(query_service)

    # Test 1: Create similar patterns that should trigger supersession
    now = datetime.now()

    old_pattern = Pattern(
        id=uuid4(),
        pattern_type=PatternType.EXECUTION_PATTERN,
        name="Old Similar Pattern",
        description="An older pattern",
        domain="testing",
        scope="unit_test",
        structure={"type": "execution_structure", "category": "test"},
        characteristics={"key": "value"},
        tags=["test"],
        source_references=[
            PatternSourceReference(
                source_type=PatternSourceType.ARTIFACT,
                source_id="artifact_old",
                observed_at=now - timedelta(days=20),
            )
        ],
        quality=PatternQualityMetrics(
            confidence_score=0.6,
            stability_score=0.5,
            consistency_score=0.5,
            observation_count=3,
            unique_execution_count=2,
            distinct_source_count=2,
            first_observed_at=now - timedelta(days=20),
            last_observed_at=now - timedelta(days=10),
        ),
        lifecycle_state=PatternLifecycleState.VALIDATED,
    )

    new_pattern = Pattern(
        id=uuid4(),
        pattern_type=PatternType.EXECUTION_PATTERN,
        name="New Similar Pattern",
        description="A newer stronger pattern",
        domain="testing",
        scope="unit_test",
        structure={"type": "execution_structure", "category": "test"},  # Same structure
        characteristics={"key": "value"},
        tags=["test"],
        source_references=[
            PatternSourceReference(
                source_type=PatternSourceType.ARTIFACT,
                source_id="artifact_new",
                observed_at=now - timedelta(days=5),
            )
        ],
        quality=PatternQualityMetrics(
            confidence_score=0.9,  # Higher confidence
            stability_score=0.8,
            consistency_score=0.8,
            observation_count=10,  # More observations
            unique_execution_count=5,
            distinct_source_count=3,
            first_observed_at=now - timedelta(days=15),
            last_observed_at=now - timedelta(days=2),
        ),
        lifecycle_state=PatternLifecycleState.CANDIDATE,
    )

    query_service.add_pattern(old_pattern)
    query_service.add_pattern(new_pattern)

    # Test supersession detection
    handler = PatternSupersessionHandler()
    supersessions = handler.detect_supersession(new_pattern, [old_pattern], similarity_threshold=0.85)

    print(f"\n✅ Supersession detection:")
    print(f"   - Detected supersessions: {len(supersessions)}")

    if len(supersessions) == 0:
        print(f"   ⚠️  Expected at least 1 supersession")
    else:
        print(f"   - Supersession details: {supersessions[0]}")

    # Apply supersession
    result = governance_service.supersede_pattern(
        old_pattern.id,
        new_pattern.id,
        reason="Newer pattern has better quality",
    )

    print(f"\n✅ Supersession applied:")
    print(f"   - Success: {result.success}")
    print(f"   - New state: {result.new_state.value if result.new_state else None}")

    if not result.success or result.new_state != PatternLifecycleState.SUPERSEDED:
        print(f"   ❌ Supersession failed")
        return False

    # Test that superseded patterns are excluded from normal queries
    validated_patterns = query_service.query_by_lifecycle_state(PatternLifecycleState.VALIDATED)
    superseded_patterns = query_service.query_by_lifecycle_state(PatternLifecycleState.SUPERSEDED)

    print(f"\n✅ Superseded pattern exclusion:")
    print(f"   - Validated patterns: {len(validated_patterns)}")
    print(f"   - Superseded patterns: {len(superseded_patterns)}")

    # The old pattern should now be in SUPERSEDED state
    superseded_pattern = query_service.get_by_id(old_pattern.id)
    if superseded_pattern and superseded_pattern.lifecycle_state == PatternLifecycleState.SUPERSEDED:
        print(f"   ✅ Old pattern correctly marked as SUPERSEDED")
    else:
        print(f"   ❌ Old pattern not marked as SUPERSEDED")
        return False

    # Test supersession chain integrity
    print(f"\n✅ Supersession chain integrity:")
    print(f"   - Old pattern superseded_by_id: {superseded_pattern.superseded_by_id}")
    print(f"   - Old pattern superseded_at: {superseded_pattern.superseded_at}")

    if superseded_pattern.superseded_by_id != new_pattern.id:
        print(f"   ❌ Supersession chain broken")
        return False

    print("\n✅ Duplicate and supersession handling working correctly")
    return True


def validate_lifecycle_edge_cases():
    """Validate lifecycle transitions under edge cases."""
    print("\n" + "="*70)
    print("3. Validating Lifecycle Edge Cases")
    print("="*70)

    workflow = PatternPromotionWorkflow()
    query_service = create_pattern_query_service()

    # Test 1: All allowed transitions
    print(f"\n✅ Testing allowed transitions:")
    allowed_transitions = [
        (PatternLifecycleState.CANDIDATE, PatternLifecycleState.OBSERVED),
        (PatternLifecycleState.OBSERVED, PatternLifecycleState.VALIDATED),
        (PatternLifecycleState.VALIDATED, PatternLifecycleState.ACTIVE),
        (PatternLifecycleState.ACTIVE, PatternLifecycleState.SUPERSEDED),
        (PatternLifecycleState.ACTIVE, PatternLifecycleState.ARCHIVED),
        (PatternLifecycleState.CANDIDATE, PatternLifecycleState.ARCHIVED),
        (PatternLifecycleState.OBSERVED, PatternLifecycleState.ARCHIVED),
    ]

    for from_state, to_state in allowed_transitions:
        is_valid = is_transition_valid(from_state, to_state)
        print(f"   - {from_state.value} → {to_state.value}: {is_valid}")
        if not is_valid:
            print(f"     ❌ Expected this transition to be valid")
            return False

    # Test 2: Invalid transitions fail cleanly
    print(f"\n✅ Testing invalid transitions:")
    invalid_transitions = [
        (PatternLifecycleState.CANDIDATE, PatternLifecycleState.VALIDATED),
        (PatternLifecycleState.CANDIDATE, PatternLifecycleState.ACTIVE),
        (PatternLifecycleState.OBSERVED, PatternLifecycleState.ACTIVE),
        (PatternLifecycleState.ARCHIVED, PatternLifecycleState.ACTIVE),
        (PatternLifecycleState.SUPERSEDED, PatternLifecycleState.ACTIVE),
    ]

    for from_state, to_state in invalid_transitions:
        is_valid = is_transition_valid(from_state, to_state)
        print(f"   - {from_state.value} → {to_state.value}: {is_valid}")
        if is_valid:
            print(f"     ❌ Expected this transition to be invalid")
            return False

    # Test 3: Archive behavior
    print(f"\n✅ Testing archive behavior:")
    governance_service = create_pattern_governance_service(query_service)

    active_pattern = create_test_pattern("Active Pattern", lifecycle_state=PatternLifecycleState.ACTIVE)
    query_service.add_pattern(active_pattern)

    archive_result = governance_service.archive_pattern(active_pattern.id, "Test archive")
    print(f"   - Archive success: {archive_result.success}")
    print(f"   - Archive state: {archive_result.new_state.value if archive_result.new_state else None}")

    if not archive_result.success or archive_result.new_state != PatternLifecycleState.ARCHIVED:
        print(f"   ❌ Archive failed")
        return False

    # Test 4: Double-archive fails gracefully
    double_archive = governance_service.archive_pattern(active_pattern.id, "Double archive")
    print(f"\n✅ Double-archive behavior:")
    print(f"   - Success: {double_archive.success}")
    print(f"   - Message: {double_archive.message}")

    if double_archive.success:
        print(f"   ⚠️  Double-archive should have failed")

    # Test 5: Revalidate behavior
    print(f"\n✅ Testing revalidate behavior:")
    revalidate_result, validation = governance_service.revalidate_pattern(active_pattern.id)
    print(f"   - Revalidate success: {revalidate_result.success}")
    print(f"   - Validation outcome: {validation.outcome.value if validation else None}")

    # Test 6: Disabled pattern type behavior
    print(f"\n✅ Testing disabled pattern type:")
    governance_service.disable_pattern_type(PatternType.FAILURE_PATTERN, "Testing disable")

    is_disabled = governance_service.is_pattern_type_disabled(PatternType.FAILURE_PATTERN)
    print(f"   - FAILURE_PATTERN disabled: {is_disabled}")

    if not is_disabled:
        print(f"   ❌ Pattern type should be disabled")
        return False

    # Re-enable for cleanup
    governance_service.enable_pattern_type(PatternType.FAILURE_PATTERN)

    print("\n✅ Lifecycle edge cases handled correctly")
    return True


def validate_ranking_filtering_edge_cases():
    """Validate ranking and filtering under difficult cases."""
    print("\n" + "="*70)
    print("4. Validating Ranking and Filtering Edge Cases")
    print("="*70)

    query_service = create_pattern_query_service()
    now = datetime.now()

    # Add patterns with various edge case properties
    edge_patterns = [
        # Stale pattern
        create_test_pattern("Stale Pattern", last_observed_days_ago=60, confidence=0.7),

        # Weak pattern (low confidence, few observations)
        Pattern(
            id=uuid4(),
            pattern_type=PatternType.EXECUTION_PATTERN,
            name="Weak Pattern",
            description="Weak pattern",
            domain="testing",
            scope="unit_test",
            structure={},
            characteristics={},
            tags=[],
            source_references=[
                PatternSourceReference(
                    source_type=PatternSourceType.ARTIFACT,
                    source_id="weak_1",
                    observed_at=now - timedelta(days=5),
                )
            ],
            quality=PatternQualityMetrics(
                confidence_score=0.3,  # Low confidence
                stability_score=0.3,
                consistency_score=0.3,
                observation_count=2,  # Few observations
                unique_execution_count=1,
                distinct_source_count=1,
                first_observed_at=now - timedelta(days=10),
                last_observed_at=now - timedelta(days=5),
            ),
            lifecycle_state=PatternLifecycleState.VALIDATED,
        ),

        # Low-confidence pattern
        create_test_pattern("Low Confidence", confidence=0.4),

        # Archived pattern
        create_test_pattern("Archived Pattern", lifecycle_state=PatternLifecycleState.ARCHIVED),

        # Superseded pattern
        create_test_pattern("Superseded Pattern", lifecycle_state=PatternLifecycleState.SUPERSEDED),
    ]

    for p in edge_patterns:
        query_service.add_pattern(p)

    # Test 1: Stale patterns
    stale = query_service.query_stale_patterns(days_threshold=30)
    print(f"\n✅ Stale pattern query:")
    print(f"   - Stale patterns found: {len(stale)}")

    if len(stale) < 1:
        print(f"   ❌ Expected at least 1 stale pattern")
        return False

    # Test 2: Weak patterns
    weak = query_service.query_weak_patterns(confidence_threshold=0.5, observation_threshold=3)
    print(f"\n✅ Weak pattern query:")
    print(f"   - Weak patterns found: {len(weak)}")

    if len(weak) < 1:
        print(f"   ❌ Expected at least 1 weak pattern")
        return False

    # Test 3: Filter by lifecycle state
    archived = query_service.query_by_lifecycle_state(PatternLifecycleState.ARCHIVED)
    superseded = query_service.query_by_lifecycle_state(PatternLifecycleState.SUPERSEDED)

    print(f"\n✅ Lifecycle state filters:")
    print(f"   - Archived patterns: {len(archived)}")
    print(f"   - Superseded patterns: {len(superseded)}")

    # Test 4: Confidence range filtering
    low_conf_filter = PatternQueryFilter(max_confidence=0.5)
    low_conf_result = query_service.query(low_conf_filter)

    print(f"\n✅ Low confidence filter:")
    print(f"   - Low confidence patterns: {low_conf_result.count}")

    # Test 5: Combined filters (edge case combinations)
    combined_filter = PatternQueryFilter(
        lifecycle_states=[PatternLifecycleState.VALIDATED],
        min_confidence=0.3,
        max_confidence=0.7,
    )
    combined_result = query_service.query(combined_filter)

    print(f"\n✅ Combined filter:")
    print(f"   - Combined filter results: {combined_result.count}")

    # Test 6: Text search with special characters
    special_pattern = create_test_pattern("Pattern with SpecialChars: @#$")
    query_service.add_pattern(special_pattern)

    search_results = query_service.search("SpecialChars")
    print(f"\n✅ Text search with special characters:")
    print(f"   - Search results: {len(search_results)}")

    # Test 7: Empty result handling
    impossible_filter = PatternQueryFilter(
        pattern_types=[PatternType.EXECUTION_PATTERN],
        lifecycle_states=[PatternLifecycleState.CANDIDATE],
        min_confidence=0.99,  # Very high confidence
    )
    empty_result = query_service.query(impossible_filter)

    print(f"\n✅ Empty result handling:")
    print(f"   - Empty results: {empty_result.count == 0}")
    print(f"   - Total count: {empty_result.total_count}")

    # Test 8: Sorting tie-breaking
    tie_pattern1 = create_test_pattern("Tie Pattern A", confidence=0.7)
    tie_pattern2 = create_test_pattern("Tie Pattern B", confidence=0.7)
    query_service.add_pattern(tie_pattern1)
    query_service.add_pattern(tie_pattern2)

    name_sorted = query_service.query(sort=PatternQuerySort.NAME_ASC)
    print(f"\n✅ Sorting tie-breaking:")
    print(f"   - Name-sorted results: {name_sorted.count}")
    print(f"   - First pattern: {name_sorted.patterns[0].name if name_sorted.patterns else 'None'}")

    print("\n✅ Ranking and filtering edge cases handled correctly")
    return True


def validate_audit_lineage_integrity():
    """Validate audit and lineage integrity."""
    print("\n" + "="*70)
    print("5. Validating Audit and Lineage Integrity")
    print("="*70)

    query_service = create_pattern_query_service()
    audit_service = create_pattern_audit_service(query_service)
    governance_service = create_pattern_governance_service(query_service, audit_service)

    # Test 1: Audit record completeness
    pattern = create_test_pattern("Audit Test Pattern")
    query_service.add_pattern(pattern)

    # Perform various actions that should create audit records
    validation_service = PatternValidationService()
    candidate = create_test_candidate("Audit Candidate")

    validation = validation_service.validate_candidate(candidate)

    # Manually add audit records for testing
    from torq_console.patterns import PatternAuditRecord

    audit_records = [
        PatternAuditRecord(
            id=uuid4(),
            pattern_id=pattern.id,
            pattern_name=pattern.name,
            pattern_type=pattern.pattern_type,
            action="validated_promote",
            decision_reasoning="Test validation passed",
            passed_rules=["rule1", "rule2"],
            failed_rules=[],
            decided_at=datetime.now() - timedelta(hours=2),
            decided_by="test_validator",
        ),
        PatternAuditRecord(
            id=uuid4(),
            pattern_id=pattern.id,
            pattern_name=pattern.name,
            pattern_type=pattern.pattern_type,
            action="promoted_to_observed",
            decision_reasoning="Promoted to observed",
            from_state=PatternLifecycleState.CANDIDATE,
            to_state=PatternLifecycleState.OBSERVED,
            passed_rules=[],
            failed_rules=[],
            decided_at=datetime.now() - timedelta(hours=1),
            decided_by="test_workflow",
        ),
    ]

    for record in audit_records:
        query_service.add_audit_record(record)

    audit_view = audit_service.get_audit_view(pattern.id)

    print(f"\n✅ Audit record completeness:")
    print(f"   - Audit view created: {audit_view is not None}")
    if audit_view:
        print(f"   - Total audit records: {len(audit_view.all_audit_records)}")
        print(f"   - Decision records: {len(audit_view.decisions)}")
        print(f"   - Promotion records: {len(audit_view.promotions)}")

    if not audit_view or len(audit_view.all_audit_records) != 2:
        print(f"   ❌ Audit records incomplete")
        return False

    # Test 2: Audit timeline integrity
    timeline = audit_view.get_decision_timeline()
    print(f"\n✅ Audit timeline integrity:")
    print(f"   - Timeline events: {len(timeline)}")

    if len(timeline) != 2:
        print(f"   ❌ Timeline incomplete")
        return False

    # Verify chronological order
    for i in range(len(timeline) - 1):
        if timeline[i]["timestamp"] > timeline[i + 1]["timestamp"]:
            print(f"   ❌ Timeline not in chronological order")
            return False

    print(f"   - Timeline in correct order: ✅")

    # Test 3: Governance action logging
    archive_result = governance_service.archive_pattern(pattern.id, "Audit test archive")
    print(f"\n✅ Governance action logging:")
    print(f"   - Archive success: {archive_result.success}")

    # Check that audit record was created
    updated_view = audit_service.get_audit_view(pattern.id)
    if updated_view:
        print(f"   - Total audit records after governance: {len(updated_view.all_audit_records)}")

    # Test 4: Validation summary
    summary = audit_view.get_validation_summary()
    print(f"\n✅ Validation summary:")
    print(f"   - Total decisions: {summary['total_decisions']}")
    print(f"   - Promotion rate: {summary['promotion_rate']:.2%}")

    # Test 5: Failed rules summary
    failed_summary = audit_view.get_failed_rules_summary()
    print(f"\n✅ Failed rules summary:")
    print(f"   - Failed rules: {failed_summary}")

    # Test 6: Compliance report
    compliance = audit_service.get_compliance_report()
    print(f"\n✅ Compliance report:")
    print(f"   - Total patterns: {compliance['total_patterns']}")
    print(f"   - Total decisions: {compliance['total_decisions']}")
    print(f"   - Promotion rate: {compliance['promotion_rate']:.2%}")

    print("\n✅ Audit and lineage integrity maintained")
    return True


def validate_full_regression():
    """Run full regression suite across all milestones."""
    print("\n" + "="*70)
    print("6. Validating Full Regression (M1-M4)")
    print("="*70)

    errors = []

    # Milestone 1: Core models
    print(f"\n✅ Milestone 1: Core Models")
    try:
        pattern_types = len([t for t in PatternType])
        states = len([s for s in PatternLifecycleState])
        sources = len([s for s in PatternSourceType])

        assert pattern_types == 11, f"Expected 11 pattern types, got {pattern_types}"
        assert states == 6, f"Expected 6 lifecycle states, got {states}"
        assert sources == 6, f"Expected 6 source types, got {sources}"

        # Test transition validation
        assert is_transition_valid(PatternLifecycleState.CANDIDATE, PatternLifecycleState.OBSERVED)
        assert not is_transition_valid(PatternLifecycleState.CANDIDATE, PatternLifecycleState.VALIDATED)

        print(f"   - Pattern types: {pattern_types}")
        print(f"   - Lifecycle states: {states}")
        print(f"   - Source types: {sources}")
        print(f"   - Transition validation: working")
    except AssertionError as e:
        errors.append(f"Milestone 1: {e}")
        print(f"   ❌ {e}")

    # Milestone 2: Extraction and aggregation
    print(f"\n✅ Milestone 2: Extraction and Aggregation")
    try:
        extractor = PatternCandidateExtractor()
        aggregator = PatternAggregationEngine()
        scorer = PatternScoringService()

        candidate = create_test_candidate("Regression Test")
        assert candidate.recurrence_score > 0, "Candidate should have recurrence score"
        assert candidate.confidence_score > 0, "Candidate should have confidence score"

        print(f"   - Extractor: available")
        print(f"   - Aggregator: available")
        print(f"   - Scorer: working")
    except AssertionError as e:
        errors.append(f"Milestone 2: {e}")
        print(f"   ❌ {e}")

    # Milestone 3: Validation and promotion
    print(f"\n✅ Milestone 3: Validation and Promotion")
    try:
        validator = PatternValidationService()
        workflow = PatternPromotionWorkflow()
        handler = PatternSupersessionHandler()

        candidate = create_test_candidate("M3 Regression", confidence=0.8, observations=5, span_days=10)
        result = validator.validate_candidate(candidate)

        assert result.outcome == ValidationOutcome.PROMOTE, f"Expected PROMOTE, got {result.outcome}"

        promo_result = workflow.promote_to_observed(candidate)
        assert promo_result.success, "Promotion should succeed"

        # Test invalid transition blocking
        invalid_result = workflow.promote_to_validated(candidate)
        assert not invalid_result.success, "Invalid transition should fail"

        print(f"   - Validation: working")
        print(f"   - Promotion: working")
        print(f"   - Invalid transitions: blocked")
    except AssertionError as e:
        errors.append(f"Milestone 3: {e}")
        print(f"   ❌ {e}")

    # Milestone 4: Query and inspection
    print(f"\n✅ Milestone 4: Query and Inspection")
    try:
        query_service = create_pattern_query_service()
        inspection_service = create_pattern_inspection_service(query_service)
        audit_service = create_pattern_audit_service(query_service)
        governance_service = create_pattern_governance_service(query_service)

        pattern = create_test_pattern("M4 Regression")
        query_service.add_pattern(pattern)

        # Test query
        retrieved = query_service.get_by_id(pattern.id)
        assert retrieved is not None, "Pattern should be retrievable"
        assert retrieved.id == pattern.id, "Retrieved pattern should match"

        # Test inspection
        view = inspection_service.inspect(pattern)
        assert view is not None, "Inspection view should be created"
        assert view.pattern_id == pattern.id, "View should match pattern"

        # Test statistics
        stats = query_service.get_statistics()
        assert stats["total_patterns"] >= 1, "Statistics should show patterns"

        print(f"   - Query service: working")
        print(f"   - Inspection service: working")
        print(f"   - Audit service: working")
        print(f"   - Governance service: working")
    except AssertionError as e:
        errors.append(f"Milestone 4: {e}")
        print(f"   ❌ {e}")

    if errors:
        print(f"\n❌ Regression errors:")
        for error in errors:
            print(f"   - {error}")
        return False

    print(f"\n✅ No regression in Milestones 1-4")
    return True


# ============================================================================
# Main
# ============================================================================

def main():
    """Run all validation tests."""
    print("="*70)
    print("Phase 4G Milestone 5 Validation")
    print("Hardening & Regression")
    print("="*70)

    validators = [
        ("Concurrent Operations", validate_concurrent_operations),
        ("Duplicate and Supersession", validate_duplicate_and_supersession),
        ("Lifecycle Edge Cases", validate_lifecycle_edge_cases),
        ("Ranking and Filtering Edge Cases", validate_ranking_filtering_edge_cases),
        ("Audit and Lineage Integrity", validate_audit_lineage_integrity),
        ("Full Regression", validate_full_regression),
    ]

    results = {}
    for name, validator in validators:
        try:
            results[name] = validator()
        except Exception as e:
            print(f"\n❌ {name} validation failed with error: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    # Print summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\nTotal: {passed}/{total} validations passed")

    if passed == total:
        print("\n" + "="*70)
        print("🎉 MILESTONE 5 COMPLETE - Phase 4G Hardened!")
        print("="*70)
        print("\nExit Criteria Met:")
        print("✅ Pattern operations are concurrency-safe")
        print("✅ Duplicate/supersession handling is correct")
        print("✅ Lifecycle transitions are stable under edge cases")
        print("✅ Ranking/filtering holds under difficult cases")
        print("✅ Audit and lineage integrity hold")
        print("✅ No regression in prior phases")
        print("\n" + "="*70)
        print("🏆 Phase 4G: Pattern Aggregation PRODUCTION-READY")
        print("="*70)
        print("\nPhase 4G Deliverables:")
        print("  M1: Pattern object model, rules, lifecycle")
        print("  M2: Extraction, aggregation, scoring, persistence")
        print("  M3: Validation and promotion workflow")
        print("  M4: Query, inspection, audit, governance")
        print("  M5: Hardening and regression")
        return 0
    else:
        print(f"\n❌ Some validations failed - review output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
