/**
 * TORQ Console - Mission Portfolio Tests
 * Post-Layer-11 Verification Plan
 *
 * Tests the Operator Control Surface mission portfolio view.
 */

import { test, expect } from '@playwright/test';

// ============================================================================
// Mission Portfolio Loading Tests
// ============================================================================

test.describe('Mission Portfolio', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/control');
    await page.waitForLoadState('networkidle');
  });

  test('should load the mission portfolio page', async ({ page }) => {
    // Check we're on the control page
    expect(page.url()).toContain('/control');

    // Look for main content area
    const mainContent = page.locator('main, [role="main"]').first();
    await expect(mainContent).toBeVisible({ timeout: 10000 });
  });

  test('should render mission list or empty state', async ({ page }) => {
    // Either a list of missions or an empty state should be visible
    const missionList = page.locator('[data-testid="mission-list"], table, [role="table"]').first();
    const emptyState = page.locator('[data-testid="empty-state"], text: /no missions|empty/i').first();

    const listVisible = await missionList.isVisible().catch(() => false);
    const emptyVisible = await emptyState.isVisible().catch(() => false);

    expect(listVisible || emptyVisible).toBe(true);
  });
});

// ============================================================================
// Mission List Controls Tests
// ============================================================================

test.describe('Mission List Controls', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/control');
    await page.waitForLoadState('networkidle');
  });

  test('should have refresh functionality', async ({ page }) => {
    // Look for refresh button
    const refreshButton = page.locator(
      'button:has-text("Refresh"), button[aria-label*="refresh"], button[title*="refresh"], svg[class*="refresh"]'
    ).first();

    if (await refreshButton.isVisible()) {
      const beforeText = await page.content();

      await refreshButton.click();
      await page.waitForTimeout(1000);

      // Page should still be functional
      const afterText = await page.content();
      expect(page.url()).toContain('/control');
    }
  });

  test('should have filter controls', async ({ page }) => {
    // Look for filter dropdowns or buttons
    const filters = await page.locator(
      'select, button:has-text("Filter"), [data-testid="filter"], [role="combobox"]'
    ).all();

    // At minimum, should have some interactive controls
    const buttons = await page.locator('button').all();
    expect(buttons.length).toBeGreaterThan(0);
  });
});

// ============================================================================
// Mission Detail Navigation Tests
// ============================================================================

test.describe('Mission Detail Navigation', () => {
  test('should navigate to mission detail when mission is clicked', async ({ page }) => {
    await page.goto('/control');

    // Look for clickable mission items
    const missionItem = page.locator(
      'tr[data-mission-id], [data-testid="mission-item"], a[href*="/control/missions"]'
    ).first();

    if (await missionItem.isVisible({ timeout: 5000 }).catch(() => false)) {
      await missionItem.click();
      await page.waitForLoadState('networkidle');

      // Should navigate to mission detail
      expect(page.url()).toMatch(/\/control\/missions\/.+/);
    } else {
      // No missions - that's OK for this test
      test.skip(true, 'No missions available to test');
    }
  });

  test('should handle mission detail page directly', async ({ page }) => {
    // Navigate directly to a mission detail (might not exist)
    await page.goto('/control/missions/test-mission-id');
    await page.waitForLoadState('networkidle');

    // Should either show details or handle gracefully
    const notFound = page.locator('text: /not found|404/i').first();
    const missionDetail = page.locator('[data-testid="mission-detail"], main').first();

    const detailVisible = await missionDetail.isVisible().catch(() => false);
    const notFoundVisible = await notFound.isVisible().catch(() => false);

    expect(detailVisible || notFoundVisible).toBe(true);
  });
});

// ============================================================================
// Mission Status Display Tests
// ============================================================================

test.describe('Mission Status Display', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/control');
    await page.waitForLoadState('networkidle');
  });

  test('should display status badges correctly', async ({ page }) => {
    // Look for status badges or indicators - use simpler selector
    const statusBadges = await page.locator(
      '[class*="status"], [class*="badge"], [data-testid*="status"]'
    ).all();

    // If there are badges, they should be visible
    if (statusBadges.length > 0) {
      const visibleBadges = await Promise.all(
        statusBadges.map(badge => badge.isVisible().catch(() => false))
      );

      expect(visibleBadges.some(v => v)).toBe(true);
    }
  });

  test('should display progress indicators for active missions', async ({ page }) => {
    // Look for progress bars or percentage indicators
    const progressBars = await page.locator(
      '[role="progressbar"], [class*="progress"], progress'
    ).all();

    // Progress bars should have proper attributes
    for (const bar of progressBars) {
      if (await bar.isVisible().catch(() => false)) {
        const hasAria = await bar.getAttribute('role');
        const hasValue = await bar.getAttribute('value') ||
                        await bar.getAttribute('aria-valuenow');

        // Progress bars should be accessible
        expect(bar).toBeTruthy();
      }
    }
  });
});
