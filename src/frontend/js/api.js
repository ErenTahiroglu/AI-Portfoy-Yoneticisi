// ═══════════════════════════════════════
// CLIENT-SIDE EXTRAS CALCULATION (Web Worker)
// ═══════════════════════════════════════
async function calculateClientSideExtras(results, payload) {
    const validResults = results.filter(r => !r.error && r.technicals && r.technicals.relative_performance);
    
    const extras = {
        sector_distribution: {},
        correlation: { tickers: [], matrix: [] },
        monte_carlo: null,
        weighted_return_5y: 0,
        pv_simulation: null
    };

    if (validResults.length === 0) return extras;

    // 1. Sector Distribution
    validResults.forEach(r => {
        const sector = r.sector_localized ? r.sector_localized[getLang() === 'en' ? 'en' : 'tr'] : r.sector || (getLang() === 'en' ? "Unknown" : "Bilinmiyor");
        extras.sector_distribution[sector] = (extras.sector_distribution[sector] || 0) + 1;
    });

    // 2. Weighted Return
    let totalWeight = 0, weigthedSum = 0;
    validResults.forEach(r => {
        const w = r.weight || 1.0;
        const ret = r.financials?.s5 || 0;
        weigthedSum += ret * w;
        totalWeight += w;
    });
    if (totalWeight > 0) extras.weighted_return_5y = parseFloat((weigthedSum / totalWeight).toFixed(1));

    // 3. Dense Math via Web Worker
    try {
        const worker = new Worker('/ui/js/worker.js');

        const workerPromise = new Promise((resolve) => {
            worker.onmessage = (e) => {
                const workerExtras = e.data;
                extras.correlation = workerExtras.correlation;
                extras.monte_carlo = workerExtras.monte_carlo;
                extras.pv_simulation = workerExtras.pv_simulation;
                resolve();
            };
        });

        worker.postMessage({ results: validResults, payload });
        await workerPromise;
        worker.terminate();
    } catch (err) {
        console.error("Worker Execution Error:", err);
    }

    return extras;
}
