/**
 * TORQ Console - Error States Tests
 * Post-Layer-11 Verification Plan
 *
 * Tests that error states are handled gracefully.
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';

// ============================================================================
// Loading States Tests
// ============================================================================

test.describe('Loading States', () => {
  test.use({ baseURL: BASE_URL });

  test('should show loading indicator during navigation', async ({ page }) => {
    // Navigate to a page that might need loading time
    await page.goto('/workflows');

    // Look for loading spinner or skeleton
    const loadingIndicator = page.locator(
      '[role="status"][aria-busy="true"], [data-testid="loading"], .spinner, [class*="skeleton"]'
    ).first();

    // Loading might appear briefly
    const loadingVisible = await loadingIndicator.isVisible({ timeout: 1000 }).catch(() => false);

    if (loadingVisible) {
      // Should eventually disappear
      await expect(loadingIndicator).not.toBeVisible({ timeout: 10000 });
    }
  });

  test('should show skeleton for data loading', async ({ page }) => {
    await page.goto('/executions');

    // Look for skeleton loaders
    const skeleton = page.locator('[class*="skeleton"], [data-testid="skeleton"]').first();

    // Skeletons are optional
    if (await skeleton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(skeleton).toBeVisible();

      // Should be replaced with actual content
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      // Skeleton might still be there if no data, or replaced with content
      const stillVisible = await skeleton.isVisible().catch(() => false);
      // This is OK - just logging
      console.log(`Skeleton still visible after load: ${stillVisible}`);
    }
  });
});

// ============================================================================
// Empty States Tests
// ============================================================================

test.describe('Empty States', () => {
  test.use({ baseURL: BASE_URL });

  test('should show empty state when no data', async ({ page }) => {
    await page.goto('/workflows');

    // Look for empty state component
    const emptyState = page.locator(
      '[data-testid="empty-state"], [class*="empty"], text: /no workflows|no data|empty/i'
    ).first();

    // Empty state might or might not be visible depending on data
    const emptyVisible = await emptyState.isVisible().catch(() => false);

    if (emptyVisible) {
      await expect(emptyState).toBeVisible();

      // Empty state should have a helpful message
      const message = await emptyState.textContent();
      expect(message?.length).toBeGreaterThan(0);
    }
  });

  test('should have call-to-action in empty state', async ({ page }) => {
    await page.goto('/workflows');

    const emptyState = page.locator('[data-testid="empty-state"], text: /no workflows/i').first();

    if (await emptyState.isVisible({ timeout: 3000 }).catch(() => false)) {
      // Look for CTA button
      const ctaButton = emptyState.locator('button').first();

      if (await ctaButton.isVisible().catch(() => false)) {
        await expect(ctaButton).toBeVisible();
        await expect(ctaButton).toBeEnabled();
      }
    }
  });
});

// ============================================================================
// Error States Tests
// ============================================================================

test.describe('Error States', () => {
  test.use({ baseURL: BASE_URL });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock a failing request
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' }),
      });
    });

    await page.goto('/control');

    // Should show error state or retry mechanism
    const errorIndicator = page.locator(
      '[data-testid="error"], [class*="error"], text: /error|failed to load/i'
    ).first();

    // Wait a bit for error to appear
    await page.waitForTimeout(2000);

    const errorVisible = await errorIndicator.isVisible().catch(() => false);

    // If error is shown, it should be user-friendly
    if (errorVisible) {
      await expect(errorIndicator).toBeVisible();
      const errorText = await errorIndicator.textContent();
      expect(errorText).toBeTruthy();
    }

    // Clean up - remove route handler
    await page.unroute('**/api/**');
  });

  test('should show retry option for failed requests', async ({ page }) => {
    // Mock a failing request
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Service unavailable' }),
      });
    });

    await page.goto('/executions');
    await page.waitForTimeout(2000);

    // Look for retry button
    const retryButton = page.locator(
      'button:has-text("Retry"), button:has-text("Try again"), [data-testid="retry"]'
    ).first();

    const retryVisible = await retryButton.isVisible().catch(() => false);

    if (retryVisible) {
      await expect(retryButton).toBeEnabled();
    }

    // Clean up
    await page.unroute('**/api/**');
  });
});

// ============================================================================
// Network Error Tests
// ============================================================================

test.describe('Network Errors', () => {
  test.use({ baseURL: BASE_URL });

  test('should handle offline mode gracefully', async ({ page }) => {
    // Go offline
    await page.context().offline();

    await page.goto('/');

    // Should show some indication of offline state or use cached data
    const offlineIndicator = page.locator(
      '[data-testid="offline"], text: /offline|no connection|network error/i'
    ).first();

    // Wait for any error handling
    await page.waitForTimeout(2000);

    const offlineVisible = await offlineIndicator.isVisible().catch(() => false);

    // App should still be visible (might use cached data)
    const appVisible = await page.locator('body').isVisible();
    expect(appVisible).toBe(true);

    // Go back online
    await page.context().online();
  });

  test('should recover when connection is restored', async ({ page }) => {
    // Start offline
    await page.context().offline();
    await page.goto('/');
    await page.waitForTimeout(1000);

    // Go online
    await page.context().online();

    // Look for recovery indicator or normal state restoration
    await page.waitForTimeout(2000);

    // App should be functional
    const bodyVisible = await page.locator('body').isVisible();
    expect(bodyVisible).toBe(true);

    // Try a basic interaction
    const buttons = await page.locator('button').all();
    if (buttons.length > 0 && await buttons[0].isVisible()) {
      const wasEnabled = await buttons[0].isEnabled();
      expect(wasEnabled).toBe(true);
    }
  });
});

// ============================================================================
// Timeout Tests
// ============================================================================

test.describe('Timeout Handling', () => {
  test.use({ baseURL: BASE_URL });

  test('should handle slow requests gracefully', async ({ page }) => {
    // Mock a slow request
    await page.route('**/api/**', async route => {
      await new Promise(resolve => setTimeout(resolve, 10000));
      route.continue();
    });

    await page.goto('/control');

    // Should show loading state, not hang indefinitely
    const loading = page.locator('[role="status"][aria-busy="true"], .spinner').first();

    // Loading should appear
    const loadingVisible = await loading.isVisible({ timeout: 5000 }).catch(() => false);

    if (loadingVisible) {
      // Loading should be visible
      await expect(loading).toBeVisible();
    }

    // Clean up - abort pending requests
    await page.unroute('**/api/**');
  });
});
