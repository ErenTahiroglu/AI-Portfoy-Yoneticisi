/**
 * 📡 API Service - Main Network & Analytics Orchestrator
 * ====================================================
 * Features:
 * - Uses HttpClient for resilient networking
 * - Delegates heavy math to Web Worker (Zero-Copy)
 * - Managed Caching (IndexedDB)
 */

import { http } from './HttpClient.js';
import { MathEngine } from '../core/MathEngine.js';

// ── Web Worker Management ──
let analyticsWorker = null;

function getWorker() {
    if (!analyticsWorker) {
        // Create worker as an ES Module
        analyticsWorker = new Worker(new URL('../worker.js', import.meta.url), { type: 'module' });
    }
    return analyticsWorker;
}

/**
 * Communicates with Worker using a Promise-based wrapper and terminates it after use.
 */
function runWorkerTask(type, results, payload) {
    return new Promise((resolve, reject) => {
        const worker = getWorker();
        
        const handler = (e) => {
            if (e.data.type === 'EXTRAS_RESULT') {
                worker.removeEventListener('message', handler);
                worker.terminate();
                analyticsWorker = null; // Reset for next time
                resolve(e.data.extras);
            } else if (e.data.type === 'ERROR') {
                worker.removeEventListener('message', handler);
                worker.terminate();
                analyticsWorker = null; // Reset for next time
                reject(new Error(e.data.message));
            }
        };

        worker.addEventListener('message', handler);
        worker.postMessage({ type, results, payload });
    });
}

// ═══════════════════════════════════════
// ASYNC JOB POLLING ENGINE
// ═══════════════════════════════════════
export async function pollJobResult(jobId, pollingInterval = 3000) {
    if (!jobId) throw new Error("Job ID eksik");
    
    let attempts = 0;
    const maxAttempts = 40; 
    
    while (attempts < maxAttempts) {
        attempts++;
        try {
            const data = await http.get(`/api/status/${jobId}`);
            
            if (data.status === "COMPLETED") return data.result;
            if (data.status === "ERROR") throw new Error(data.error || "Arkaplan görevinde sunucu hatası.");
            
            // PENDING or RUNNING -> Wait
            await new Promise(r => setTimeout(r, pollingInterval));
        } catch (err) {
            if (err.status === 404) throw new Error("Arkaplan görevi zaman aşımına uğradı veya bulunamadı.");
            console.warn("[Polling API Error]", err);
            await new Promise(r => setTimeout(r, pollingInterval));
        }
    }
    throw new Error("Zaman aşımı: Sunucu görevi belirtilen sürede (2dk) tamamlayamadı.");
}
window.pollJobResult = pollJobResult;

// ═══════════════════════════════════════
// HEALTH CHECK
// ═══════════════════════════════════════
export async function checkServerHealth() {
    try {
        const data = await http.get('/api/health');
        return { online: true, message: data.message };
    } catch (e) {
        return { online: false, message: e.message || "Sunucuya ulaşılamıyor." };
    }
}
window.checkServerHealth = checkServerHealth;

