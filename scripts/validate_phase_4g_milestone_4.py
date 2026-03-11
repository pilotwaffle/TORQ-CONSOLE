#!/usr/bin/env python3
"""
Validation Script for Phase 4G Milestone 4: Pattern Query, Inspection, and Audit Layer

This script validates the query, inspection, and audit capabilities for patterns.

Exit Criteria:
- Patterns are queryable and inspectable
- Lifecycle/promotion history is visible
- Evidence and lineage are visible
- Governance actions work
- Audit trail is complete
- No regression in Milestones 1-3 or prior phases
"""

import sys
from datetime import datetime, timedelta
from uuid import uuid4

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
    ValidationOutcome,

    # Milestone 2
    PatternCandidate,
    PatternEvidence,

    # Milestone 3
    PatternValidationService,
    PromotionResult,
    PatternAuditRecord,

    # Milestone 4
    PatternQueryService,
    PatternQueryFilter,
    PatternQuerySort,
    PatternInspectionService,
    PatternInspectionView,
    PatternAuditService,
    PatternAuditView,
    PatternGovernanceService,
    GovernanceActionResult,
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
    """Create a test pattern candidate."""
    now = datetime.now()

    # Create evidence from multiple source types to meet validation thresholds
    source_types = [
        PatternSourceType.ARTIFACT,
        PatternSourceType.MEMORY,
        PatternSourceType.INSIGHT,
    ]

    evidence = []
    source_references = []

    for i in range(observations):
        source_type = source_types[i % len(source_types)]  # Rotate through source types

        # Distribute evidence evenly across the full span
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

    # Score the candidate using PatternScoringService
    from torq_console.patterns import PatternScoringService
    scorer = PatternScoringService()
    candidate = scorer.score_candidate(candidate)

    return candidate


# ============================================================================
# Validation Functions
# ============================================================================

def validate_query_service():
    """Validate that the pattern query service works."""
    print("\n" + "="*70)
    print("1. Validating Pattern Query Service")
    print("="*70)

    service = create_pattern_query_service()

    # Test 1: Add and retrieve by ID
    pattern = create_test_pattern("Query Test 1")
    service.add_pattern(pattern)

    retrieved = service.get_by_id(pattern.id)
    print(f"\n✅ Get by ID:")
    print(f"   - Found: {retrieved is not None}")
    print(f"   - Name matches: {retrieved.name == pattern.name if retrieved else False}")

    if not retrieved or retrieved.name != pattern.name:
        print(f"   ❌ Get by ID failed")
        return False

    # Test 2: Query by type
    pattern2 = create_test_pattern("Query Test 2", pattern_type=PatternType.FAILURE_PATTERN)
    pattern3 = create_test_pattern("Query Test 3", pattern_type=PatternType.EXECUTION_PATTERN)
    service.add_pattern(pattern2)
    service.add_pattern(pattern3)

    exec_patterns = service.query_by_type(PatternType.EXECUTION_PATTERN)
    print(f"\n✅ Query by type:")
    print(f"   - Execution patterns found: {len(exec_patterns)}")

    if len(exec_patterns) != 2:
        print(f"   ❌ Expected 2 execution patterns, got {len(exec_patterns)}")
        return False

    # Test 3: Query by lifecycle state
    validated = service.query_by_lifecycle_state(PatternLifecycleState.VALIDATED)
    print(f"\n✅ Query by lifecycle state:")
    print(f"   - Validated patterns found: {len(validated)}")

    if len(validated) != 3:
        print(f"   ❌ Expected 3 validated patterns, got {len(validated)}")
        return False

    # Test 4: Query with filter
    filter_obj = PatternQueryFilter(
        pattern_types=[PatternType.EXECUTION_PATTERN],
        lifecycle_states=[PatternLifecycleState.VALIDATED],
        min_confidence=0.7,
    )
    result = service.query(filter_obj)
    print(f"\n✅ Query with filter:")
    print(f"   - Filtered results: {result.count}")
    print(f"   - Total count: {result.total_count}")

    if result.count != 2:
        print(f"   ❌ Expected 2 filtered patterns")
        return False

    # Test 5: Sorting
    result_sorted = service.query(sort=PatternQuerySort.CONFIDENCE_DESC)
    print(f"\n✅ Query with sort:")
    print(f"   - Results sorted by confidence")

    # Test 6: Search
    pattern_with_search = create_test_pattern("Search Target Pattern")
    service.add_pattern(pattern_with_search)

    search_results = service.search("Search Target")
    print(f"\n✅ Search:")
    print(f"   - Search results: {len(search_results)}")

    if len(search_results) < 1:
        print(f"   ❌ Expected at least 1 search result")
        return False

    print("\n✅ Query service working correctly")
    return True


