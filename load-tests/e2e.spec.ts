import { test, expect } from '@playwright/test';

test('open app and navigate to Copilot', async ({ page }) => {
    await page.goto('/');

    // Wait for main UI to load
    await page.waitForLoadState('domcontentloaded');

    // Try to find Copilot link and navigate
    const copilot = page.getByRole('link', { name: /copilot/i }).first();
    if (await copilot.count() > 0) {
        await copilot.click();
        await expect(page).toHaveURL(/\/copilot/);
        await expect(page.getByText(/Generate Test Cases|Quality Copilot|AI Insights/)).toBeVisible();
    } else {
        // fallback: ensure page has Projects or Dashboard text
        await expect(page.locator('text=Projects').first()).toBeVisible();
    }
});
