const { test, expect } = require('@playwright/test');

test.describe('Network Chaos & Resilience Tests', () => {
    test('should retry on 503 Service Unavailable and eventually succeed', async ({ page }) => {
        let attempt = 0;

        // Intercept /api/analyze
        await page.route('**/api/analyze', async (route) => {
            attempt++;
            if (attempt === 1) {
                // Fail the first attempt
                await route.fulfill({
                    status: 503,
                    contentType: 'application/json',
                    body: JSON.stringify({ detail: 'Service Unavailable' })
                });
            } else {
                // Succeed on subsequent attempts (mocked SSE)
                await route.fulfill({
                    status: 200,
                    contentType: 'text/event-stream',
                    body: 'data: {"ticker": "AAPL", "price": 150}\n\n'
                });
            }
        });

        await page.goto('/');
        
        // Trigger analysis
        await page.fill('#ticker-input', 'AAPL');
        await page.click('#analyze-btn');

        // Check for "retrying" message (it should appear after the 1st failure)
        // Note: Our backoff starts at 2s for attempt 1
        const statusMsg = page.locator('#progress-text'); // Assuming this ID exists in HTML
        await expect(statusMsg).toContainText(/retrying/i, { timeout: 10000 });

        // Verify it eventually succeeds
        const resultCard = page.locator('#skeleton-AAPL'); // It will be replaced by real card
        // Actually, in our ResultsComponent, we replace skeleton with real card
        await expect(page.locator('.ticker-card')).toBeVisible({ timeout: 15000 });
        await expect(page.locator('.ticker-symbol')).toHaveText('AAPL');
    });

    test('should retry on network disconnect (abort)', async ({ page }) => {
        let attempt = 0;

        await page.route('**/api/analyze', async (route) => {
            attempt++;
            if (attempt === 1) {
                await route.abort('failed');
            } else {
                await route.fulfill({
                    status: 200,
                    contentType: 'text/event-stream',
                    body: 'data: {"ticker": "MSFT", "price": 300}\n\n'
                });
            }
        });

        await page.goto('/');
        await page.fill('#ticker-input', 'MSFT');
        await page.click('#analyze-btn');

        await expect(page.locator('.ticker-card')).toBeVisible({ timeout: 15000 });
        await expect(page.locator('.ticker-symbol')).toHaveText('MSFT');
    });
});
