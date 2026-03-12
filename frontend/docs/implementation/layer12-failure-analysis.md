# Layer 12 Test Failure Analysis

**Date**: 2026-03-12
**Tests**: 90/150 passing (60%)

## Failure Buckets

### Bucket A - Contract/Shape Mismatches (Priority 1)
**ContradictionAndPluralityManager**: 
- Missing `clusterByTopic` method
- `getPluralityView` returns undefined for `hasConsensus`, `preservesPlurality`
- `checkMonocultureRisk` returns undefined for `atRisk`, `diversityScore`

**Root Cause**: Tests expect methods that weren't implemented
**Fix**: Add missing public methods to service

### Bucket C - Repository/Mock Assumptions (Priority 2)
**FederatedClaimRegistry**:
- Tests call `findRelevantClaims` but implementation may differ
- `getStatistics` returns undefined for breakdown properties

### Bucket B - Scoring/Trust Logic (Priority 3)
**LocalQualificationEngine**:
- 6 failures related to threshold values
- Trust computation produces 0.67-0.77 when test expects >0.8

### Bucket D - Async/Timing Issues (Priority 4)
**ContradictionAndPlurandPluralityManager**:
- Tests call async methods without `await`
- Need to add `async` to test functions

## Test-by-Test Priority

### Critical Path (Claim Lifecycle)
1. publish → qualify → adopt → audit

**Status**: Repository tests 17/17 passing, indicating core lifecycle works.

### Recommended Fix Order
1. Add `await` to ContradictionAndPluralityManager tests
2. Add `clusterByTopic` method
3. Fix `getPluralityView` return values
4. Fix `checkMonocultureRisk` return values
5. Adjust trust/scoring thresholds
6. Add missing FederatedClaimRegistry methods

## Quick Wins

The following changes would fix ~20 tests immediately:
- Add `await` to all async method calls in tests
- Add placeholder `clusterByTopic` method
- Initialize all return objects with default values
