# Agent 1 - Prioritization Engine Bug Fix

**Date:** 2026-03-14
**Found By:** Agent 2 (Validation Operator)
**Severity:** CRITICAL - Blocking validation

---

## Bug Report

### Issue
`BudgetAwarePrioritization.rank_by_efficiency()` filters out ineligible proposals before returning them to the allocation engine. This causes `rejected_mission_ids` to always be empty.

### Location
**File:** `torq_console/layer13/economic/budget_aware_prioritization.py`
**Method:** `rank_by_efficiency()`
**Lines:** 83-92

### Current Code (BROKEN)
```python
# Filter to only eligible proposals and sort by efficiency
eligible_proposals = [s for s in scored_proposals if s.eligible]
ranked_proposals = sorted(
    eligible_proposals,
    key=lambda s: (
        s.efficiency,
        s.quality_adjusted_value,
    ),
    reverse=True,
)

return ranked_proposals
```

### Fix Required
```python
# Sort all proposals, with eligible ones first
ranked_proposals = sorted(
    scored_proposals,
    key=lambda s: (
        s.eligible,  # Eligible proposals first (True > False)
        s.efficiency if s.eligible else 0.0,  # Then by efficiency
        s.quality_adjusted_value,
    ),
    reverse=True,
)

return ranked_proposals
```

### Why This Is The Fix

1. **Preserve all proposals** - Don't filter out ineligible ones
2. **Sort eligible first** - Uses `s.eligible` as primary sort key (True > False)
3. **Maintain efficiency ordering** - Eligible proposals still sorted by efficiency
4. **Allow allocation to handle rejection** - Layer 5 needs to see ineligible proposals to populate `rejected_mission_ids`

---

## Verification

### Before Fix
```python
# INTO prioritization:
risky_bet: eligible=False
safe_bet: eligible=True

# OUT OF prioritization:
safe_bet: eligible=True
# risky_bet is LOST

# Allocation result:
Rejected: []  # WRONG
```

### After Fix (Expected)
```python
# INTO prioritization:
risky_bet: eligible=False
safe_bet: eligible=True

# OUT OF prioritization:
safe_bet: eligible=True, efficiency=0.0039  # First (eligible)
risky_bet: eligible=False, efficiency=0.0   # Second (ineligible)

# Allocation result:
Rejected: ['risky_bet']  # CORRECT
```

---

## Test Case

Run this to verify the fix:
```bash
python -m torq_console.layer13.economic.run_validation --scenarios low_confidence_rejection --verbose
```

**Expected Output After Fix:**
```
[PASS] low_confidence_rejection: Low-confidence high-cost proposals are rejected
  [PASS] Rejected Missions Match
    Expected: {'risky_bet'}
    Actual: {'risky_bet'}
```

---

## Impact

### Scenarios Affected
- `low_confidence_rejection` - Currently failing on rejected missions check

### Scenarios That Will Pass After Fix
- `low_confidence_rejection` should pass (6/7 tests already passing)

### Other Issues (Separate)
- Regret ratio expectations still need adjustment (0.15 → 0.60)
- Some mission selections may need review

---

## Additional Notes

The feasibility gate in `economic_evaluation_engine.py` is working correctly. The bug is purely in how ineligible proposals are handled during prioritization.

This fix ensures that proposals rejected at Layer 1 (feasibility gate) are properly tracked through to Layer 5 (allocation) where they are categorized as rejected.

---

**Status:** ⏸️ AWAITING FIX
**Priority:** CRITICAL
**Estimated Effort:** 5 minutes (simple code change)
