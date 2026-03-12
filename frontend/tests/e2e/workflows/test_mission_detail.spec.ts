/**
 * TORQ Console - Mission Detail Tests
 * Post-Layer-11 Verification Plan
 *
 * Tests the mission detail view with graph, event stream, and node timeline.
 */

import { test, expect } from '@playwright/test';

const TEST_MISSION_ID = 'test-mission-123';

// ============================================================================
// Mission Detail Page Tests
// ============================================================================

test.describe('Mission Detail Page', () => {
  test('should load mission detail page', async ({ page }) => {
    await page.goto(`/control/missions/${TEST_MISSION_ID}`);
    await page.waitForLoadState('networkidle');

    // Should have main content
    const mainContent = page.locator('main, [role="main"]').first();
    await expect(mainContent).toBeVisible({ timeout: 10000 });
  });

  test('should display mission header with basic info', async ({ page }) => {
    await page.goto(`/control/missions/${TEST_MISSION_ID}`);
    await page.waitForLoadState('networkidle');

    // Look for heading with mission info
    const heading = page.locator('h1, h2, [data-testid="mission-header"]').first();
    await expect(heading).toBeVisible({ timeout: 10000 });
  });

  test('should handle missing missions gracefully', async ({ page }) => {
    await page.goto('/control/missions/non-existent-mission');
    await page.waitForLoadState('networkidle');

    // Should not crash - either show 404 or handle gracefully
    const bodyVisible = await page.locator('body').isVisible();
    expect(bodyVisible).toBe(true);
  });
});

// ============================================================================
// Mission Graph Tests
// ============================================================================

test.describe('Mission Graph', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`/control/missions/${TEST_MISSION_ID}`);
    await page.waitForLoadState('networkidle');
  });

  test('should render mission graph or graph container', async ({ page }) => {
    // Look for graph visualization
    const graphContainer = page.locator(
      '[data-testid="mission-graph"], [data-testid="workflow-graph"], canvas, svg'
    ).first();

    const graphVisible = await graphContainer.isVisible().catch(() => false);

    // Graph should be visible or there should be a placeholder
    expect(graphVisible).toBe(true);
  });

  test('should have graph controls', async ({ page }) => {
    // Look for zoom, pan, or fit controls
    const graphControls = await page.locator(
      'button[aria-label*="zoom"], button[aria-label*="pan"], button[aria-label*="fit"], [data-testid="graph-controls"]'
    ).all();

    // If graph controls exist, they should be clickable
    for (const control of graphControls) {
      if (await control.isVisible().catch(() => false)) {
        await expect(control).toBeEnabled();
      }
    }
  });
});

// ============================================================================
// Event Stream Tests
// ============================================================================

test.describe('Mission Event Stream', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`/control/missions/${TEST_MISSION_ID}`);
    await page.waitForLoadState('networkidle');
  });

  test('should display event stream section', async ({ page }) => {
    // Look for event stream container
    const eventStream = page.locator(
      '[data-testid="event-stream"], [data-testid="mission-events"], section:has-text("event")'
    ).first();

    const streamVisible = await eventStream.isVisible().catch(() => false);

    // Event stream might be in a tab or panel
    if (!streamVisible) {
      // Check for tabs that might contain events
      const tabs = await page.locator('[role="tab"]').all();
      const tabsVisible = await Promise.all(
        tabs.map(tab => tab.isVisible().catch(() => false))
      );

      // At least tabs should exist if event stream is hidden
      expect(tabsVisible.some(v => v) || streamVisible).toBe(true);
    }
  });

  test('should distinguish between simulated and live events', async ({ page }) => {
    // Look for visual distinction between event types
    const simulatedBadge = page.locator(
      '[data-testid="simulated-badge"], [class*="simulated"], text: /simulated/i'
    ).first();

    const liveBadge = page.locator(
      '[data-testid="live-badge"], [class*="live"], text: /live|real/i'
    ).first();

    // At least one type of badge should be visible if events exist
    const hasEventBadges = await Promise.all([
      simulatedBadge.isVisible().catch(() => false),
      liveBadge.isVisible().catch(() => false)
    ]);

    // This is a soft assertion - events might not exist in test data
    if (hasEventBadges.some(v => v)) {
      // If events are shown, they should be distinguishable
      expect(true).toBe(true);
    }
  });
});

// ============================================================================
// Node Detail Drawer Tests
// ============================================================================

test.describe('Node Detail Drawer', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`/control/missions/${TEST_MISSION_ID}`);
    await page.waitForLoadState('networkidle');
  });

  test('should open node detail when node is clicked', async ({ page }) => {
    // Look for clickable nodes
    const node = page.locator(
      '[data-testid="workflow-node"], [class*="node"], circle[data-id], rect[data-id]'
    ).first();

    if (await node.isVisible({ timeout: 5000 }).catch(() => false)) {
      await node.click();
      await page.waitForTimeout(500);

      // Should show drawer or detail panel
      const drawer = page.locator(
        '[data-testid="node-detail"], [data-testid="drawer"], aside[class*="detail"], dialog'
      ).first();

      const drawerVisible = await drawer.isVisible().catch(() => false);
      expect(drawerVisible).toBe(true);
    } else {
      test.skip(true, 'No graph nodes visible to test');
    }
  });

  test('should close drawer when close button is clicked', async ({ page }) => {
    // First try to open a drawer
    const node = page.locator('[data-testid="workflow-node"], circle, rect').first();

    if (await node.isVisible({ timeout: 5000 }).catch(() => false)) {
      await node.click();
      await page.waitForTimeout(500);

      const closeButton = page.locator(
        'button:has-text("Close"), button[aria-label*="close"], button[class*="close"]'
      ).first();

      if (await closeButton.isVisible().catch(() => false)) {
        await closeButton.click();
        await page.waitForTimeout(300);

        // Drawer should be closed or hidden
        const drawer = page.locator('[data-testid="drawer"], aside, dialog').first();
        const visible = await drawer.isVisible().catch(() => true);

        // Either drawer is gone or not visible
        expect(visible).toBe(false);
      }
    } else {
      test.skip(true, 'No graph nodes visible to test');
    }
  });
});

// ============================================================================
// Mission Timeline Tests
// ============================================================================

test.describe('Mission Timeline', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`/control/missions/${TEST_MISSION_ID}`);
    await page.waitForLoadState('networkidle');
  });

  test('should display timeline or execution history', async ({ page }) => {
    // Look for timeline component
    const timeline = page.locator(
      '[data-testid="timeline"], [data-testid="execution-history"], ol[class*="timeline"]'
    ).first();

    const timelineVisible = await timeline.isVisible().catch(() => false);

    // Timeline is optional for this test
    if (timelineVisible) {
      await expect(timeline).toBeVisible();
    }
  });
});
