import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.BASE_URL || process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:8000';

export default defineConfig({
  testDir: './tests',
  testMatch: ['**/vnk3-*.spec.ts'],
  timeout: 30 * 1000,
  expect: { timeout: 10000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['list'],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    headless: true,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'cd .. && set ADMIN_USERNAME=admin && set ADMIN_PASSWORD=adminpass && set APP_ENV=development && python -m uvicorn dev.app.main:app --host 127.0.0.1 --port 8000',
    url: baseURL,
    reuseExistingServer: true,
    timeout: 120 * 1000,
  },
});