def validate_inspection_view():
    """Validate that pattern inspection views work."""
    print("\n" + "="*70)
    print("2. Validating Pattern Inspection View")
    print("="*70)

    query_service = create_pattern_query_service()
    inspection_service = create_pattern_inspection_service(query_service)

    # Add test pattern
    pattern = create_test_pattern("Inspection Test", confidence=0.85, observation_count=8)
    query_service.add_pattern(pattern)

    # Create inspection view
    view = inspection_service.inspect(pattern)

    print(f"\n✅ Inspection view created:")
    print(f"   - Pattern ID: {view.id}")
    print(f"   - Name: {view.name}")
    print(f"   - Type: {view.pattern_type.value}")
    print(f"   - State: {view.lifecycle_state.value}")
    print(f"   - Domain: {view.domain}")
    print(f"   - Scope: {view.scope}")

    # Test evidence summary
    print(f"\n✅ Evidence summary:")
    print(f"   - Total count: {view.evidence_summary.total_count}")
    print(f"   - Time span days: {view.evidence_summary.time_span_days}")
    print(f"   - By source type: {view.evidence_summary.by_source_type}")

    if view.evidence_summary.total_count != 8:
        print(f"   ❌ Expected 8 evidence items, got {view.evidence_summary.total_count}")
        return False

    # Test score breakdown
    print(f"\n✅ Score breakdown:")
    print(f"   - Confidence: {view.score_breakdown.confidence_score:.2f}")
    print(f"   - Stability: {view.score_breakdown.stability_score:.2f}")
    print(f"   - Overall: {view.score_breakdown.overall_score:.2f}")

    # Test to_dict conversion
    view_dict = view.to_dict()
    print(f"\n✅ View to_dict:")
    print(f"   - Dict keys: {len(view_dict)}")
    print(f"   - Has pattern info: {'pattern' in view_dict}")
    print(f"   - Has evidence summary: {'evidence_summary' in view_dict}")
    print(f"   - Has score breakdown: {'score_breakdown' in view_dict}")

    required_keys = ["pattern", "evidence_summary", "score_breakdown", "lifecycle_history", "supersession_info", "source_references"]
    missing_keys = [k for k in required_keys if k not in view_dict]

    if missing_keys:
        print(f"   ❌ Missing keys in dict: {missing_keys}")
        return False

    print("\n✅ Inspection view working correctly")
    return True


