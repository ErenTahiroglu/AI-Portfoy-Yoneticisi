// ── Global Correlation ID Tracer & Cold Start Resilience ──
(function() {
    let coldStartWarningShown = false; 

    // Kapı Zili (Ping-First) Sistemi: Render uyanık mı?
    async function pingServer(originalFetch) {
        const retries = 4;
        for (let i = 0; i < retries; i++) {
            try {
                const healthRes = await originalFetch(`${API_BASE || ""}/api/health`, { method: "GET" });
                if (healthRes.ok) return true;
                throw new Error("Sunucu uyanmadı");
            } catch (err) {
                if (i === retries - 1) return false;
                
                if (!coldStartWarningShown && typeof window.showToast === "function") {
                    coldStartWarningShown = true;
                    window.showToast("🚀 Motorlar Isıtılıyor (Bu işlem yaklaşık 15-30 saniye sürebilir)...", "info");
                    setTimeout(() => { coldStartWarningShown = false; }, 30000);
                }
                
                const backoffTime = 3000 * Math.pow(2, i); // 3s, 6s, 12s
                console.warn(`[Kapı Zili] Sunucu uykuda. ${backoffTime/1000}s sonra tekrar deneniyor...`);
                await new Promise(r => setTimeout(r, backoffTime));
            }
        }
        return false;
    }

    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        let [resource, config] = args;
        
        // Sadece kendi API'mize giden istekleri yakala
        if (typeof resource === "string" && resource.includes("/api/")) {
            config = config || {};
            config.headers = config.headers || {};
            if (!config.headers["X-Correlation-ID"]) {
                config.headers["X-Correlation-ID"] = crypto.randomUUID();
            }
            args[1] = config;

            // Ping-First: Eğer ağır bir istekse (POST/PUT vs ve health değilse), önce kapıyı çal.
            if (config.method && ["POST", "PUT"].includes(config.method.toUpperCase()) && !resource.includes("/health")) {
                 const isAwake = await pingServer(originalFetch);
                 if (!isAwake) {
                     throw new Error("Sunucu uyandırılamadı (Vercel Timeout veya Render Down). Lütfen daha sonra tekrar deneyin.");
                 }
            }

            const retries = 3;
            // İlk istek genel ağ hatası verirse standart retry algısı:
            for (let i = 0; i < retries; i++) {
                try {
                    const response = await originalFetch.apply(this, args);
                    
                    if (response.ok || ![502, 503, 504].includes(response.status)) {
                        return response;
                    }
                    throw new Error(`Status: ${response.status}`);
                } catch (err) {
                    if (i === retries - 1) throw err;
                    const backoffTime = 2000 * Math.pow(2, i);
                    await new Promise(r => setTimeout(r, backoffTime));
                }
            }
        }
        
        return originalFetch.apply(this, args);
    };
})();

// ═══════════════════════════════════════
// ASYNC JOB POLLING ENGINE (Vercel Timeout Bypass)
// ═══════════════════════════════════════
window.pollJobResult = async function(jobId, pollingInterval = 3000) {
    if (!jobId) throw new Error("Job ID eksik");
    
    return new Promise((resolve, reject) => {
        let attempts = 0;
        const maxAttempts = 40; // Maksimum 2 dakika tahammül (40 * 3 sn = 120s). Sonsuz döngü kalkanı.
        
        const intervalChecker = setInterval(async () => {
             attempts++;
             if (attempts > maxAttempts) {
                  clearInterval(intervalChecker);
                  reject(new Error("Zaman aşımı: Sunucu görevi belirtilen sürede (2dk) tamamlayamadı. Sistem meşgul olabilir."));
                  return;
             }
             
             try {
                  const res = await fetch(`${API_BASE}/api/status/${jobId}`);
                  if (res.status === 404) {
                       clearInterval(intervalChecker);
                       reject(new Error("Arkaplan görevi (Job) zaman aşımına uğradı veya bulunamadı."));
                       return;
                  }
                  
                  const data = await res.json();
                  
                  if (data.status === "COMPLETED") {
                       clearInterval(intervalChecker);
                       resolve(data.result);
                  } else if (data.status === "ERROR") {
                       clearInterval(intervalChecker);
                       reject(new Error(data.error || "Arkaplan görevinde sunucu hatası."));
                  }
                  // PENDING veya RUNNING ise beklemeye devam et
             } catch (err) {
                  // status api'sine erişirken ağ hatası olduysa tolere et, poll etmeye devam et
                  console.warn("[Polling API Error]", err);
             }
        }, pollingInterval);
    });
};

// ═══════════════════════════════════════
// AI WIZARD
// ═══════════════════════════════════════
// runWizard has been moved to services/WizardService.js

