import { test, expect } from '@playwright/test';

test.describe('End-to-End Portfolio Analysis Flow', () => {
    test.beforeEach(async ({ page }) => {
        // Navigate to the app (assuming it's running locally)
        await page.goto('http://localhost:3000');
    });

    test('should allow guest login and run analysis', async ({ page }) => {
        // 1. Bypass landing page by clicking "Misafir Olarak Dene"
        // Wait for landing page to be visible
        const guestBtn = page.getByRole('button', { name: /Misafir Olarak Dene/i });
        await expect(guestBtn).toBeVisible();
        await guestBtn.click();

        // 2. Ensure main app is visible
        await expect(page.locator('#sidebar')).toBeVisible();
        await expect(page.locator('#ticker-input')).toBeVisible();

        // 3. Enter tickers
        await page.locator('#ticker-input').fill('AAPL, TSLA');

        // 4. Start analysis
        const analyzeBtn = page.locator('#analyze-btn');
        await analyzeBtn.click();

        // 5. Wait for progress indicators (Loader)
        await expect(page.locator('#loader')).not.toHaveClass(/hidden/);
        
        // 6. Wait for results section to appear
        // SSE might take a few seconds
        await expect(page.locator('#results')).toBeVisible({ timeout: 30000 });
        
        // 7. Verify some results content (e.g. Hero Cards)
        const heroCards = page.locator('#hero-cards');
        await expect(heroCards).toBeVisible();
        
        // 8. Verify specific ticker data in summary table
        // (x-analysis-table usually populates based on state)
        await expect(page.locator('body')).toContainText(/AAPL/i);
        await expect(page.locator('body')).toContainText(/TSLA/i);
    });

    test('should show auth modal when clicking primary action without login', async ({ page }) => {
        // This test assumes we are on landing page
        await page.locator('#landing-nav-login-btn').click();
        await expect(page.locator('#login-modal')).toBeVisible();
        
        // Try password visibility toggle
        const pwInput = page.locator('#auth-password');
        await expect(pwInput).toHaveAttribute('type', 'password');
        await page.locator('button[onclick*="togglePasswordVisibility"]').click();
        await expect(pwInput).toHaveAttribute('type', 'text');
    });
});
