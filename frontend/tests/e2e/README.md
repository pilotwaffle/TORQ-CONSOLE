# TORQ Console - Post-Layer-11 UI Verification Plan

## Overview

This E2E test suite validates the TORQ Console frontend after Layer 11: Distributed Intelligence Fabric implementation. The tests verify that the UI remains functional, performant, and consistent across local and browser deployments.

## Test Categories

### 1. Smoke Tests (`tests/e2e/smoke/`)

Basic app functionality and loading validation.

- `test_app_shell.spec.ts` - App shell, navigation, console health
- `test_navigation.spec.ts` - Route transitions, deep links, browser history

### 2. Workflow Tests (`tests/e2e/workflows/`)

End-to-end validation of operator workflows.

- `test_mission_portfolio.spec.ts` - Mission list, filtering, refresh
- `test_mission_detail.spec.ts` - Mission graph, event stream, node details

### 3. Distributed Fabric Tests (`tests/e2e/distributed_fabric/`)

Layer 11 specific validation.

- `test_fabric_nodes.spec.ts` - Node list, health, inspection, boundary compliance
- `test_failover_visibility.spec.ts` - Failover status, history, actions

### 4. Regression Tests (`tests/e2e/regression/`)

Comprehensive UI control and error state validation.

- `test_buttons_and_controls.spec.ts` - Buttons, dropdowns, modals, tabs, filters
- `test_error_states.spec.ts` - Loading, empty, error, and network states

## Running Tests

### Local Environment

```bash
cd frontend

# Install Playwright browsers (first time only)
npx playwright install

# Run all tests
npm run test:e2e

# Run specific test suite
npx playwright test tests/e2e/smoke
npx playwright test tests/e2e/workflows
npx playwright test tests/e2e/distributed_fabric
npx playwright test tests/e2e/regression

# Run with UI
npx playwright test --ui

# Run with debug mode
npx playwright test --debug

# Run headed (see browser)
npx playwright test --headed
```

### Browser Deployment Testing

```bash
# Test against deployed version
BROWSER_URL=https://torq-console.vercel.app npx playwright test --project=browser-deployment
```

### Local Dev Server Testing

```bash
# Start dev server in one terminal
npm run dev

# Run tests in another
BASE_URL=http://localhost:5173 npx playwright test
```

## Test Execution Matrix

| Suite | Duration | Priority | Environment |
|-------|----------|----------|-------------|
| Smoke | ~2 min | Critical | Both |
| Workflows | ~5 min | High | Both |
| Distributed Fabric | ~3 min | High | Both |
| Regression | ~8 min | Medium | Local |

## Environment Variables

- `BASE_URL` - Local development URL (default: `http://localhost:5173`)
- `BROWSER_URL` - Browser deployment URL (default: `https://torq-console.vercel.app`)
- `CI` - Set to `1` for CI-specific behavior

## Success Criteria

A test run is considered successful when:

1. **Smoke Tests Pass**: All 100% - App loads and core navigation works
2. **Workflow Tests Pass**: ≥95% - Core operator flows functional
3. **Fabric Tests Pass**: ≥90% - Layer 11 UI visible and working
4. **Regression Tests Pass**: ≥95% - No UI regressions

## Test Results

Results are saved to:

- `playwright-report/` - HTML report with screenshots and traces
- `test-results.json` - Machine-readable results

View HTML report:

```bash
npx playwright show-report
```

## Troubleshooting

### Tests Timing Out

- Increase timeout in `playwright.config.ts`
- Check if local dev server is running
- Verify network connectivity for browser tests

### Flaky Tests

- Run with retries: `npx playwright test --retries=3`
- Check for timing issues with `--debug` mode
- Review traces in HTML report

### Browser Deployment Fails

- Verify `BROWSER_URL` is correct
- Check deployment is accessible
- Review authentication requirements

## CI/CD Integration

Add to CI pipeline:

```yaml
- name: Install Playwright
  run: npx playwright install --with-deps

- name: Run E2E Tests
  run: npm run test:e2e

- name: Upload Test Results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

## Maintenance

When adding new features:

1. Add smoke test coverage for new routes
2. Add workflow test for new operator flows
3. Update regression tests for new UI components
4. Run full suite before merging

## Next Steps

1. Run full test suite locally
2. Fix any failing tests
3. Set up CI/CD integration
4. Establish baseline results
5. Create test execution schedule
