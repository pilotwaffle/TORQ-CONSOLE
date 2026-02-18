import { test, expect } from '@playwright/test';

/**
 * E2E tests for TORQ Console health and API endpoints.
 * Tests the deployed Vercel application.
 */

test.describe('TORQ Console - Health & Status', () => {
  test('health endpoint returns healthy status', async ({ request }) => {
    const response = await request.get('/health');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toMatchObject({
      status: 'healthy',
      service: 'torq-console',
      platform: 'vercel',
      timestamp: expect.any(String),
    });
  });

  test('api status endpoint returns service information', async ({ request }) => {
    const response = await request.get('/api/status');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toMatchObject({
      status: 'healthy',
      service: 'torq-console',
      version: expect.any(String),
      platform: 'vercel',
    });
  });

  test('root endpoint returns HTML', async ({ page }) => {
    await page.goto('/');

    // Should return HTML response
    const html = await page.content();
    expect(html).toBeTruthy();
    expect(html.length).toBeGreaterThan(0);
  });
});

test.describe('TORQ Console - API Endpoints', () => {
  test('chat endpoint handles missing API key gracefully', async ({ request }) => {
    const response = await request.post('/api/chat', {
      data: {
        message: 'test message',
        mode: 'single_agent',
      },
    });

    // Should return 200 (API handles errors gracefully)
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('detail');
    expect(data.detail).toContain('API key');
  });

  test('chat endpoint requires message field', async ({ request }) => {
    const response = await request.post('/api/chat', {
      data: {},  // Missing message
    });

    // Should return validation error (422) or handle gracefully
    expect(response.status()).toBeGreaterThanOrEqual(400);
  });
});

test.describe('TORQ Console - Documentation', () => {
  test('API documentation is accessible', async ({ page }) => {
    await page.goto('/docs');

    // FastAPI docs should be visible
    await page.waitForLoadState('networkidle');
    const url = page.url();
    expect(url).toContain('/docs');

    const content = await page.content();
    expect(content).toContain('TORQ Console API');
  });

  test('ReDoc documentation is accessible', async ({ page }) => {
    await page.goto('/redoc');

    await page.waitForLoadState('networkidle');
    const url = page.url();
    expect(url).toContain('/redoc');
  });
});
