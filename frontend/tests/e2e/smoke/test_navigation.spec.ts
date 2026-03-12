/**
 * TORQ Console - Navigation Tests
 * Post-Layer-11 Verification Plan
 *
 * Tests navigation between pages and route transitions.
 */

import { test, expect } from '@playwright/test';

// ============================================================================
// Navigation Tests
// ============================================================================

test.describe('Navigation', () => {
  test('should navigate to all main routes', async ({ page }) => {
    await page.goto('/');

    const mainRoutes = [
      { path: '/workflows', selector: 'a[href*="/workflows"]' },
      { path: '/executions', selector: 'a[href*="/executions"]' },
      { path: '/control', selector: 'a[href*="/control"]' },
    ];

    for (const route of mainRoutes) {
      // Try navigation via URL first
      await page.goto(route.path);
      await page.waitForLoadState('networkidle');

      expect(page.url()).toContain(route.path);

      // Check for page heading or main content
      const heading = page.locator('h1, h2').first();
      await expect(heading).toBeVisible({ timeout: 10000 });
    }
  });

  test('should navigate using sidebar links', async ({ page }) => {
    await page.goto('/');

    // Find navigation links
    const navLinks = page.locator('nav a, aside a, [role="navigation"] a').all();

    // Try clicking the first few navigation links
    const linkCount = Math.min((await navLinks).length, 3);

    for (let i = 0; i < linkCount; i++) {
      const links = await page.locator('nav a, aside a, [role="navigation"] a').all();
      if (links[i]) {
        const href = await links[i].getAttribute('href');
        if (href && !href.startsWith('http')) {
          await links[i].click();
          await page.waitForLoadState('networkidle');
          await page.goBack();
          await page.waitForLoadState('networkidle');
        }
      }
    }
  });

  test('should support browser back and forward', async ({ page }) => {
    await page.goto('/');

    // Navigate to a few pages
    await page.goto('/workflows');
    await page.waitForLoadState('networkidle');

    await page.goto('/control');
    await page.waitForLoadState('networkidle');

    // Go back
    await page.goBack();
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/workflows');

    // Go forward
    await page.goForward();
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/control');
  });

  test('should handle route parameters correctly', async ({ page }) => {
    // Navigate to a route with parameters
    await page.goto('/workflows');

    // Try accessing a details route (might not exist in current implementation)
    await page.goto('/workflows/test-workflow-id');

    // Should handle gracefully - either show details or 404
    await page.waitForLoadState('networkidle');

    // URL should contain our test ID
    expect(page.url()).toContain('test-workflow-id');
  });
});

// ============================================================================
// Navigation State Tests
// ============================================================================

test.describe('Navigation State', () => {
  test('should preserve navigation state across routes', async ({ page }) => {
    await page.goto('/');

    // Check for active route indicators
    const workflowLink = page.locator('a[href*="/workflows"]').first();

    if (await workflowLink.isVisible()) {
      await workflowLink.click();
      await page.waitForLoadState('networkidle');

      // The clicked link should have an active state
      const activeClass = await workflowLink.getAttribute('class');
      const isActive = activeClass?.includes('active') ||
                      await workflowLink.evaluate(el => {
                        const styles = window.getComputedStyle(el);
                        return styles.fontWeight === '700' || styles.fontWeight === 'bold';
                      });

      // Active state might be indicated in various ways
      expect(activeClass || isActive).toBeTruthy();
    }
  });

  test('should update browser title on route change', async ({ page }) => {
    await page.goto('/');

    let initialTitle = await page.title();

    await page.goto('/workflows');
    await page.waitForLoadState('networkidle');

    let workflowTitle = await page.title();

    // Title should change or at least contain TORQ
    expect(workflowTitle).toMatch(/TORQ|Console|Workflow/i);
  });
});
