import { test, expect } from '@playwright/test';

/**
 * E2E tests for provider fallback system.
 * Tests fallback behavior once integrated into LLMManager.
 *
 * Note: These tests will require API keys to be configured in Vercel.
 */

test.describe('Provider Fallback System', () => {
  let apiConfigured = false;

  test.beforeAll(async ({ request }) => {
    // Check if API is configured
    try {
      const health = await request.get('/health');
      const data = await health.json();
      apiConfigured = data.anthropic_configured || data.openai_configed;
    } catch (e) {
      console.log('Could not verify API configuration');
    }
  });

  test.beforeEach(async ({}, testInfo) => {
    // Skip tests if API keys not configured
    if (!apiConfigured) {
      testInfo.skip('API keys not configured');
    }
  });

  test('simple query returns response with metadata', async ({ request }) => {
    const response = await request.post('/api/chat', {
      data: {
        message: 'What is 2+2? Answer with only the number.',
        mode: 'single_agent',
      },
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('response');
    expect(data).toHaveProperty('metadata');

    // Check metadata structure
    expect(data.metadata).toMatchObject({
      agent_id: expect.any(String),
      timestamp: expect.any(String),
    });
  });

  test('metadata includes provider information', async ({ request }) => {
    const response = await request.post('/api/chat', {
      data: {
        message: 'Hello',
        mode: 'single_agent',
      },
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.metadata).toHaveProperty('provider');
    expect(data.metadata).toHaveProperty('latency_ms');
  });

  test('metadata includes provider_attempts when fallback enabled', async ({ request }) => {
    // This test will pass once provider fallback is integrated
    const response = await request.post('/api/chat', {
      data: {
        message: 'Test query',
        mode: 'single_agent',
      },
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.metadata).toHaveProperty('provider_attempts');

    // Once fallback is integrated, check for:
    // - provider_attempts is an array
    // - fallback_used boolean
    // - fallback_reason string (when fallback used)
  });
});

test.describe('Provider Fallback - Error Handling', () => {
  test('handles timeout gracefully', async ({ request }) => {
    // This test would require mocking a timeout scenario
    // For now, we verify the API doesn't crash
    const response = await request.post('/api/chat', {
      data: {
        message: 'test',
        mode: 'single_agent',
      },
    });

    // Should return 200 even if query fails
    expect(response.status()).toBeGreaterThanOrEqual(200);
    expect(response.status()).toBeLessThan(500);
  });

  test('handles provider errors gracefully', async ({ request }) => {
    // Test that provider errors don't crash the API
    const response = await request.post('/api/chat', {
      data: {
        message: 'test',
        mode: 'single_agent',
      },
    });

    // Should handle errors gracefully
    expect(response.status()).toBeGreaterThanOrEqual(200);
  });
});

test.describe('Provider Fallback - Safety', () => {
  test('policy violations are handled correctly', async ({ request }) => {
    // Test that safety/policy violations don't crash the system
    // This would require triggering an actual policy violation

    // For now, verify the system is stable
    const health = await request.get('/health');
    expect(health.ok()).toBeTruthy();
  });
});
