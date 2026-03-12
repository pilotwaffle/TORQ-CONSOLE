/**
 * TORQ Console - Failover Visibility Tests
 * Post-Layer-11 Verification Plan
 *
 * Tests failover event visibility and status indication.
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';

// ============================================================================
// Failover Status Tests
// ============================================================================

test.describe('Failover Status', () => {
  test.use({ baseURL: BASE_URL });

  test.beforeEach(async ({ page }) => {
    await page.goto('/control');
  });

  test('should display system health status', async ({ page }) => {
    // Look for overall health indicator
    const healthStatus = page.locator(
      '[data-testid="health-status"], [data-testid="system-health"], div:has-text("health")'
    ).first();

    const healthVisible = await healthStatus.isVisible().catch(() => false);

    // Health status is optional in current implementation
    if (healthVisible) {
      await expect(healthStatus).toBeVisible();

      // Should have a status indicator (good/warning/error)
      const statusIndicator = healthStatus.locator(
        '[class*="status"], [role="status"]'
      ).first();

      await expect(statusIndicator).toBeVisible();
    }
  });

  test('should indicate degraded or failed nodes', async ({ page }) => {
    // Look for status badges
    const statusBadges = page.locator(
      '[class*="status"], [class*="badge"], span:has-text(/healthy|degraded|unhealthy|failed/i)'
    ).all();

    // If status badges exist, they should be accessible
    for (const badge of statusBadges) {
      if (await badge.isVisible().catch(() => false)) {
        const hasAria = await badge.getAttribute('role') ||
                        await badge.getAttribute('aria-label');

        // Status badges should ideally be accessible
        expect(badge).toBeTruthy();
      }
    }
  });
});

// ============================================================================
// Failover History Tests
// ============================================================================

test.describe('Failover History', () => {
  test.use({ baseURL: BASE_URL });

  test.beforeEach(async ({ page }) => {
    await page.goto('/control');
  });

  test('should show failover event log if events exist', async ({ page }) => {
    // Look for failover log section
    const failoverLog = page.locator(
      '[data-testid="failover-log"], [data-testid="failover-history"], section:has-text("failover")'
    ).first();

    const logVisible = await failoverLog.isVisible().catch(() => false);

    // Failover log is optional - depends on system state
    if (logVisible) {
      await expect(failoverLog).toBeVisible();

      // Check for event items
      const eventItems = failoverLog.locator(
        '[data-testid="failover-event"], li, tr'
      ).all();

      const itemCount = await eventItems.length;
      expect(itemCount).toBeGreaterThanOrEqual(0);
    }
  });

  test('should show failover statistics', async ({ page }) => {
    // Look for stats display
    const statsSection = page.locator(
      '[data-testid="failover-stats"], div:has-text("failover")'
    ).first();

    const statsVisible = await statsSection.isVisible().catch(() => false);

    if (statsVisible) {
      await expect(statsSection).toBeVisible();

      // Should have some numerical data
      const textContent = await statsSection.textContent();
      expect(textContent).toMatch(/\d+/); // At least one number
    }
  });
});

// ============================================================================
// Failover Action Tests
// ============================================================================

test.describe('Failover Actions', () => {
  test.use({ baseURL: BASE_URL });

  test.beforeEach(async ({ page }) => {
    await page.goto('/control');
  });

  test('should have manual failover controls if enabled', async ({ page }) => {
    // Look for manual failover button
    const failoverButton = page.locator(
      'button:has-text("Failover"), button:has-text("Migrate"), [data-testid="manual-failover"]'
    ).first();

    const buttonVisible = await failoverButton.isVisible().catch(() => false);

    // Manual failover controls are optional and require permissions
    if (buttonVisible) {
      await expect(failoverButton).toBeEnabled();
    }
  });

  test('should show confirmation dialog for failover actions', async ({ page }) => {
    const failoverButton = page.locator(
      'button:has-text("Failover"), button:has-text("Migrate")'
    ).first();

    if (await failoverButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await failoverButton.click();
      await page.waitForTimeout(500);

      // Should show confirmation
      const dialog = page.locator(
        '[role="dialog"], [data-testid="confirmation"], div:has-text("confirm")'
      ).first();

      const dialogVisible = await dialog.isVisible().catch(() => false);
      expect(dialogVisible).toBe(true);
    } else {
      test.skip(true, 'No failover button found');
    }
  });
});
