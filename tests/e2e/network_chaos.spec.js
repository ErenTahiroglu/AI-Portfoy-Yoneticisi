const { test, expect } = require('@playwright/test');

test.describe('Aggressive Network Chaos & Resilience Tests', () => {
  
  test('Frontend should survive unexpected SSE Analysis drops (Network Abort)', async ({ page }) => {
    // Navigate to local or production depending on environment
    await page.goto(process.env.TEST_URL || 'http://localhost:3000');
    
    // Simulate being logged in (Zero-Trust LocalStorage mock)
    await page.evaluate(() => {
      localStorage.setItem('supabase.auth.token', JSON.stringify({
        currentSession: { access_token: 'fake-token' }
      }));
    });
    
    // Intercept the /api/analyze SSE route and abort it randomly!
    await page.route('**/api/analyze', async route => {
      // Intentionally drop the connection as if Vercel Timeout hit
      await route.abort('failed');
    });

    // Wait for App to initialize
    await page.waitForTimeout(2000);

    // Try starting an analysis
    // Type a ticker
    const input = page.locator('#tickerInput, [data-test="ticker-input"]');
    if (await input.count() > 0) {
      await input.fill('AAPL');
      await page.keyboard.press('Enter');
    }

    // Since the network was aborted, the frontend should NOT freeze.
    // It should either show an error notification or stop the loading state.
    // Wait a couple seconds to see how UI reacts.
    await page.waitForTimeout(1000);

    // Verify spinning loader is gone or error is shown
    const isLoaderVisible = await page.locator('.loading-spinner').isVisible();
    expect(isLoaderVisible).toBeFalsy();
    
    // Check if error message is displayed somewhere on screen
    const bodyText = await page.locator('body').innerText();
    expect(bodyText).toMatch(/hata|zaman|bağlantı|çöktü/i);
  });

  test('Frontend should handle heavy HTTP Throttling gracefully', async ({ page }) => {
    // Create a slow network condition via CDP
    const client = await page.context().newCDPSession(page);
    await client.send('Network.emulateNetworkConditions', {
        offline: false,
        latency: 1000, // 1 saniye gecikme
        downloadThroughput: 50 * 1024, // 50 kb/s (Çok yavaş bağlantı)
        uploadThroughput: 50 * 1024
    });

    await page.goto(process.env.TEST_URL || 'http://localhost:3000');
    
    // Yavaş yükleme durumunda uygulamanın tamamen beyaz ekranda kalmamasını bekle.
    // Navbar veya ana başlığın en fazla 5 saniye içinde belirmesini zorunlu kıl.
    const header = page.locator('header, h1');
    await expect(header).toBeVisible({ timeout: 10000 });
  });

});