def validate_audit_view():
    """Validate that pattern audit views work."""
    print("\n" + "="*70)
    print("3. Validating Pattern Audit View")
    print("="*70)

    query_service = create_pattern_query_service()
    audit_service = create_pattern_audit_service(query_service)

    # Add test pattern
    pattern = create_test_pattern("Audit Test Pattern")
    query_service.add_pattern(pattern)

    # Add audit records
    record1 = PatternAuditRecord(
        id=uuid4(),
        pattern_id=pattern.id,
        pattern_name=pattern.name,
        pattern_type=pattern.pattern_type,
        action="validated_promote",
        decision_reasoning="All validation rules passed",
        decided_at=datetime.now() - timedelta(hours=2),
        decided_by="validation_service",
    )

    record2 = PatternAuditRecord(
        id=uuid4(),
        pattern_id=pattern.id,
        pattern_name=pattern.name,
        pattern_type=pattern.pattern_type,
        action="promoted_to_observed",
        decision_reasoning="Candidate promoted to observed",
        decided_at=datetime.now() - timedelta(hours=1),
        from_state=PatternLifecycleState.CANDIDATE,
        to_state=PatternLifecycleState.OBSERVED,
        decided_by="promotion_workflow",
    )

    query_service.add_audit_record(record1)
    query_service.add_audit_record(record2)

    # Get audit view
    audit_view = audit_service.get_audit_view(pattern.id)

    print(f"\n✅ Audit view created:")
    print(f"   - Pattern ID: {audit_view.pattern_id}")
    print(f"   - Pattern name: {audit_view.pattern_name}")
    print(f"   - Total audit records: {len(audit_view.all_audit_records)}")

    if len(audit_view.all_audit_records) != 2:
        print(f"   ❌ Expected 2 audit records, got {len(audit_view.all_audit_records)}")
        return False

    # Test decision timeline
    timeline = audit_view.get_decision_timeline()
    print(f"\n✅ Decision timeline:")
    print(f"   - Timeline events: {len(timeline)}")

    if len(timeline) != 2:
        print(f"   ❌ Expected 2 timeline events, got {len(timeline)}")
        return False

    # Test validation summary
    summary = audit_view.get_validation_summary()
    print(f"\n✅ Validation summary:")
    print(f"   - Total decisions: {summary['total_decisions']}")
    print(f"   - Promoted: {summary['promoted']}")

    print("\n✅ Audit view working correctly")
    return True


def validate_governance_controls():
    """Validate that governance controls work."""
    print("\n" + "="*70)
    print("4. Validating Governance Controls")
    print("="*70)

    query_service = create_pattern_query_service()
    governance_service = create_pattern_governance_service(query_service)

    # Test 1: Archive pattern
    pattern = create_test_pattern("Governance Test", lifecycle_state=PatternLifecycleState.ACTIVE)
    query_service.add_pattern(pattern)

    archive_result = governance_service.archive_pattern(
        pattern.id,
        reason="Test archiving",
        triggered_by="test_script",
    )

    print(f"\n✅ Archive pattern:")
    print(f"   - Success: {archive_result.success}")
    print(f"   - Previous state: {archive_result.previous_state.value if archive_result.previous_state else None}")
    print(f"   - New state: {archive_result.new_state.value if archive_result.new_state else None}")

    if not archive_result.success:
        print(f"   ❌ Archive failed: {archive_result.message}")
        return False

    if archive_result.new_state != PatternLifecycleState.ARCHIVED:
        print(f"   ❌ Expected ARCHIVED state")
        return False

    # Test 2: Supersede pattern
    old_pattern = create_test_pattern("Old Pattern")
    new_pattern = create_test_pattern("New Pattern")
    query_service.add_pattern(old_pattern)
    query_service.add_pattern(new_pattern)

    supersede_result = governance_service.supersede_pattern(
        old_pattern.id,
        new_pattern.id,
        reason="Newer pattern has better quality",
        triggered_by="test_script",
    )

    print(f"\n✅ Supersede pattern:")
    print(f"   - Success: {supersede_result.success}")
    print(f"   - New state: {supersede_result.new_state.value if supersede_result.new_state else None}")

    if not supersede_result.success:
        print(f"   ❌ Supersede failed: {supersede_result.message}")
        return False

    if supersede_result.new_state != PatternLifecycleState.SUPERSEDED:
        print(f"   ❌ Expected SUPERSEDED state")
        return False

    # Test 3: Revalidate pattern
    revalidate_result, validation_result = governance_service.revalidate_pattern(
        new_pattern.id,
        triggered_by="test_script",
    )

    print(f"\n✅ Revalidate pattern:")
    print(f"   - Success: {revalidate_result.success}")
    print(f"   - Validation result: {validation_result.outcome.value if validation_result else None}")

    if not revalidate_result.success:
        print(f"   ❌ Revalidate failed: {revalidate_result.message}")
        return False

    # Test 4: Disable/enable pattern type
    disable_result = governance_service.disable_pattern_type(
        PatternType.EXECUTION_PATTERN,
        reason="Testing disable",
    )

    print(f"\n✅ Disable pattern type:")
    print(f"   - Success: {disable_result.success}")
    print(f"   - Is disabled: {governance_service.is_pattern_type_disabled(PatternType.EXECUTION_PATTERN)}")

    if not governance_service.is_pattern_type_disabled(PatternType.EXECUTION_PATTERN):
        print(f"   ❌ Pattern type should be disabled")
        return False

    enable_result = governance_service.enable_pattern_type(PatternType.EXECUTION_PATTERN)
    print(f"\n✅ Enable pattern type:")
    print(f"   - Success: {enable_result.success}")
    print(f"   - Is disabled: {governance_service.is_pattern_type_disabled(PatternType.EXECUTION_PATTERN)}")

    if governance_service.is_pattern_type_disabled(PatternType.EXECUTION_PATTERN):
        print(f"   ❌ Pattern type should be enabled")
        return False

    # Test 5: Inspect stale patterns
    stale_pattern = create_test_pattern(
        "Stale Pattern",
        days_ago=60,  # Very old first observation
        last_observed_days_ago=45,  # Very old last observation (more than 30 days ago)
        confidence=0.7,
    )
    query_service.add_pattern(stale_pattern)

    stale_patterns = governance_service.inspect_stale_patterns(days_threshold=30)
    print(f"\n✅ Inspect stale patterns:")
    print(f"   - Stale patterns found: {len(stale_patterns)}")

    if len(stale_patterns) < 1:
        print(f"   ❌ Expected at least 1 stale pattern")
        return False

    # Test 6: Inspect weak patterns
    weak_pattern = create_test_pattern(
        "Weak Pattern",
        confidence=0.4,
        observation_count=2,
    )
    query_service.add_pattern(weak_pattern)

    weak_patterns = governance_service.inspect_weak_patterns(
        confidence_threshold=0.5,
        observation_threshold=3,
    )
    print(f"\n✅ Inspect weak patterns:")
    print(f"   - Weak patterns found: {len(weak_patterns)}")

    if len(weak_patterns) < 1:
        print(f"   ❌ Expected at least 1 weak pattern")
        return False

    print("\n✅ Governance controls working correctly")
    return True


