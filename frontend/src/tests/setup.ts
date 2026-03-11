/**
 * Vitest Setup File
 *
 * Global test setup for TORQ Console
 * Runs before all test suites
 */

import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

// Extend Vitest's expect with jest-dom matchers
expect.extend({});

// Cleanup after each test
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// Mock window.location
global.location = {
  href: 'http://localhost:3013',
  origin: 'http://localhost:3013',
  protocol: 'http:',
  host: 'localhost:3013',
  hostname: 'localhost',
  port: '3013',
  pathname: '/',
  search: '',
  hash: '',
  username: '',
  password: '',
  assign: vi.fn(),
  reload: vi.fn(),
  replace: vi.fn(),
};

// Mock crypto.randomUUID for environments that don't have it
if (typeof crypto === 'undefined' || !crypto.randomUUID) {
  global.crypto = {
    randomUUID: () => {
      return 'mock-uuid-' + Math.random().toString(36).substring(2, 15);
    },
  } as any;
}

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
} as any;

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
} as any;

// Mock requestAnimationFrame
global.requestAnimationFrame = (callback: FrameRequestCallback) =>
  setTimeout(callback, 0) as unknown as number;

global.cancelAnimationFrame = (id: number) => {
  clearTimeout(id);
};

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  error: vi.fn(),
  warn: vi.fn(),
  log: vi.fn(),
};

export {};
