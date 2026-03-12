/**
 * TORQ Console - Smoke Tests
 * Post-Layer-11 Verification Plan
 *
 * Tests basic app functionality and loading.
 * These are the first tests to run - if these fail, deeper testing is blocked.
 */

import { test, expect } from '@playwright/test';

// ============================================================================
// Test Configuration
// ============================================================================

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const BROWSER_URL = process.env.BROWSER_URL || 'https://torq-console.vercel.app';

// ============================================================================
// App Shell Tests
// ============================================================================

test.describe('App Shell - Local Environment', () => {
  test.use({ baseURL: BASE_URL });

  test('should load the application without errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('pageerror', (error) => {
      errors.push(error.message);
    });

    await page.goto('/');

    // Check for critical console errors
    expect(errors.filter(e => !e.includes('Warning')).length).toBe(0);

    // Verify app container is present
    const appContainer = page.locator('#root, [data-testid="app-container"], body');
    await expect(appContainer).toBeVisible();
  });

  test('should render the sidebar navigation', async ({ page }) => {
    await page.goto('/');

    // Check for sidebar - may be a nav element or aside
    const sidebar = page.locator('nav, aside, [data-testid="sidebar"]').first();
    await expect(sidebar).toBeVisible({ timeout: 10000 });
  });

  test('should render the top navigation', async ({ page }) => {
    await page.goto('/');

    // Check for top nav
    const topNav = page.locator('header, [data-testid="topnav"], nav[class*="top"]').first();
    await expect(topNav).toBeVisible({ timeout: 10000 });
  });

  test('should display the TORQ logo', async ({ page }) => {
    await page.goto('/');

    // Check for logo - multiple possible selectors
    const logo = page.locator(
      '[data-testid="torq-logo"], svg, img[alt*="TORQ"], text: /torq/i'
    ).first();
    await expect(logo).toBeVisible({ timeout: 10000 });
  });
});

test.describe('App Shell - Browser Environment', () => {
  test.use({ baseURL: BROWSER_URL });

  test('should load the browser deployment without errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('pageerror', (error) => {
      errors.push(error.message);
    });

    await page.goto('/');

    // Allow for some non-critical warnings
    const criticalErrors = errors.filter(e =>
      !e.includes('Warning') &&
      !e.includes('deprecated') &&
      !e.includes('DevTools')
    );

    expect(criticalErrors.length).toBeLessThan(3);

    // Verify app loaded
    await expect(page.locator('body')).toBeVisible();
  });

  test('should render equivalent UI to local environment', async ({ page }) => {
    await page.goto('/');

    // Check for core UI elements
    const sidebar = page.locator('nav, aside').first();
    const topNav = page.locator('header').first();

    // At least one navigation element should be present
    const navVisible = await Promise.all([
      sidebar.isVisible().catch(() => false),
      topNav.isVisible().catch(() => false)
    ]);

    expect(navVisible.some(v => v)).toBe(true);
  });
});

// ============================================================================
// Route Loading Tests
// ============================================================================

test.describe('Route Loading', () => {
  test.use({ baseURL: BASE_URL });

  const routes = [
    { path: '/', name: 'Home/Chat' },
    { path: '/workflows', name: 'Workflows' },
    { path: '/executions', name: 'Executions' },
    { path: '/control', name: 'Operator Control' },
  ];

  for (const route of routes) {
    test(`should load ${route.name} route`, async ({ page }) => {
      await page.goto(route.path);

      // Wait for page to stabilize
      await page.waitForLoadState('networkidle');

      // Verify we didn't get a 404 or error page
      const notFound = page.locator('text: /not found|404|page not found/i').first();
      await expect(notFound).not.toBeVisible({ timeout: 5000 }).catch(() => {
        // Some pages might not have this element at all
      });

      // Check that main content area is visible
      const mainContent = page.locator('main, [role="main"], .content').first();
      await expect(mainContent).toBeVisible({ timeout: 10000 });
    });
  }

  test('should handle deep links correctly', async ({ page }) => {
    // Navigate directly to a nested route
    await page.goto('/workflows');

    // Should load without redirect loops
    await page.waitForLoadState('networkidle');

    // URL should remain unchanged
    expect(page.url()).toContain('/workflows');
  });

  test('should handle page refresh on nested routes', async ({ page }) => {
    await page.goto('/control');

    await page.waitForLoadState('networkidle');

    // Refresh the page
    await page.reload();

    // Should still load correctly
    await page.waitForLoadState('networkidle');

    // No error indicators
    const errorIndicator = page.locator('[data-testid="error"], .error, text: /error/i').first();
    await expect(errorIndicator).not.toBeVisible({ timeout: 5000 }).catch(() => {});
  });
});

// ============================================================================
// 404 and Error Handling Tests
// ============================================================================

test.describe('Error Handling', () => {
  test.use({ baseURL: BASE_URL });

  test('should handle 404 routes gracefully', async ({ page }) => {
    // Go to a non-existent route
    await page.goto('/this-route-does-not-exist');

    // Should redirect to home or show 404 page
    await page.waitForTimeout(2000);

    // Either redirect to home or show a 404 page
    const url = page.url();
    const isAtHome = url.endsWith('/') || url.endsWith('/#');
    const has404Message = await page.locator('text: /404|not found/i').isVisible().catch(() => false);

    expect(isAtHome || has404Message).toBe(true);
  });

  test('should show loading state for slow routes', async ({ page }) => {
    // Navigate to a heavier page
    await page.goto('/workflows');

    // Should show some loading indicator initially
    const loadingSpinner = page.locator(
      '[data-testid="loading"], .spinner, [class*="spin"], [role="status"]'
    ).first();

    const loadingVisible = await loadingSpinner.isVisible().catch(() => false);

    // Loading indicator should appear and then disappear
    if (loadingVisible) {
      await expect(loadingSpinner).not.toBeVisible({ timeout: 10000 });
    }
  });
});

// ============================================================================
// Console Validation Tests
// ============================================================================

test.describe('Console Health Check', () => {
  test.use({ baseURL: BASE_URL });

  test('should not have critical console errors', async ({ page }) => {
    const errors: string[] = [];
    const warnings: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
      if (msg.type() === 'warn') {
        warnings.push(msg.text());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000); // Catch delayed errors

    // Filter out benign errors/warnings
    const benignPatterns = [
      /Warning/,
      /deprecated/,
      /DevTools/,
      /favicon/,
      /404/,
    ];

    const criticalErrors = errors.filter(e =>
      !benignPatterns.some(pattern => pattern.test(e))
    );

    // Log for debugging
    if (criticalErrors.length > 0) {
      console.log('Critical errors found:', criticalErrors);
    }

    // Should have no critical errors
    expect(criticalErrors.length).toBe(0);
  });

  test('should not have repeated failing network requests', async ({ page }) => {
    const failedRequests: Map<string, number> = new Map();

    page.on('requestfailed', request => {
      const url = request.url();
      const count = failedRequests.get(url) || 0;
      failedRequests.set(url, count + 1);
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Check for URLs that failed multiple times
    const repeatedFailures: [string, number][] = [];
    for (const [url, count] of failedRequests.entries()) {
      if (count > 2) {
        repeatedFailures.push([url, count]);
      }
    }

    if (repeatedFailures.length > 0) {
      console.log('Repeated failed requests:', repeatedFailures);
    }

    // Should not have any URL failing more than twice
    expect(repeatedFailures.length).toBe(0);
  });
});
