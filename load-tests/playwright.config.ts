import { defineConfig } from '@playwright/test';

export default defineConfig({
    testDir: './',
    timeout: 30_000,
    expect: { timeout: 5000 },
    use: {
        headless: true,
        baseURL: process.env.BASE_URL || 'http://localhost:5173',
        viewport: { width: 1280, height: 720 },
        actionTimeout: 5000,
        trace: 'on-first-retry',
    },
    projects: [
        { name: 'chromium', use: { browserName: 'chromium' } },
    ],
});