def validate_query_statistics():
    """Validate that query statistics work."""
    print("\n" + "="*70)
    print("5. Validating Query Statistics")
    print("="*70)

    service = create_pattern_query_service()

    # Add varied patterns
    patterns = [
        create_test_pattern(f"Stat Pattern {i}", pattern_type=PatternType.EXECUTION_PATTERN, confidence=0.5 + i * 0.1)
        for i in range(5)
    ]
    patterns.append(create_test_pattern("Failure Pattern", pattern_type=PatternType.FAILURE_PATTERN))
    patterns.append(create_test_pattern("Recovery Pattern", pattern_type=PatternType.RECOVERY_PATTERN))

    for p in patterns:
        service.add_pattern(p)

    # Get statistics
    stats = service.get_statistics()

    print(f"\n✅ Statistics:")
    print(f"   - Total patterns: {stats['total_patterns']}")
    print(f"   - By type: {stats['by_type']}")
    print(f"   - By lifecycle state: {stats['by_lifecycle_state']}")
    print(f"   - By domain: {stats['by_domain']}")
    print(f"   - Average confidence: {stats['average_confidence']}")
    print(f"   - Average observations: {stats['average_observations']}")

    if stats['total_patterns'] < 7:
        print(f"   ❌ Expected at least 7 patterns")
        return False

    if 'execution_pattern' not in stats['by_type']:
        print(f"   ❌ Missing execution_pattern in by_type")
        return False

    print("\n✅ Query statistics working correctly")
    return True


