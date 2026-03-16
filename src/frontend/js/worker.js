// ═══════════════════════════════════════
// WEB WORKER - DENSE ANALYTICS
// ═══════════════════════════════════════

self.onmessage = function(e) {
    const { results, payload } = e.data;
    const extras = {
        correlation: { tickers: [], matrix: [] },
        monte_carlo: null,
        pv_simulation: null
    };

    if (!results || results.length === 0) {
        self.postMessage(extras);
        return;
    }

    const validResults = results;

    // 1. Correlation Matrix
    const tickers = validResults.map(r => r.ticker);
    extras.correlation.tickers = tickers;

    for (let i = 0; i < tickers.length; i++) {
        const row = [];
        const historyI = validResults[i].technicals?.relative_performance?.stock_history || [];
        for (let j = 0; j < tickers.length; j++) {
            if (i === j) { row.push(1.0); continue; }
            const historyJ = validResults[j].technicals?.relative_performance?.stock_history || [];
            row.push(calculateCorrelation(historyI, historyJ));
        }
        extras.correlation.matrix.push(row);
    }

    // 2. Monte Carlo
    extras.monte_carlo = runMonteCarloJS(validResults);

    // 3. PV Simulation
    if (payload) {
         extras.pv_simulation = runPVSimulationJS(validResults, payload);
    }

    self.postMessage(extras);
};

function calculateCorrelation(seriesA, seriesB) {
    const n = Math.min(seriesA.length, seriesB.length);
    if (n < 2) return 0;
    
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;
    for (let i = 0; i < n; i++) {
        sumX += seriesA[i]; sumY += seriesB[i];
        sumXY += seriesA[i] * seriesB[i];
        sumX2 += seriesA[i] * seriesA[i]; sumY2 += seriesB[i] * seriesB[i];
    }
    const num = (n * sumXY) - (sumX * sumY);
    const den = Math.sqrt(((n * sumX2) - (sumX * sumX)) * ((n * sumY2) - (sumY * sumY)));
    return den === 0 ? 0 : parseFloat((num / den).toFixed(2));
}

function runPVSimulationJS(results, payload) {
    const initialBalance = Number(payload.initial_balance || 10000);
    const monthlyContribution = Number(payload.monthly_contribution || 0);
    
    const minLength = Math.min(...results.map(r => r.technicals.relative_performance.stock_history.length));
    if (minLength < 2) return null;

    const totalWeight = results.reduce((sum, r) => sum + (r.weight || 1.0), 0);
    const initialWeights = results.map(r => (r.weight || 1.0) / totalWeight);

    let currentBalance = initialBalance;
    let currentBenchmark = initialBalance;

    const balanceHistory = [currentBalance];
    const benchmarkHistory = [currentBenchmark];
    const drawdownSeries = [0];

    let maxBalance = currentBalance;
    let maxDrawdown = 0;

    const dates = results[0]?.technicals?.relative_performance?.dates || [];

    for (let t = 1; t < minLength; t++) {
        let periodReturn = 0;
        let periodBmReturn = 0;

        results.forEach((r, idx) => {
            const hist = r.technicals.relative_performance.stock_history;
            const bmHist = r.technicals.relative_performance.bm_history;

            if (hist && hist[t-1] > 0) {
                periodReturn += ((hist[t] / hist[t-1]) - 1) * initialWeights[idx];
            }
            
            if (bmHist && bmHist[t-1] > 0) {
                periodBmReturn += ((bmHist[t] / bmHist[t-1]) - 1) * initialWeights[idx];
            }
        });

        currentBalance = currentBalance * (1 + periodReturn) + monthlyContribution;
        currentBenchmark = currentBenchmark * (1 + periodBmReturn) + monthlyContribution;

        balanceHistory.push(currentBalance);
        benchmarkHistory.push(currentBenchmark);

        if (currentBalance > maxBalance) maxBalance = currentBalance;
        const dd = maxBalance > 0 ? ((maxBalance - currentBalance) / maxBalance) * 100 : 0;
        drawdownSeries.push(-dd);
        if (dd > maxDrawdown) maxDrawdown = dd;
    }

    const finalBalance = currentBalance;
    const totalInvested = initialBalance + (monthlyContribution * (minLength - 1));
    const totalReturn = (finalBalance - totalInvested) / totalInvested;
    
    // Assuming 5-day step (weekly)
    const weeksToYear = (minLength - 1) / 52;
    const cagr = weeksToYear > 0 ? (Math.pow(1 + totalReturn, 1 / weeksToYear) - 1) * 100 : 0;

    const periodReturns = [];
    for (let t = 1; t < balanceHistory.length; t++) periodReturns.push((balanceHistory[t] / balanceHistory[t-1]) - 1);
    const meanRet = periodReturns.reduce((a, b) => a + b, 0) / periodReturns.length;
    const downsideDev = Math.sqrt(periodReturns.map(v => v < 0 ? Math.pow(v, 2) : 0).reduce((a, b) => a + b, 0) / periodReturns.length);
    const stdDev = Math.sqrt(periodReturns.map(v => Math.pow(v - meanRet, 2)).reduce((a, b) => a + b, 0) / periodReturns.length);

    return {
        metrics: {
            cagr: parseFloat(cagr.toFixed(1)), 
            max_drawdown: parseFloat(maxDrawdown.toFixed(1)),
            sharpe: stdDev > 0 ? parseFloat(((meanRet / stdDev) * Math.sqrt(52)).toFixed(2)) : 0,
            drawdown_series: drawdownSeries
        },
        final_balance: Math.round(finalBalance),
        dates: dates.slice(0, minLength),
        balance_history: balanceHistory.map(v => Math.round(v)),
        benchmark_history: benchmarkHistory.map(v => Math.round(v))
    };
}