// ═══════════════════════════════════════
// HEALTH CHECK
// ═══════════════════════════════════════
async function checkServerHealth() {
    try {
        const res = await fetch(`${API_BASE}/api/health`, { method: "GET" });
        if (res.ok) {
            const data = await res.json();
            return { online: true, message: data.message };
        }
        return { online: false, message: `Sunucu hatası: ${res.status}` };
    } catch (e) {
        return { online: false, message: "Sunucuya ulaşılamıyor (Cold start veya Bağlantı hatası)." };
    }
}

// ═══════════════════════════════════════
// DYNAMIC NEWS
// ═══════════════════════════════════════
// loadNews has been moved to services/NewsService.js

// ═══════════════════════════════════════
// EXPORT
// ═══════════════════════════════════════
// exportResults has been moved to services/ExportService.js

// exportPortfolioImage has been moved to services/ExportService.js

// ═══════════════════════════════════════
// MAIN ANALYSIS
// ═══════════════════════════════════════
// ═══════════════════════════════════════
// MAIN ANALYSIS (Streaming & Caching)
// ═══════════════════════════════════════
async function runAnalysis(payload, endpoint) {
    const macroPanel = document.getElementById("macro-advice-container");
    if (macroPanel) macroPanel.remove();

    const btn = document.getElementById("analyze-btn");
    const progressContainer = document.getElementById("progress-container");
    const progressFill = document.getElementById("progress-fill");
    const progressText = document.getElementById("progress-text");
    const resultsSection = document.getElementById("results");

    btn.disabled = true; 
    resultsSection.classList.add("hidden");
    document.getElementById("loader").classList.add("hidden");
    progressContainer.classList.remove("hidden");

    let progress = 0;
    progressFill.style.width = "0%";
    progressText.textContent = getLang() === "en" ? "Checking cache..." : "Önbellek kontrol ediliyor...";

    await saveApiKeys();
    
    // Reset AppState results for a new analysis
    AppState.results = [];
    AppState.extras = null;

    try {
        const tickers = payload.tickers || [];
        const tickersToFetch = [];
        const cachedItems = [];

        let sseBuffer = [];
        let animationFrameId = null;

        // Batch Update Function (Üste taşındı)
        const triggerBatchUpdate = () => {
            if (animationFrameId) return; // Zaten planlanmış
            animationFrameId = requestAnimationFrame(async () => {
                if (sseBuffer.length > 0) {
                    const batch = [...sseBuffer];
                    sseBuffer = []; // Buffer'ı temizle
                    
                    // 1. Live Render (Toplu)
                    for (const item of batch) {
                        if (typeof renderSingleCard === "function") {
                            renderSingleCard(item);
                        }
                        // Sadece taze verileri önbelleğe kaydet
                        if (!item._fromCache) {
                            const cacheKey = `analysis_${item.ticker}_ai${payload.use_ai}_isl${payload.check_islamic}_fin${payload.check_financials}_mod${payload.use_ai ? payload.model : 'none'}`;
                            await setCache(cacheKey, item);
                        }
                    }

                    // 2. State Management (Toplu güncelleme)
                    AppState.results = [...AppState.results, ...batch];

                    // 3. UI Progress Güncelleme
                    const lastItem = batch[batch.length - 1];
                    progressText.textContent = `${lastItem.ticker} ${getLang() === "en" ? "analyzed." : "analiz edildi."}`;
                    const progress = (AppState.results.length / tickers.length) * 100;
                    progressFill.style.width = `${Math.min(progress, 100)}%`;
                }
                animationFrameId = null;
                // Yeni veri gelmişse tekrar tetikle
                if (sseBuffer.length > 0) triggerBatchUpdate(); 
            });
        };

        // 1. Önbellek (IndexedDB) Kontrolü
        for (const ticker of tickers) {
            const cleanTicker = ticker.trim().toUpperCase();
            if (!cleanTicker) continue;

            const cacheKey = `analysis_${cleanTicker}_ai${payload.use_ai}_isl${payload.check_islamic}_fin${payload.check_financials}_mod${payload.use_ai ? payload.model : 'none'}`;
            const cachedData = await getCache(cacheKey);

            if (cachedData) {
                cachedData._fromCache = true; // Bayrak ekle
                cachedItems.push(cachedData);
            } else {
                tickersToFetch.push(cleanTicker);
            }
        }

        // Önbellekteki verileri anında buffer'a al ve batch-render et
        if (cachedItems.length > 0) {
            sseBuffer.push(...cachedItems);
            triggerBatchUpdate();
        }

        if (tickers.length > 0) {
            const progress = (cachedItems.length / tickers.length) * 100;
            progressFill.style.width = `${Math.min(progress, 100)}%`;
        }

        const grid = document.getElementById("results-grid");
        resultsSection.classList.remove("hidden");
        grid.innerHTML = ""; 
        document.getElementById("summary-table-body").innerHTML = "";

        const { createSkeletonCard } = await import('./components/CardComponent.js');
        tickers.forEach(t => {
            if (cachedItems.some(r => r.ticker === t)) return; // Skip cached ones
            const card = createSkeletonCard(t);
            grid.appendChild(card);
        });

        if (tickersToFetch.length > 0) {
            progressText.textContent = getLang() === "en" ? "Streaming analysis from server..." : "Sunucudan analiz akışı bekleniyor...";
            const fetchPayload = { ...payload, tickers: tickersToFetch };
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(fetchPayload)
            });

            if (!response.ok) {
                if (response.status === 429) {
                    throw new Error("Çok fazla istek attınız, sistem soğutuluyor. Lütfen 1 dakika sonra tekrar deneyin.");
                }
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || `Sunucu hatası (${response.status})`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";



            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value);
                const lines = buffer.split("\n\n");
                buffer = lines.pop(); // Sonuncu tamamlanmamış olabilir

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        try {
                            const dataString = line.substring(6);
                            const item = JSON.parse(dataString);
                            
                            if (item.ticker) {
                                sseBuffer.push(item);
                                triggerBatchUpdate();
                            }
                        } catch (e) {
                            console.error("Stream parse error:", e, line);
                        }
                    }
                }
            }

            // Stream bittiğinde Buffer'ın tamamen boşalmasını bekle
            while (sseBuffer.length > 0 || animationFrameId) {
                await new Promise(resolve => setTimeout(resolve, 50));
            }
        }

        progressFill.style.width = "100%"; 
        progressText.textContent = getLang() === "en" ? "Done!" : "Tamamlandı!";
        setTimeout(() => progressContainer.classList.add("hidden"), 500);

        // Calculate and Save Extras reactively
        const extras = calculateClientSideExtras(AppState.results, payload);
        AppState.extras = extras; // Save to State
        
        showToast(`${AppState.results.length} ${t("toast.analysisComplete")}`, "success");

        // --- Makro AI Analizi Tetikleme ---
        if (typeof renderMacroAI === "function") {
            runMacroAnalysis(renderMacroAI);
        }

    } catch (err) {
        progressContainer.classList.add("hidden");
        console.error("Analysis Error:", err);
        showToast(err.message || "Bağlantı hatası", "error");
    } finally {
        btn.disabled = false;
    }
}