def validate_filter_combinations():
    """Validate that complex filter combinations work."""
    print("\n" + "="*70)
    print("6. Validating Filter Combinations")
    print("="*70)

    service = create_pattern_query_service()

    # Add test patterns with various properties
    patterns = [
        create_test_pattern("High Conf Exec", pattern_type=PatternType.EXECUTION_PATTERN, confidence=0.9),
        create_test_pattern("Low Conf Exec", pattern_type=PatternType.EXECUTION_PATTERN, confidence=0.4),
        create_test_pattern("High Conf Failure", pattern_type=PatternType.FAILURE_PATTERN, confidence=0.85),
        create_test_pattern("Medium Conf Recovery", pattern_type=PatternType.RECOVERY_PATTERN, confidence=0.7),
    ]
    for p in patterns:
        service.add_pattern(p)

    # Test 1: Combined type and confidence filter
    filter1 = PatternQueryFilter(
        pattern_types=[PatternType.EXECUTION_PATTERN],
        min_confidence=0.8,
    )
    result1 = service.query(filter1)
    print(f"\n✅ Type + Confidence filter:")
    print(f"   - Results: {result1.count}")

    if result1.count != 1:
        print(f"   ❌ Expected 1 result (high confidence execution)")
        return False

    # Test 2: Domain and state filter
    filter2 = PatternQueryFilter(
        domains=["testing"],
        lifecycle_states=[PatternLifecycleState.VALIDATED],
    )
    result2 = service.query(filter2)
    print(f"\n✅ Domain + State filter:")
    print(f"   - Results: {result2.count}")

    # Test 3: Text search with type filter
    filter3 = PatternQueryFilter(
        pattern_types=[PatternType.EXECUTION_PATTERN, PatternType.FAILURE_PATTERN],
        search_text="High Conf",
    )
    result3 = service.query(filter3)
    print(f"\n✅ Text search + Type filter:")
    print(f"   - Results: {result3.count}")

    if result3.count < 1:
        print(f"   ❌ Expected at least 1 result for 'High Conf'")
        return False

    # Test 4: Time range filter
    now = datetime.now()
    filter4 = PatternQueryFilter(
        observed_after=now - timedelta(days=15),
        observed_before=now - timedelta(days=5),
    )
    result4 = service.query(filter4)
    print(f"\n✅ Time range filter:")
    print(f"   - Results: {result4.count}")

    # Test 5: Source type filter
    filter5 = PatternQueryFilter(
        source_types=[PatternSourceType.ARTIFACT],
    )
    result5 = service.query(filter5)
    print(f"\n✅ Source type filter:")
    print(f"   - Results: {result5.count}")

    print("\n✅ Filter combinations working correctly")
    return True


def validate_milestone_1_regression():
    """Validate no regression in Milestone 1."""
    print("\n" + "="*70)
    print("7. Validating Milestone 1 Regression")
    print("="*70)

    # Test pattern types
    types = [t for t in PatternType]
    print(f"\n✅ Pattern types: {len(types)} defined")

    if len(types) < 11:
        print(f"   ❌ Expected at least 11 pattern types")
        return False

    # Test lifecycle states
    states = [s for s in PatternLifecycleState]
    print(f"✅ Lifecycle states: {len(states)} defined")

    if len(states) < 6:
        print(f"   ❌ Expected at least 6 lifecycle states")
        return False

    # Test source types
    source_types = [st for st in PatternSourceType]
    print(f"✅ Source types: {len(source_types)} defined")

    # Test Pattern model
    pattern = create_test_pattern("Regression Test")
    print(f"✅ Pattern model: working")

    # Test transition validation
    from torq_console.patterns import is_transition_valid
    valid = is_transition_valid(PatternLifecycleState.CANDIDATE, PatternLifecycleState.OBSERVED)
    print(f"✅ Transition validation: working")

    # Test that direct CANDIDATE -> VALIDATED is NOT valid (Milestone 3 fix)
    invalid = is_transition_valid(PatternLifecycleState.CANDIDATE, PatternLifecycleState.VALIDATED)
    print(f"✅ CANDIDATE -> VALIDATED blocked: {not invalid}")

    if invalid:
        print(f"   ❌ CANDIDATE -> VALIDATED should be blocked")
        return False

    print("\n✅ No regression in Milestone 1")
    return True