// ═══════════════════════════════════════
// MAIN ANALYSIS (Streaming & Caching)
// ═══════════════════════════════════════
export async function runAnalysis(payload, endpoint) {
    const macroPanel = document.getElementById("macro-advice-container");
    if (macroPanel) macroPanel.remove();

    const btn = document.getElementById("analyze-btn");
    const progressContainer = document.getElementById("progress-container");
    const progressFill = document.getElementById("progress-fill");
    const progressText = document.getElementById("progress-text");
    const resultsSection = document.getElementById("results");

    if (btn) btn.disabled = true; 
    if (resultsSection) resultsSection.classList.add("hidden");
    if (progressContainer) progressContainer.classList.remove("hidden");

    if (progressFill) progressFill.style.width = "0%";
    if (progressText) progressText.textContent = getLang() === "en" ? "Checking cache..." : "Önbellek kontrol ediliyor...";

    // Reset AppState results for a new analysis
    if (typeof AppState !== 'undefined') {
        AppState.results = [];
        AppState.extras = null;
    }

    let isConflict = false;
    try {
        const tickers = payload.tickers || [];
        const tickersToFetch = [];
        const cachedItems = [];

        let sseBuffer = [];
        let animationFrameId = null;

        const triggerBatchUpdate = () => {
            if (animationFrameId) return;
            animationFrameId = requestAnimationFrame(async () => {
                if (sseBuffer.length > 0) {
                    const batch = [...sseBuffer];
                    sseBuffer = [];
                    
                    for (const item of batch) {
                        if (typeof renderSingleCard === "function") renderSingleCard(item);
                        if (!item._fromCache && typeof setCache === 'function') {
                            const cacheKey = `analysis_${item.ticker}_ai${payload.use_ai}_isl${payload.check_islamic}_fin${payload.check_financials}_mod${payload.use_ai ? payload.model : 'none'}`;
                            await setCache(cacheKey, item);
                        }
                    }

                    if (typeof AppState !== 'undefined') AppState.results = [...AppState.results, ...batch];

                    const lastItem = batch[batch.length - 1];
                    if (progressText) progressText.textContent = `${lastItem.ticker} ${getLang() === "en" ? "analyzed." : "analiz edildi."}`;
                    if (typeof AppState !== 'undefined' && progressFill) {
                        const progress = (AppState.results.length / tickers.length) * 100;
                        progressFill.style.width = `${Math.min(progress, 100)}%`;
                    }
                }
                animationFrameId = null;
                if (sseBuffer.length > 0) triggerBatchUpdate(); 
            });
        };

        // 1. Cache Check
        for (const ticker of tickers) {
            const cleanTicker = ticker.trim().toUpperCase();
            if (!cleanTicker) continue;
            const cacheKey = `analysis_${cleanTicker}_ai${payload.use_ai}_isl${payload.check_islamic}_fin${payload.check_financials}_mod${payload.use_ai ? payload.model : 'none'}`;
            const cachedData = typeof getCache === 'function' ? await getCache(cacheKey) : null;
            if (cachedData) {
                cachedData._fromCache = true;
                cachedItems.push(cachedData);
            } else {
                tickersToFetch.push(cleanTicker);
            }
        }

        if (cachedItems.length > 0) {
            sseBuffer.push(...cachedItems);
            triggerBatchUpdate();
        }

        const grid = document.getElementById("results-grid");
        if (resultsSection) resultsSection.classList.remove("hidden");
        if (grid) grid.innerHTML = "";

        if (tickersToFetch.length > 0) {
            const { createSkeletonCard } = await import('../components/CardComponent.js');
            tickers.forEach(t => {
                if (cachedItems.some(r => r.ticker === t)) return;
                if (grid) grid.appendChild(createSkeletonCard(t));
            });

            if (progressText) progressText.textContent = getLang() === "en" ? "Streaming from server..." : "Sunucudan akış bekleniyor...";
            
            const response = await http.post(endpoint, { ...payload, tickers: tickersToFetch });
            
            // HttpClient returns the raw response if it's a stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            for (;;) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value);
                const lines = buffer.split("\n\n");
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        try {
                            const item = JSON.parse(line.substring(6));
                            if (item.ticker) {
                                sseBuffer.push(item);
                                triggerBatchUpdate();
                            }
                        } catch (e) { /* ignore parse errors */ }
                    }
                }
            }

            while (sseBuffer.length > 0 || animationFrameId) {
                await new Promise(r => setTimeout(r, 50));
            }
        }

        if (progressFill) progressFill.style.width = "100%"; 
        if (progressText) progressText.textContent = getLang() === "en" ? "Done!" : "Tamamlandı!";
        if (progressContainer) setTimeout(() => progressContainer.classList.add("hidden"), 500);

        // 2. Delegate Heavy Math to Worker
        if (typeof AppState !== 'undefined') {
            const extras = await runWorkerTask('CALCULATE_EXTRAS', AppState.results, payload);
            
            // Add non-math extras (like sector distribution) in main thread if needed
            extras.sector_distribution = calculateSectorDistribution(AppState.results);
            extras.weighted_return_5y = calculateWeightedReturn(AppState.results);

            AppState.extras = extras; 
            showToast(`${AppState.results.length} ${t("toast.analysisComplete")}`, "success");
        }

        if (typeof renderMacroAI === "function") runMacroAnalysis(renderMacroAI);

    } catch (err) {
        if (err.status === 409) {
            isConflict = true;
            console.log("⚡ [Idempotency] İşlem sunucuda devam ediyor (409). Arka planda bekleniyor...");
            if (progressText) progressText.textContent = getLang() === "en" ? "Processing in background..." : "Arka planda işleniyor...";
            if (typeof AppState !== 'undefined') AppState.systemStatus = 'syncing';
            
            // Poll after 5 seconds by re-running the same analysis (it will hit cache or retry if still processing)
            setTimeout(() => {
                runAnalysis(payload, endpoint, btn);
            }, 5000);
            return; // Exit here so we don't enable the button or hide progress
        }

        if (progressContainer) progressContainer.classList.add("hidden");
        console.error("Analysis Error:", err);
        showToast(err.message || "Bağlantı hatası", "error");
    } finally {
        if (btn && !isConflict) {
            btn.disabled = false;
        }
    }
}
window.runAnalysis = runAnalysis;

// ── Helper Math Functions (Non-blocking) ──