// ═══════════════════════════════════════
// FILE ANALYSIS (Client-Side Parsing)
// ═══════════════════════════════════════
async function runFileAnalysis(file) {
    if (!file) return;
    showToast(getLang() === "en" ? "Parsing file..." : "Dosya okunuyor...", "info");

    const reader = new FileReader();
    const extension = file.name.split('.').pop().toLowerCase();

    reader.onload = function(e) {
        let tickers = [];
        try {
            if (extension === 'xlsx' || extension === 'xls') {
                // xlsx-js
                const data = new Uint8Array(e.target.result);
                const workbook = XLSX.read(data, { type: 'array' });
                const firstSheet = workbook.SheetNames[0];
                const worksheet = workbook.Sheets[firstSheet];
                // Get all text
                const csv = XLSX.utils.sheet_to_csv(worksheet);
                tickers = extractTickersFromCsv(csv);
            } else if (extension === 'csv' || extension === 'txt') {
                // PapaParse or text fallback
                const text = e.target.result;
                tickers = extractTickersFromCsv(text);
            } else {
                showToast("Desteklenmeyen dosya formatı", "error");
                return;
            }

            if (tickers.length === 0) {
                showToast("Dosyada geçerli sembol bulunamadı.", "warning");
                return;
            }

            // Update UI input to show extracted
            document.getElementById("ticker-input").value = tickers.join(", ");
            showToast(`${tickers.length} sembol çıkarıldı. Analiz başlıyor...`, "success");

            // Trigger Analysis
            const payload = {
                tickers: tickers,
                use_ai: document.getElementById("use-ai-toggle").checked,
                check_islamic: document.getElementById("check-islamic-toggle").checked,
                check_financials: document.getElementById("check-financials-toggle").checked,
                model: document.getElementById("model-select").value,
                lang: getLang(),
                initial_balance: parseFloat(document.getElementById("sim-initial-balance").value) || 10000,
                monthly_contribution: parseFloat(document.getElementById("sim-monthly-contribution").value) || 0,
                rebalancing_freq: document.getElementById("sim-rebalance-freq").value || "none"
            };
            runAnalysis(payload, "/api/analyze");

        } catch (err) {
            console.error("File Parse Error:", err);
            showToast(`Dosya okunurken hata: ${err.message}`, "error");
        }
    };

    if (extension === 'xlsx' || extension === 'xls') {
        reader.readAsArrayBuffer(file);
    } else {
        reader.readAsText(file);
    }
}