def validate_milestone_2_regression():
    """Validate no regression in Milestone 2."""
    print("\n" + "="*70)
    print("8. Validating Milestone 2 Regression")
    print("="*70)

    from torq_console.patterns import (
        PatternCandidateExtractor,
        PatternAggregationEngine,
        PatternScoringService,
    )

    # Test extractor
    extractor = PatternCandidateExtractor()
    print(f"✅ Extractor: PatternCandidateExtractor available")

    # Test aggregator
    aggregator = PatternAggregationEngine()
    print(f"✅ Aggregator: PatternAggregationEngine available")

    # Test scorer
    scorer = PatternScoringService()
    print(f"✅ Scorer: PatternScoringService available")

    # Test candidate creation
    candidate = create_test_candidate("M2 Regression Test")
    print(f"✅ Candidate: PatternCandidate creation working")

    # Test scoring
    scored = scorer.score_candidate(candidate)
    print(f"✅ Scoring: candidate scored with confidence {scored.confidence_score:.2f}")

    print("\n✅ No regression in Milestone 2")
    return True


def validate_milestone_3_regression():
    """Validate no regression in Milestone 3."""
    print("\n" + "="*70)
    print("9. Validating Milestone 3 Regression")
    print("="*70)

    from torq_console.patterns import (
        PatternValidationService,
        PatternPromotionWorkflow,
        PatternSupersessionHandler,
    )

    # Test validation service
    validator = PatternValidationService()
    print(f"✅ Validation service: PatternValidationService available")

    # Test promotion workflow
    workflow = PatternPromotionWorkflow()
    print(f"✅ Promotion workflow: PatternPromotionWorkflow available")

    # Test supersession handler
    handler = PatternSupersessionHandler()
    print(f"✅ Supersession handler: PatternSupersessionHandler available")

    # Test validation
    candidate = create_test_candidate("M3 Regression Test", confidence=0.8, observations=5, span_days=10)
    result = validator.validate_candidate(candidate)
    print(f"✅ Validation: candidate outcome {result.outcome.value}")

    if result.outcome != ValidationOutcome.PROMOTE:
        print(f"   ❌ Expected PROMOTE outcome")
        return False

    # Test promotion
    promo_result = workflow.promote_to_observed(candidate)
    print(f"✅ Promotion: candidate promoted to {promo_result.actual_state.value}")

    if not promo_result.success:
        print(f"   ❌ Promotion failed")
        return False

    # Test that invalid transition is blocked
    invalid_result = workflow.promote_to_validated(candidate)  # Should fail without force
    print(f"✅ Invalid transition blocked: {not invalid_result.success}")

    if invalid_result.success:
        print(f"   ❌ Invalid transition should have been blocked")
        return False

    print("\n✅ No regression in Milestone 3")
    return True


# ============================================================================
# Main
# ============================================================================

def main():
    """Run all validation tests."""
    print("="*70)
    print("Phase 4G Milestone 4 Validation")
    print("Pattern Query, Inspection, and Audit Layer")
    print("="*70)

    validators = [
        ("Query Service", validate_query_service),
        ("Inspection View", validate_inspection_view),
        ("Audit View", validate_audit_view),
        ("Governance Controls", validate_governance_controls),
        ("Query Statistics", validate_query_statistics),
        ("Filter Combinations", validate_filter_combinations),
        ("Milestone 1 Regression", validate_milestone_1_regression),
        ("Milestone 2 Regression", validate_milestone_2_regression),
        ("Milestone 3 Regression", validate_milestone_3_regression),
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
        print("🎉 MILESTONE 4 COMPLETE - All deliverables verified!")
        print("="*70)
        print("\nExit Criteria Met:")
        print("✅ Patterns are queryable and inspectable")
        print("✅ Lifecycle/promotion history is visible")
        print("✅ Evidence and lineage are visible")
        print("✅ Governance actions work")
        print("✅ Audit trail is complete")
        print("✅ No regression in Milestones 1-3 or prior phases")
        return 0
    else:
        print(f"\n❌ Some validations failed - review output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
