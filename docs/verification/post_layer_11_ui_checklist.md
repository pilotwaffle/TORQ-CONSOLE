# TORQ Console - Post-Layer-11 UI Verification Checklist

**Milestone**: System Verification - UI and Operator Surface Validation
**Date**: 2025-03-11
**Purpose**: Validate frontend integration after Layer 11 implementation

---

## Pre-Verification Setup

- [ ] Local dev server running (`npm run dev`)
- [ ] Browser deployment accessible
- [ ] Playwright browsers installed (`npx playwright install`)
- [ ] Environment variables configured
- [ ] Backend services running (Layers 1-11)

---

## Phase 1: Smoke Tests (CRITICAL)

### App Shell

- [ ] App loads without critical console errors
- [ ] Sidebar renders correctly
- [ ] Top navigation renders correctly
- [ ] TORQ logo is visible
- [ ] No white-screen crashes

### Navigation

- [ ] Home route (`/`) loads
- [ ] Workflows route (`/workflows`) loads
- [ ] Executions route (`/executions`) loads
- [ ] Control route (`/control`) loads
- [ ] Deep links work correctly
- [ ] Browser back/forward works
- [ ] Page refresh doesn't break state

### Console Health

- [ ] No uncaught runtime exceptions
- [ ] No repeated failing network requests
- [ ] No React hydration errors
- [ ] No broken WebSocket/SSE behavior

---

## Phase 2: Workflow Tests (HIGH PRIORITY)

### Mission Portfolio

- [ ] Mission list renders or empty state shows
- [ ] Refresh button works
- [ ] Filter controls are functional
- [ ] Status badges display correctly
- [ ] Progress indicators render

### Mission Detail

- [ ] Mission detail page loads
- [ ] Mission graph renders
- [ ] Graph controls work (zoom/pan)
- [ ] Event stream section visible
- [ ] Node detail drawer opens on click
- [ ] Drawer close button works
- [ ] Timeline or execution history visible

### Simulation vs Live Data

- [ ] Simulated events clearly labeled
- [ ] Live events clearly labeled
- [ ] Visual distinction between types
- [ ] No simulation data shown as live

---

## Phase 3: Distributed Fabric Tests (HIGH PRIORITY)

### Node List/Status

- [ ] Node list or status cards visible
- [ ] Health indicators displayed
- [ ] Region/tier information shown
- [ ] Node inspection works

### Boundary Compliance

- [ ] Protected state not exposed in federated views
- [ ] Sensitive data redacted (passwords, tokens, _id fields)
- [ ] Artifact redaction status shown
- [ ] Governance tags visible

### Federation Events

- [ ] Federation audit trail visible (if data exists)
- [ ] Event metadata displayed
- [ ] Source tracking visible

### Failover Status

- [ ] System health status shown
- [ ] Degraded/failed nodes indicated
- [ ] Failover history visible (if events exist)
- [ ] Manual failover controls work (if enabled)

---

## Phase 4: Regression Tests (MEDIUM PRIORITY)

### Buttons and Controls

- [ ] All visible buttons are clickable
- [ ] Disabled buttons properly styled
- [ ] Dropdowns open on click
- [ ] Modals open and close
- [ ] Tabs switch correctly
- [ ] Filters apply correctly

### Loading States

- [ ] Loading indicators appear
- [ ] Skeleton screens show where appropriate
- [ ] Loading states resolve

### Empty States

- [ ] Empty state messages shown
- [ ] Call-to-action buttons visible
- [ ] Helpful messaging

### Error States

- [ ] API errors handled gracefully
- [ ] Retry options shown
- [ ] Error messages user-friendly
- [ ] No white-screen errors

---

## Phase 5: Environment Parity (MEDIUM PRIORITY)

### Browser vs Local

- [ ] Same routes available in both
- [ ] Same UI components render
- [ ] Buttons behave consistently
- [ ] API responses handled consistently
- [ ] Empty/loading/error states consistent

---

## Phase 6: End-to-End Workflows

### Workflow 1: Open Mission and Inspect

1. [ ] Load dashboard
2. [ ] Open mission portfolio
3. [ ] Select a mission
4. [ ] Inspect mission details
5. [ ] Open node detail
6. [ ] Review event stream
7. [ ] Return to dashboard

### Workflow 2: Review Readiness

1. [ ] Open readiness panel
2. [ ] Inspect score breakdown
3. [ ] Expand evidence dimensions
4. [ ] Review warnings
5. [ ] Navigate back

### Workflow 3: Strategic Simulation

1. [ ] Open simulation workspace
2. [ ] Create scenario
3. [ ] Run simulation
4. [ ] View forecast
5. [ ] Inspect risk assessment
6. [ ] Verify simulation vs live distinction

### Workflow 4: Inspect Fabric Status

1. [ ] Open distributed fabric view
2. [ ] Inspect nodes
3. [ ] Review node health
4. [ ] View routing event (if exists)
5. [ ] View federation event (if exists)

### Workflow 5: Refresh/Reload

1. [ ] Open nested page
2. [ ] Refresh browser
3. [ ] Reopen app in new tab
4. [ ] Verify state restoration

---

## Success Criteria

**Gate Requirements:**

- ✅ All Smoke Tests pass (100%)
- ✅ Workflow Tests pass (≥95%)
- ✅ Fabric Tests pass (≥90%)
- ✅ Regression Tests pass (≥95%)

**Overall Pass Rate**: ≥95%

---

## Test Execution Results

| Suite | Tests | Passed | Failed | Pass Rate |
|-------|-------|--------|--------|-----------|
| Smoke | ___ | ___ | ___ | ___% |
| Workflows | ___ | ___ | ___ | ___% |
| Fabric | ___ | ___ | ___ | ___% |
| Regression | ___ | ___ | ___ | ___% |
| **TOTAL** | ___ | ___ | ___ | ___% |

---

## Issues Found

| ID | Description | Severity | Status | Fixed By |
|----|-------------|----------|--------|---------|
| | | | | |

---

## Approval

**Tested By**: ________________
**Date**: ________________
**Approved**: [ ] Yes [ ] No
**Notes**: ________________

---

**Next Steps**:
- If all gates pass: Proceed to Layer 12 planning
- If gates fail: Fix critical issues before proceeding
- Document all non-blocking issues for backlog