function extractTickersFromCsv(text) {
    // Highly resilient ticker extractor
    // Use regex to find uppercase words or parts with weight ':'
    const tickers = [];
    const rows = text.split(/\r?\n/);
    for (const row of rows) {
        // Find things like 'AAPL', 'THYAO:0.5', etc.
        // Match words that are all caps or have .IS / .HE or weights
        const matches = row.match(/[A-Z]+(\.[A-Z]+)?(:[0-9.]+)?/g);
        if (matches) {
            matches.forEach(m => {
                if (m.length >= 2 && !tickers.includes(m)) tickers.push(m);
            });
        }
    }
    return tickers;
}

// ═══════════════════════════════════════
// CLIENT-SIDE EXTRAS CALCULATION
// ═══════════════════════════════════════
function calculateClientSideExtras(results, payload) {
    const validResults = results.filter(r => !r.error && r.technicals && r.technicals.relative_performance);
    
    const extras = {
        sector_distribution: {},
        correlation: { tickers: [], matrix: [] },
        monte_carlo: null,
        weighted_return_5y: 0,
        pv_simulation: null
    };

    if (validResults.length === 0) return extras;

    // 1. Sektör Dağılımı
    validResults.forEach(r => {
        const sector = r.sector_localized ? r.sector_localized[getLang() === 'en' ? 'en' : 'tr'] : r.sector || (getLang() === 'en' ? "Unknown" : "Bilinmiyor");
        extras.sector_distribution[sector] = (extras.sector_distribution[sector] || 0) + 1;
    });

    // 2. Korelasyon Matrisi
    const tickers = validResults.map(r => r.ticker);
    extras.correlation.tickers = tickers;

    for (let i = 0; i < tickers.length; i++) {
        const row = [];
        const historyI = validResults[i].technicals.relative_performance.stock_history;
        for (let j = 0; j < tickers.length; j++) {
            if (i === j) { row.push(1.0); continue; }
            const historyJ = validResults[j].technicals.relative_performance.stock_history;
            row.push(calculateCorrelation(historyI, historyJ));
        }
        extras.correlation.matrix.push(row);
    }

    // 3. Monte Carlo Simülasyonu
    extras.monte_carlo = runMonteCarloJS(validResults);

    // 4. Ağırlıklı Getiri
    let totalWeight = 0;
    let weigthedSum = 0;
    validResults.forEach(r => {
        const w = r.weight || 1.0;
        const ret = r.financials?.s5 || 0;
        weigthedSum += ret * w;
        totalWeight += w;
    });
    if (totalWeight > 0) extras.weighted_return_5y = parseFloat((weigthedSum / totalWeight).toFixed(1));

    // 5. PV Simulation
    if (payload) {
        extras.pv_simulation = runPVSimulationJS(validResults, payload);
    }

    return extras;
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

function calculateCorrelation(seriesA, seriesB) {
    const n = Math.min(seriesA.length, seriesB.length);
    if (n < 2) return 0;
    
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;
    for (let i = 0; i < n; i++) {
        sumX += seriesA[i];
        sumY += seriesB[i];
        sumXY += seriesA[i] * seriesB[i];
        sumX2 += seriesA[i] * seriesA[i];
        sumY2 += seriesB[i] * seriesB[i];
    }
    const num = (n * sumXY) - (sumX * sumY);
    const den = Math.sqrt(((n * sumX2) - (sumX * sumX)) * ((n * sumY2) - (sumY * sumY)));
    return den === 0 ? 0 : parseFloat((num / den).toFixed(2));
}

function runMonteCarloJS(results) {
    if (results.length === 0) return null;
    const minLength = Math.min(...results.map(r => r.technicals.relative_performance.stock_history.length));
    if (minLength < 4) return null;

    const portfolioReturns = [];
    const totalWeight = results.reduce((sum, r) => sum + (r.weight || 1.0), 0);

    for (let i = 1; i < minLength; i++) {
        let periodRet = 0;
        results.forEach(r => {
            const hist = r.technicals.relative_performance.stock_history;
            const w = r.weight || 1.0;
            const singleRet = (hist[i] / hist[i-1]) - 1;
            periodRet += (singleRet * (w / totalWeight));
        });
        portfolioReturns.push(periodRet);
    }

    const mean = portfolioReturns.reduce((a, b) => a + b, 0) / portfolioReturns.length;
    const sqDiff = portfolioReturns.map(v => Math.pow(v - mean, 2));
    const variance = sqDiff.reduce((a, b) => a + b, 0) / (portfolioReturns.length);
    const stdDev = Math.sqrt(variance);

    const simulations = [];
    const numSims = 200;
    const steps = 12;

    for (let s = 0; s < numSims; s++) {
        const simPath = [1.0];
        let current = 1.0;
        for (let t = 0; t < steps; t++) {
            const u1 = Math.random();
            const u2 = Math.random();
            const randStdNorm = Math.sqrt(-2.0 * Math.log(u1)) * Math.sin(2.0 * Math.PI * u2);
            const walk = mean + stdDev * randStdNorm;
            current *= (1 + walk);
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

    return {
        percentiles,
        months: Array.from({length: steps + 1}, (_, i) => i)
    };
}

// ═══════════════════════════════════════
// MACRO AI ANALYSIS (SSE / FETCH STREAM)
// ═══════════════════════════════════════
async function runMacroAnalysis(onChunk) {
    const apiKey = document.getElementById("api-key")?.value || "";
    // If running in development or has setup, API_BASE is global
    const model = document.getElementById("model-select")?.value || "gemini-2.5-flash";
    const lang = getLang();

    if (!apiKey) {
        if (onChunk) onChunk("⚠️ **Makro Analiz için Gemini API Anahtarı eksik.** Ayarlardan ekleyin.", true);
        return;
    }

    const portfolioData = {
        results: AppState.results.map(r => ({
            ticker: r.ticker,
            market: r.market,
            weight: r.weight || 1,
            status: r.status,
            sector: r.sector,
            financials: r.financials ? { 
                son_fiyat: r.financials.son_fiyat, 
                s5: r.financials.s5 
            } : null,
            valuation: r.valuation ? { 
                pe: r.valuation.pe, 
                pb: r.valuation.pb 
            } : null
        })),
        extras: AppState.extras
    };

    try {
        let jwtToken = "";
        try {
            const session = await window.SupabaseAuth.getValidSession();
            if (session) jwtToken = session.access_token;
        } catch (e) {
            if (onChunk) onChunk(`⚠️ **Güvenlik Hatası:** ${e.message}`, true);
            return;
        }

        const response = await fetch(`${API_BASE}/api/analyze-macro`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${jwtToken}`
            },
            body: JSON.stringify({
                portfolio: portfolioData,
                api_key: apiKey,
                model: model,
                lang: lang
            })
        });

        if (!response.ok) {
            if (response.status === 429) {
                throw new Error("Çok fazla istek attınız, sistem soğutuluyor. Lütfen 1 dakika sonra tekrar deneyin.");
            }
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || "Makro analiz başlatılamadı");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value);
            const lines = buffer.split("\n\n");
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    const dataStr = line.substring(6).trim();
                    if (dataStr === "[DONE]") {
                        if (onChunk) onChunk(null, true);
                        break;
                    }
                    try {
                        const parsed = JSON.parse(dataStr);
                        if (parsed.chunk && onChunk) {
                            onChunk(parsed.chunk, false);
                        } else if (parsed.error && onChunk) {
                            onChunk(`⚠️ **Hata:** ${parsed.error}`, true);
                        }
                    } catch (e) {
                        // ignore parse errors
                    }
                }
            }
        }

    } catch (err) {
        if (onChunk) onChunk(`⚠️ **Hata:** ${err.message}`, true);
    }
}

// ═══════════════════════════════════════
// RETRY HANDLER
// ═══════════════════════════════════════
window.retryAnalysis = function(ticker) {
    if (!ticker) return;
    if (typeof showToast === "function") showToast(`${ticker} için analiz tekrarlanıyor...`, "info");
    
    const checkIslamic = document.getElementById("check-islamic-toggle")?.checked || false;
    const checkFinancials = document.getElementById("check-financials-toggle")?.checked || false;
    const aiToggle = document.getElementById("use-ai-toggle");
    const useAI = aiToggle ? aiToggle.checked : false;
    const apiKey = document.getElementById("api-key")?.value || "";
    const model = localStorage.getItem("ai_model") || "gemini-2.5-flash";

    runAnalysis({ 
        tickers: [ticker], 
        use_ai: useAI, 
        api_key: apiKey, 
        check_islamic: checkIslamic, 
        check_financials: checkFinancials,
        model: model 
    }, "/api/analyze");
};
