"""
Phase 4H.1 Milestone 1 Validation Tests

Tests for memory eligibility rules and validation schema.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from datetime import datetime, timedelta
from uuid import uuid4

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test imports
try:
    from torq_console.memory.memory_models import (
        MemoryType,
        ConfidenceLevel,
        MemoryStatus,
        ValidationDecision,
        RejectionReason,
        MemoryProvenance,
        MemoryMetadata,
        MemoryContent,
        MemoryCandidate,
        EligibilityRule,
        EligibilityRuleset,
        DEFAULT_ELIGIBILITY_RULESET,
        get_freshness_window,
        confidence_to_level,
        level_to_min_score,
    )
    from torq_console.memory.eligibility_rules import (
        EligibilityEngine,
        ConflictDetector,
        get_eligibility_engine,
        get_conflict_detector,
        ELIGIBLE_ARTIFACT_TYPES,
        INELIGIBLE_ARTIFACT_TYPES,
        CONFIDENCE_REQUIREMENTS,
        COMPLETENESS_REQUIREMENTS,
        REQUIRED_FIELDS,
    )
    IMPORTS_OK = True
except Exception as e:
    logger.error(f"Import failed: {e}")
    IMPORTS_OK = False


def make_provenance(
    artifact_type: str = "code_execution",
    days_ago: int = 0,
) -> MemoryProvenance:
    """Create a test provenance object."""
    created_at = datetime.now() - timedelta(days=days_ago)
    return MemoryProvenance(
        artifact_id=uuid4(),
        artifact_type=artifact_type,
        workspace_id=uuid4(),
        mission_id=uuid4(),
        node_id=uuid4(),
        execution_id="exec_123",
        team_execution_id=uuid4(),
        role_name="researcher",
        round_number=1,
        tool_name="test_tool",
        artifact_created_at=created_at,
    )


def make_content(
    title: str = "Test Memory",
    summary: str = "Test summary",
    **kwargs,
) -> MemoryContent:
    """Create a test content object."""
    return MemoryContent(
        title=title,
        summary=summary,
        content_json=kwargs,
        content_text=f"{title}: {summary}",
        tags=["test"],
    )


def make_candidate(
    artifact_type: str = "code_execution",
    confidence: float = 0.8,
    completeness: float = 0.8,
    memory_type: MemoryType = MemoryType.KNOWLEDGE,
    days_ago: int = 0,
    **content_kwargs,
) -> MemoryCandidate:
    """Create a test memory candidate."""
    return MemoryCandidate(
        artifact_id=uuid4(),
        artifact_type=artifact_type,
        content=make_content(**content_kwargs),
        provenance=make_provenance(artifact_type, days_ago),
        confidence_score=confidence,
        completeness_score=completeness,
        proposed_memory_type=memory_type,
    )


async def test_01_imports() -> None:
    """Test that all Milestone 1 components can be imported."""
    print("\n[1] Testing imports...")

    assert IMPORTS_OK, "Failed to import memory models"

    # Check key classes are available
    assert MemoryCandidate is not None
    assert EligibilityEngine is not None
    assert ConflictDetector is not None
    assert DEFAULT_ELIGIBILITY_RULESET is not None

    # Check enums
    assert MemoryType.KNOWLEDGE == "knowledge"
    assert ConfidenceLevel.VERIFIED == "verified"
    assert ValidationDecision.ACCEPT == "accept"
    assert RejectionReason.LOW_CONFIDENCE == "low_confidence"

    print("  [OK] All imports successful")


async def test_02_memory_candidate_model() -> None:
    """Test MemoryCandidate model creation and validation."""
    print("\n[2] Testing MemoryCandidate model...")

    candidate = make_candidate(
        title="Test Pattern",
        summary="A useful pattern",
        confidence=0.85,
        completeness=0.9,
    )

    # Basic properties
    assert candidate.artifact_id is not None
    assert candidate.artifact_type == "code_execution"
    assert candidate.confidence_score == 0.85
    assert candidate.completeness_score == 0.9

    # Confidence level
    assert candidate.confidence_level == ConfidenceLevel.HIGH

    # Eligibility check
    assert candidate.is_eligible, "Candidate should be eligible"

    print("  [OK] MemoryCandidate model works correctly")


async def test_03_confidence_levels() -> None:
    """Test confidence score to level mapping."""
    print("\n[3] Testing confidence levels...")

    test_cases = [
        (0.95, ConfidenceLevel.VERIFIED),
        (0.9, ConfidenceLevel.VERIFIED),
        (0.75, ConfidenceLevel.HIGH),
        (0.7, ConfidenceLevel.HIGH),
        (0.55, ConfidenceLevel.MEDIUM),
        (0.5, ConfidenceLevel.MEDIUM),
        (0.3, ConfidenceLevel.LOW),
        (0.0, ConfidenceLevel.LOW),
    ]

    for score, expected_level in test_cases:
        candidate = make_candidate(confidence=score)
        actual_level = candidate.confidence_level
        assert actual_level == expected_level, f"Score {score} -> {actual_level}, expected {expected_level}"

    print("  [OK] Confidence level mapping correct")


async def test_04_eligibility_by_confidence() -> None:
    """Test that low confidence candidates are rejected."""
    print("\n[4] Testing eligibility by confidence...")

    engine = get_eligibility_engine()

    # High confidence - should accept
    high_candidate = make_candidate(confidence=0.85, memory_type=MemoryType.KNOWLEDGE)
    decision, reason, msg = engine.check_candidate(high_candidate)
    assert decision == ValidationDecision.ACCEPT, f"High confidence should accept, got {decision}: {msg}"
    print(f"  [OK] High confidence (0.85) accepted: {msg}")

    # Low confidence - should reject
    low_candidate = make_candidate(confidence=0.4, memory_type=MemoryType.KNOWLEDGE)
    decision, reason, msg = engine.check_candidate(low_candidate)
    assert decision == ValidationDecision.REJECT, f"Low confidence should reject, got {decision}: {msg}"
    assert reason == RejectionReason.LOW_CONFIDENCE
    print(f"  [OK] Low confidence (0.4) rejected: {msg}")


async def test_05_eligibility_by_completeness() -> None:
    """Test that incomplete candidates are rejected."""
    print("\n[5] Testing eligibility by completeness...")

    engine = get_eligibility_engine()

    # Decision type requires high completeness
    decision_content = MemoryContent(
        title="Decision",
        summary="Use API X",
        content_json={"rationale": "Because it's good", "decision_point": "Use API X"},
    )
    decision_candidate = MemoryCandidate(
        artifact_id=uuid4(),
        artifact_type="decision",
        content=decision_content,
        provenance=make_provenance("decision"),
        confidence_score=0.8,
        completeness_score=0.9,  # Meets 0.8 threshold
        proposed_memory_type=MemoryType.DECISION,
    )
    decision, reason, msg = engine.check_candidate(decision_candidate)
    assert decision == ValidationDecision.ACCEPT, f"Complete decision should accept, got {decision}: {msg}"
    print(f"  [OK] Complete decision (0.9) accepted: {msg}")

    # Incomplete decision - should reject
    incomplete_decision = MemoryCandidate(
        artifact_id=uuid4(),
        artifact_type="decision",
        content=MemoryContent(title="Decision", summary="Incomplete decision"),
        provenance=make_provenance("decision"),
        confidence_score=0.8,
        completeness_score=0.5,  # Below 0.8 threshold
        proposed_memory_type=MemoryType.DECISION,
    )
    decision, reason, msg = engine.check_candidate(incomplete_decision)
    assert decision == ValidationDecision.REJECT, f"Incomplete decision should reject, got {decision}: {msg}"
    assert reason == RejectionReason.INCOMPLETE
    print(f"  [OK] Incomplete decision (0.5) rejected: {msg}")


async def test_06_required_fields_validation() -> None:
    """Test that required fields are validated."""
    print("\n[6] Testing required fields validation...")

    engine = get_eligibility_engine()

    # API knowledge requires endpoint, method, parameters
    api_content = MemoryContent(
        title="API",
        summary="Users API",
        content_json={"endpoint": "/api/users", "method": "GET", "parameters": "user_id"},
    )
    api_candidate_with_fields = MemoryCandidate(
        artifact_id=uuid4(),
        artifact_type="api_call",
        content=api_content,
        provenance=make_provenance("api_call"),
        confidence_score=0.85,
        completeness_score=0.9,
        proposed_memory_type=MemoryType.API_KNOWLEDGE,
    )
    decision, reason, msg = engine.check_candidate(api_candidate_with_fields)
    assert decision == ValidationDecision.ACCEPT, f"API with required fields should accept, got {decision}: {msg}"
    print(f"  [OK] API with required fields accepted: {msg}")

    # API knowledge missing required fields
    api_content_missing = MemoryContent(
        title="API",
        summary="Users API",
        content_json={"endpoint": "/api/users"},  # Missing method, parameters
    )
    api_candidate_missing = MemoryCandidate(
        artifact_id=uuid4(),
        artifact_type="api_call",
        content=api_content_missing,
        provenance=make_provenance("api_call"),
        confidence_score=0.85,
        completeness_score=0.9,
        proposed_memory_type=MemoryType.API_KNOWLEDGE,
    )
    decision, reason, msg = engine.check_candidate(api_candidate_missing)
    assert decision == ValidationDecision.REJECT, f"API missing fields should reject, got {decision}: {msg}"
    assert reason == RejectionReason.MISSING_FIELDS
    assert "Missing required fields" in msg
    print(f"  [OK] API missing required fields rejected: {msg}")


async def test_07_freshness_validation() -> None:
    """Test that stale artifacts are rejected."""
    print("\n[7] Testing freshness validation...")

    engine = get_eligibility_engine()

    # API knowledge stales after 7 days
    fresh_api_content = MemoryContent(
        title="API",
        summary="Test API",
        content_json={"endpoint": "/api/test", "method": "GET", "parameters": "user_id"},
    )
    fresh_api = MemoryCandidate(
        artifact_id=uuid4(),
        artifact_type="api_call",
        content=fresh_api_content,
        provenance=make_provenance("api_call", days_ago=3),  # Fresh
        confidence_score=0.9,
        completeness_score=0.9,
        proposed_memory_type=MemoryType.API_KNOWLEDGE,
    )
    decision, reason, msg = engine.check_candidate(fresh_api)
    assert decision == ValidationDecision.ACCEPT, f"Fresh API should accept, got {decision}: {msg}"
    print(f"  [OK] Fresh API (3 days old) accepted: {msg}")

    # Stale API
    stale_api_content = MemoryContent(
        title="API",
        summary="Test API",
        content_json={"endpoint": "/api/test", "method": "GET", "parameters": "user_id"},
    )
    stale_api = MemoryCandidate(
        artifact_id=uuid4(),
        artifact_type="api_call",
        content=stale_api_content,
        provenance=make_provenance("api_call", days_ago=14),  # Stale (over 7 day window)
        confidence_score=0.9,
        completeness_score=0.9,
        proposed_memory_type=MemoryType.API_KNOWLEDGE,
    )
    decision, reason, msg = engine.check_candidate(stale_api)
    assert decision == ValidationDecision.REJECT, f"Stale API should reject, got {decision}: {msg}"
    assert reason == RejectionReason.STALE_SOURCE
    print(f"  [OK] Stale API (14 days old) rejected: {msg}")


async def test_08_artifact_type_filtering() -> None:
    """Test that ineligible artifact types are rejected."""
    print("\n[8] Testing artifact type filtering...")

    engine = get_eligibility_engine()

    # Raw output is ineligible
    raw_output = make_candidate(
        artifact_type="raw_output",
        confidence=0.9,
    )
    decision, reason, msg = engine.check_candidate(raw_output)
    assert decision == ValidationDecision.REJECT, f"Raw output should reject, got {decision}: {msg}"
    assert reason == RejectionReason.INVALID_SOURCE_TYPE
    print(f"  [OK] Raw output rejected: {msg}")

    # Debug output is ineligible
    debug_output = make_candidate(
        artifact_type="debug_output",
        confidence=0.9,
    )
    decision, reason, msg = engine.check_candidate(debug_output)
    assert decision == ValidationDecision.REJECT, f"Debug output should reject, got {decision}: {msg}"
    assert reason == RejectionReason.INVALID_SOURCE_TYPE
    print(f"  [OK] Debug output rejected: {msg}")

    # Code execution is eligible
    code_exec = make_candidate(
        artifact_type="code_execution",
        confidence=0.8,
    )
    decision, reason, msg = engine.check_candidate(code_exec)
    assert decision == ValidationDecision.ACCEPT, f"Code execution should accept, got {decision}: {msg}"
    print(f"  [OK] Code execution accepted: {msg}")


async def test_09_provenance_validation() -> None:
    """Test that candidates without provenance are rejected."""
    print("\n[9] Testing provenance validation...")

    engine = get_eligibility_engine()

    # Candidate without artifact_id
    candidate = make_candidate()
    candidate.provenance.artifact_id = None

    decision, reason, msg = engine.check_candidate(candidate)
    assert decision == ValidationDecision.REJECT, f"No artifact_id should reject, got {decision}: {msg}"
    assert reason == RejectionReason.NO_PROVENANCE
    print(f"  [OK] Candidate without artifact_id rejected: {msg}")

    # Candidate without workspace_id
    candidate = make_candidate()
    candidate.provenance.workspace_id = None

    decision, reason, msg = engine.check_candidate(candidate)
    assert decision == ValidationDecision.REJECT, f"No workspace_id should reject, got {decision}: {msg}"
    assert reason == RejectionReason.NO_PROVENANCE
    print(f"  [OK] Candidate without workspace_id rejected: {msg}")


async def test_10_freshness_window_by_type() -> None:
    """Test freshness windows for different memory types."""
    print("\n[10] Testing freshness windows by type...")

    test_cases = [
        (MemoryType.API_KNOWLEDGE, 7),
        (MemoryType.TEAM_INSIGHT, 14),
        (MemoryType.CODE_PATTERN, 30),
        (MemoryType.ARCHITECTURE_DECISION, 90),
    ]

    for memory_type, expected_days in test_cases:
        actual_days = get_freshness_window(memory_type)
        assert actual_days == expected_days, f"{memory_type} should have {expected_days} day window, got {actual_days}"
        print(f"  [OK] {memory_type.value}: {actual_days} day freshness window")


async def test_11_confidence_thresholds() -> None:
    """Test confidence thresholds for different memory types."""
    print("\n[11] Testing confidence thresholds...")

    expected = {
        MemoryType.KNOWLEDGE: 0.7,
        MemoryType.PATTERN: 0.75,
        MemoryType.DECISION: 0.7,
        MemoryType.CODE_PATTERN: 0.8,
        MemoryType.API_KNOWLEDGE: 0.8,
    }

    for memory_type, expected_threshold in expected.items():
        actual_threshold = CONFIDENCE_REQUIREMENTS.get(memory_type)
        assert actual_threshold == expected_threshold, f"{memory_type} threshold should be {expected_threshold}, got {actual_threshold}"
        print(f"  [OK] {memory_type.value}: {actual_threshold} confidence threshold")


async def test_12_eligibility_ruleset() -> None:
    """Test that the default eligibility ruleset is properly configured."""
    print("\n[12] Testing default eligibility ruleset...")

    ruleset = DEFAULT_ELIGIBILITY_RULESET

    assert ruleset.name == "default"
    assert ruleset.default_min_confidence == 0.7
    assert ruleset.default_min_completeness == 0.6
    assert len(ruleset.rules) > 0, "Ruleset should have rules"

    # Check specific rules exist
    rule_names = [r.rule_name for r in ruleset.rules]
    assert "verified_knowledge" in rule_names
    assert "web_search_knowledge" in rule_names
    assert "decision_memory" in rule_names
    assert "api_knowledge" in rule_names

    print(f"  [OK] Default ruleset has {len(ruleset.rules)} rules")
    print(f"  [OK] Rules: {', '.join(rule_names)}")


async def test_13_conflict_detector() -> None:
    """Test conflict detection between candidates and existing memory."""
    print("\n[13] Testing conflict detector...")

    detector = get_conflict_detector()

    # Create two candidates with contradictory content
    candidate1 = MemoryCandidate(
        artifact_id=uuid4(),
        artifact_type="decision",
        content=MemoryContent(
            title="API Choice",
            summary="We should use API X",
            content_text="We should use API X for this project",
        ),
        provenance=make_provenance("decision", days_ago=10),
        confidence_score=0.8,
        completeness_score=0.8,
        proposed_memory_type=MemoryType.DECISION,
    )

    candidate2 = MemoryCandidate(
        artifact_id=uuid4(),
        artifact_type="decision",
        content=MemoryContent(
            title="API Choice",
            summary="We should not use API X",
            content_text="We should not use API X for this project",
        ),
        provenance=make_provenance("decision", days_ago=5),
        confidence_score=0.8,
        completeness_score=0.8,
        proposed_memory_type=MemoryType.DECISION,
    )

    # Test contradiction detection - "should use" vs "should not use"
    has_conflict = detector._is_contradictory(candidate1, candidate2)
    assert has_conflict, "Contradictory statements should be detected as conflict"
    print(f"  [OK] Contradictory statements detected as conflict")

    # Test supersession detection - same title, different dates
    newer = MemoryCandidate(
        artifact_id=uuid4(),
        artifact_type="decision",
        content=MemoryContent(
            title="API Choice",
            summary="Use API X",
            content_text="Use API X",
        ),
        provenance=make_provenance("decision", days_ago=0),  # Newer
        confidence_score=0.8,
        completeness_score=0.8,
        proposed_memory_type=MemoryType.DECISION,
    )

    older = MemoryCandidate(
        artifact_id=uuid4(),
        artifact_type="decision",
        content=MemoryContent(
            title="API Choice",
            summary="Use API X",
            content_text="Use API X",
        ),
        provenance=make_provenance("decision", days_ago=10),  # Older
        confidence_score=0.8,
        completeness_score=0.8,
        proposed_memory_type=MemoryType.DECISION,
    )

    is_superseding = detector._is_superseding(newer, older)
    assert is_superseding, "Same title with newer date should be detected as superseding"
    print(f"  [OK] Newer version detected as superseding")


async def test_14_rejection_stats() -> None:
    """Test that rejection reasons are tracked."""
    print("\n[14] Testing rejection statistics...")

    engine = get_eligibility_engine()

    # Reset stats
    engine.reset_stats()
    assert len(engine.get_rejection_stats()) == 0, "Stats should be empty after reset"

    # Generate some rejections
    low_conf = make_candidate(confidence=0.3)
    engine.check_candidate(low_conf)

    raw = make_candidate(artifact_type="raw_output", confidence=0.9)
    engine.check_candidate(raw)

    debug = make_candidate(artifact_type="debug_output", confidence=0.9)
    engine.check_candidate(debug)

    stats = engine.get_rejection_stats()
    assert len(stats) > 0, "Should have rejection stats"
    print(f"  [OK] Rejection stats: {stats}")


# ============================================================================
# Test Runner
# ============================================================================

async def run_all_tests() -> None:
    """Run all Milestone 1 validation tests."""
    print("\n" + "=" * 60)
    print("Phase 4H.1 Milestone 1: Memory Eligibility Rules")
    print("=" * 60)

    tests = [
        test_01_imports,
        test_02_memory_candidate_model,
        test_03_confidence_levels,
        test_04_eligibility_by_confidence,
        test_05_eligibility_by_completeness,
        test_06_required_fields_validation,
        test_07_freshness_validation,
        test_08_artifact_type_filtering,
        test_09_provenance_validation,
        test_10_freshness_window_by_type,
        test_11_confidence_thresholds,
        test_12_eligibility_ruleset,
        test_13_conflict_detector,
        test_14_rejection_stats,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            await test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"  [FAIL] {e}")
        except Exception as e:
            failed += 1
            print(f"  [ERROR] {e}")

    print("\n" + "=" * 60)
    print(f"Milestone 1 Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n[SUCCESS] Phase 4H.1 Milestone 1: VALIDATED")
        print("\nMemory eligibility rules and validation schema are working:")
        print("  - Memory candidate models validated")
        print("  - Eligibility rules enforced correctly")
        print("  - Confidence thresholds applied")
        print("  - Completeness checks working")
        print("  - Required fields validated")
        print("  - Freshness rules applied")
        print("  - Artifact type filtering working")
        print("  - Provenance validation working")
        print("  - Conflict detection functional")
        print("  - Rejection tracking operational")
    else:
        print("\n[FAILURE] Some tests failed - review above output")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
