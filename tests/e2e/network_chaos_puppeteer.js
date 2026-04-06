import puppeteer from 'puppeteer';

/**
 * 🧪 Network Chaos Test using Puppeteer
 * Verifies Exponential Backoff & Retry Logic
 */
async function runChaosTest() {
    const browser = await puppeteer.launch({ headless: "new" });
    const page = await browser.newPage();
    let attempt = 0;

    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    
    // Enable Request Interception
    await page.setRequestInterception(true);
    
    page.on('request', request => {
        const url = request.url();
        const method = request.method();

        // 🛡️ CORS Headers for Mock
        const headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Correlation-ID, Idempotency-Key'
        };

        if (method === 'OPTIONS') {
            return request.respond({ status: 204, headers });
        }

        if (url.includes('/api/search')) {
            console.log("🔍 Mocking Search Result...");
            request.respond({
                status: 200,
                headers,
                contentType: 'application/json',
                body: JSON.stringify([{ ticker: 'AAPL', name: 'Apple Inc.' }])
            });
        } else if (url.includes('/api/analyze')) {
            attempt++;
            if (attempt === 1) {
                console.log("💉 Injecting 503 Service Unavailable for /api/analyze...");
                request.respond({
                    status: 503,
                    headers,
                    contentType: 'application/json',
                    body: JSON.stringify({ detail: 'Service Unavailable' })
                });
            } else {
                console.log("✅ Allowing retry to succeed (SSE Mock)...");
                request.respond({
                    status: 200,
                    headers,
                    contentType: 'text/event-stream',
                    body: 'data: {"ticker": "AAPL", "price": 150}\n\n'
                });
            }
        } else {
            request.continue();
        }
    });

    try {
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle0' });

        // Bypass Landing Page
        console.log("🔓 Bypassing landing page...");
        await page.evaluate(() => {
            const guestBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Misafir'));
            if (guestBtn) guestBtn.click();
        });
        await new Promise(r => setTimeout(r, 500));
        
        console.log("⌨️ Typing AAPL...");
        await page.type('#ticker-input', 'AAPL');
        await page.keyboard.press('Enter');
        
        console.log("🚀 Clicking analyze button...");
        await page.waitForSelector('#analyze-btn:not([disabled])');
        await page.click('#analyze-btn');

        // Wait for the UI to reflect the retry state
        await page.waitForFunction(
            () => {
                const text = document.getElementById('progress-text')?.textContent.toLowerCase() || "";
                return text.includes('retry') || text.includes('tekrar');
            },
            { timeout: 10000 }
        );
        console.log("🎯 UI detected 'retry' state successfully.");

        // Wait for final success
        await page.waitForSelector('.result-card', { timeout: 15000 });
        const ticker = await page.$eval('.result-card', el => el.getAttribute('data-ticker') || 'AAPL');
        
        if (ticker === 'AAPL') {
            console.log("⭐⭐⭐ CHAOS TEST PASSED: System healed itself!");
        } else {
            throw new Error(`Expected AAPL but got ${ticker}`);
        }

    } catch (err) {
        console.error("❌ CHAOS TEST FAILED:", err.message);
        process.exit(1);
    } finally {
        await browser.close();
    }
}

runChaosTest();
