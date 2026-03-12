/**
 * TORQ Console - Playwright Configuration
 * Post-Layer-11 Verification Plan
 *
 * Configuration for E2E testing across local and browser environments.
 */

import { defineConfig, devices } from '@playwright/test';

/**
 * Read environment variables and set defaults
 */
const baseURL = process.env.BASE_URL || 'http://localhost:5173';
const browserURL = process.env.BROWSER_URL || 'https://torq-console.vercel.app';

/**
 * Test timeout configuration
 */
const TIMEOUT = 30000;
const ACTION_TIMEOUT = 10000;

export default defineConfig({
  // Test directory
  testDir: './tests/e2e',

  // Timeout settings
  timeout: TIMEOUT,
  expect: {
    timeout: ACTION_TIMEOUT,
  },

  // Run tests in parallel
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
    ['json', { outputFile: 'test-results.json' }],
  ],

  // Shared settings for all tests
  use: {
    // Base URL for tests
    baseURL,

    // Collect trace when retrying
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video on failure
    video: 'retain-on-failure',

    // Action navigation timeout
    actionTimeout: ACTION_TIMEOUT,

    // Wait for network idle after navigation
    navigationTimeout: TIMEOUT,
  },

  // Projects for different environments
  projects: [
    {
      name: 'local-chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'local-firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'local-webkit',
      use: { ...devices['Desktop Safari'] },
    },

    {
      name: 'browser-deployment',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: browserURL,
      },
    },

    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },

    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  // Start local dev server before running tests (optional)
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:5173',
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120000,
  // },
});