function calculateSectorDistribution(results) {
    const dist = {};
    results.forEach(r => {
        if (r.error) return;
        const sector = r.sector_localized ? r.sector_localized[getLang() === 'en' ? 'en' : 'tr'] : r.sector || (getLang() === 'en' ? "Unknown" : "Bilinmiyor");
        dist[sector] = (dist[sector] || 0) + 1;
    });
    return dist;
}

function calculateWeightedReturn(results) {
    let totalWeight = 0, weightedSum = 0;
    results.forEach(r => {
        if (r.error) return;
        const w = r.weight || 1.0;
        const ret = r.financials?.s5 || 0;
        weightedSum += ret * w;
        totalWeight += w;
    });
    return totalWeight > 0 ? MathEngine.round(weightedSum / totalWeight, 1) : 0;
}

// ═══════════════════════════════════════
// MACRO AI ANALYSIS (SSE)
// ═══════════════════════════════════════
export async function runMacroAnalysis(onChunk) {
    const apiKey = document.getElementById("api-key")?.value || "";
    if (!apiKey) {
        if (onChunk) onChunk("⚠️ Gemini API Anahtarı eksik.", true);
        return;
    }

    const portfolioData = {
        results: AppState.results.map(r => ({
            ticker: r.ticker, weight: r.weight || 1, sector: r.sector,
            financials: r.financials ? { son_fiyat: r.financials.son_fiyat, s5: r.financials.s5 } : null,
            valuation: r.valuation ? { pe: r.valuation.pe, pb: r.valuation.pb } : null
        })),
        extras: AppState.extras
    };

    try {
        const response = await http.post('/api/analyze-macro', {
            portfolio: portfolioData, api_key: apiKey,
            model: document.getElementById("model-select")?.value || "gemini-2.5-flash",
            lang: getLang()
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        for (;;) {
            const { value, done } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value);
            const lines = buffer.split("\n\n");
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    const dataStr = line.substring(6).trim();
                    if (dataStr === "[DONE]") { if (onChunk) onChunk(null, true); break; }
                    try {
                        const parsed = JSON.parse(dataStr);
                        if (parsed.chunk && onChunk) onChunk(parsed.chunk, false);
                        else if (parsed.error && onChunk) onChunk(`⚠️ **Hata:** ${parsed.error}`, true);
                    } catch (e) {
                        console.warn("Sessiz hata:", e);
                    }
                }
            }
        }
    } catch (err) {
        if (onChunk) onChunk(`⚠️ **Hata:** ${err.message}`, true);
    }
}
window.runMacroAnalysis = runMacroAnalysis;

// ═══════════════════════════════════════
// FILE ANALYSIS
// ═══════════════════════════════════════
export async function runFileAnalysis(file) {
    if (!file) return;
    showToast(getLang() === "en" ? "Parsing file..." : "Dosya okunuyor...", "info");

    const reader = new FileReader();
    const extension = file.name.split('.').pop().toLowerCase();

    reader.onload = function(e) {
        let tickers = [];
        try {
            if (extension === 'xlsx' || extension === 'xls') {
                const data = new Uint8Array(e.target.result);
                const workbook = XLSX.read(data, { type: 'array' });
                const csv = XLSX.utils.sheet_to_csv(workbook.Sheets[workbook.SheetNames[0]]);
                tickers = extractTickersFromCsv(csv);
            } else {
                tickers = extractTickersFromCsv(e.target.result);
            }

            if (tickers.length === 0) return showToast("Geçerli sembol bulunamadı.", "warning");

            document.getElementById("ticker-input").value = tickers.join(", ");
            runAnalysis({
                tickers,
                use_ai: document.getElementById("use-ai-toggle")?.checked || false,
                check_islamic: document.getElementById("check-islamic-toggle")?.checked || false,
                check_financials: document.getElementById("check-financials-toggle")?.checked || false,
                model: document.getElementById("model-select")?.value || "gemini-2.5-flash",
                lang: getLang()
            }, "/api/analyze");

        } catch (err) {
            showToast(`Dosya hatası: ${err.message}`, "error");
        }
    };

    if (extension === 'xlsx' || extension === 'xls') reader.readAsArrayBuffer(file);
    else reader.readAsText(file);
}
window.runFileAnalysis = runFileAnalysis;

function extractTickersFromCsv(text) {
    const matches = text.match(/[A-Z]+(\.[A-Z]+)?(:[0-9.]+)?/g);
    return matches ? [...new Set(matches.filter(m => m.length >= 2))] : [];
}

// ═══════════════════════════════════════
// RETRY HANDLER
// ═══════════════════════════════════════
window.retryAnalysis = function(ticker) {
    if (!ticker) return;
    runAnalysis({ 
        tickers: [ticker], 
        use_ai: document.getElementById("use-ai-toggle")?.checked || false, 
        api_key: document.getElementById("api-key")?.value || "", 
        model: localStorage.getItem("ai_model") || "gemini-2.5-flash" 
    }, "/api/analyze");
};
