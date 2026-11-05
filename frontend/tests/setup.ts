import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/svelte';
import { setupServer } from 'msw/node';
import { afterAll, afterEach, beforeAll, vi } from 'vitest';
import { handlers } from './mocks/handlers';

export const server = setupServer(...handlers);

vi.mock('$app/navigation', () => ({
  goto: vi.fn(),
  invalidateAll: vi.fn(),
  beforeNavigate: vi.fn(),
  afterNavigate: vi.fn()
}));

vi.mock('$app/environment', () => ({
  browser: true,
  dev: false,
  building: false,
  version: 'test'
}));

beforeAll(() => server.listen({ onUnhandledFrame: 'error' }));

afterEach(() => {
  cleanup();
  server.resetHandlers();
  vi.restoreAllMocks();
  document.cookie = 'pt_csrf=; Max-Age=0; path=/';
});

afterAll(() => server.close());