function runMonteCarloJS(results) {
    const minLength = Math.min(...results.map(r => r.technicals.relative_performance.stock_history.length));
    if (minLength < 4) return null;

    const portfolioReturns = [];
    const totalWeight = results.reduce((sum, r) => sum + (r.weight || 1.0), 0);

    for (let i = 1; i < minLength; i++) {
        let periodRet = 0;
        results.forEach(r => {
            const hist = r.technicals.relative_performance.stock_history;
            periodRet += (((hist[i] / hist[i-1]) - 1) * ((r.weight || 1.0) / totalWeight));
        });
        portfolioReturns.push(periodRet);
    }

    const mean = portfolioReturns.reduce((a, b) => a + b, 0) / portfolioReturns.length;
    const stdDev = Math.sqrt(portfolioReturns.map(v => Math.pow(v - mean, 2)).reduce((a, b) => a + b, 0) / portfolioReturns.length);

    const simulations = [];
    const numSims = 200, steps = 12;

    for (let s = 0; s < numSims; s++) {
        const simPath = [1.0]; let current = 1.0;
        for (let t = 0; t < steps; t++) {
            const randStdNorm = Math.sqrt(-2.0 * Math.log(Math.random())) * Math.sin(2.0 * Math.PI * Math.random());
            current *= (1 + (mean + stdDev * randStdNorm));
            simPath.push(current);
        }
        simulations.push(simPath);
    }

    const percentiles = { p5: [], p25: [], p50: [], p75: [], p95: [] };
    for (let t = 0; t <= steps; t++) {
        const stepValues = simulations.map(sim => sim[t]).sort((a, b) => a - b);
        percentiles.p5.push(parseFloat(stepValues[Math.floor(numSims * 0.05)].toFixed(3)));
        percentiles.p25.push(parseFloat(stepValues[Math.floor(numSims * 0.25)].toFixed(3)));
        percentiles.p50.push(parseFloat(stepValues[Math.floor(numSims * 0.5)].toFixed(3)));
        percentiles.p75.push(parseFloat(stepValues[Math.floor(numSims * 0.75)].toFixed(3)));
        percentiles.p95.push(parseFloat(stepValues[Math.floor(numSims * 0.95)].toFixed(3)));
    }
    return { percentiles, months: Array.from({length: steps + 1}, (_, i) => i) };
}
