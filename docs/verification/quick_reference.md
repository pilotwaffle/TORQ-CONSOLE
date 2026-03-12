# TORQ Console - System Verification Quick Reference

**Purpose**: Quick execution guide for Post-Layer-11 release gate

---

## Pre-Check (2 min)

```bash
cd frontend

# Check environment
node --version   # Should be v18+
npm --version

# Install dependencies (if needed)
npm install

# Install Playwright browsers (first time only)
npx playwright install
```

---

## Fast Track (15 min)

Run all gates in sequence:

```bash
# 1. Smoke (100% required) - ~2 min
npm run test:e2e:smoke

# 2. Workflows (≥95%) - ~5 min
npm run test:e2e:workflows

# 3. Fabric (≥90%) - ~3 min
npm run test:e2e:fabric

# 4. Regression (≥95%) - ~8 min
npm run test:e2e:regression
```

**STOP IF**: Smoke fails or any gate below threshold

---

## Full Verification (30 min)

```bash
# Run complete test suite
npm run test:e2e

# View HTML report
npm run test:e2e:report
```

---

## Browser Deployment Check (10 min)

```bash
# Test against deployed version
BROWSER_URL=https://your-deployment.vercel.app npm run test:e2e:browser
```

---

## Automated Script

```bash
# Run the full verification script
bash scripts/run_ui_verification.sh
```

---

## Decision Matrix

| Gate | Threshold | Blocker? |
|------|-----------|----------|
| Smoke | 100% | YES |
| Workflows | ≥95% | YES |
| Fabric | ≥90% | YES |
| Regression | ≥95% | YES |
| Boundary | 100% | YES |

---

## If Tests Fail

1. **Check HTML report**: `npm run test:e2e:report`
2. **Review screenshots**: `frontend/test-results/`
3. **Check traces**: `frontend/playwright-report/traces/`
4. **Fix critical issues**
5. **Re-run failed suite**

---

## Common Issues

**Issue**: Tests timeout
```bash
# Fix: Start dev server first
npm run dev
# In another terminal:
npm run test:e2e
```

**Issue**: Browser deployment fails
```bash
# Fix: Verify URL is accessible
curl -I https://your-deployment.vercel.app
```

**Issue**: Flaky tests
```bash
# Fix: Run with retries
npx playwright test --retries=3
```

---

## Success Indicators

✅ All smoke tests pass
✅ Workflow pass rate ≥95%
✅ Fabric pass rate ≥90%
✅ Regression pass rate ≥95%
✅ No boundary violations
✅ Browser parity confirmed

**If all above**: Ready for Layer 12 🚀
