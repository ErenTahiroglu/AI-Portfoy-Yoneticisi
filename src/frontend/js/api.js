// ═══════════════════════════════════════
// AI WIZARD
// ═══════════════════════════════════════
async function runWizard() {
    const promptText = document.getElementById("wizard-input").value.trim();
    if (!promptText) { showToast(t("toast.enterTickers") || "Lütfen sihirbaza bir talimat yazın", "warning"); return; }

    const apiKey = document.getElementById("api-key").value;
    if (!apiKey) { showToast(t("toast.noApiKey") || "AI Sihirbazı için Gemini API Anahtarı gereklidir (Ayarlar)", "warning"); return; }

    const currModel = document.getElementById("model-select").value || "gemini-2.5-flash";
    const btn = document.getElementById("btn-run-wizard");
    const origText = btn.innerHTML;

    btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Sihirbaz Düşünüyor...`;
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/api/wizard`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: promptText, api_key: apiKey, model: currModel, lang: getLang() })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Makine öğrenimi servisi yanıt vermedi");

        if (data.portfolio && Array.isArray(data.portfolio)) {
            const tickerString = data.portfolio.map(p => `${p.ticker}:${p.weight}`).join(", ");
            document.getElementById("ticker-input").value = tickerString;
            showToast("Yapay Zeka portföyünüzü hazırladı! Analiz başlıyor...", "success");

            document.getElementById("ticker-input").scrollIntoView({ behavior: "smooth", block: "center" });

            setTimeout(() => {
                document.getElementById("analyze-btn").click();
            }, 800);
        } else {
            showToast("Geçerli bir portföy döndürülemedi.", "error");
        }
    } catch (err) {
        showToast(`Sihirbaz Hatası: ${err.message}`, "error");
    } finally {
        btn.innerHTML = origText;
        btn.disabled = false;
    }
}

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
async function loadNews(results) {
    const wrap = document.getElementById("news-wrap");
    const container = document.getElementById("news-container");

    // Sadece geçerli ticker listesi
    const tickers = results.filter(r => !r.error && r.ticker).map(r => r.ticker);
    if (tickers.length === 0) {
        wrap.classList.add("hidden");
        return;
    }

    wrap.classList.remove("hidden");
    container.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--text-muted);"><i class="fas fa-spinner fa-spin fa-2x" style="margin-bottom:1rem"></i><br>Yapay zeka haberleri tarayıp portföyünüz için en önemlilerini seçiyor...</div>`;

    let aKey = "";
    if (localStorage.getItem("settingsParams")) {
        try {
            const sp = JSON.parse(await decryptData(localStorage.getItem("settingsParams")));
            aKey = sp.geminiApiKey || "";
        } catch { }
    }
    const currModel = localStorage.getItem("ai_model") || "gemini-2.5-flash";

    try {
        const res = await fetch(`${API_BASE}/api/news`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tickers: tickers.slice(0, 5), api_key: aKey, model: currModel, lang: getLang() })
        });

        const data = await res.json();

        if (!data.news || data.news.length === 0) {
            container.innerHTML = `<div class="card" style="padding:1rem; text-align:center; color:var(--text-muted)">Portföydeki şirketler için kayda değer önemli bir haber bulunamadı.</div>`;
            return;
        }

        let html = "";
        data.news.forEach(item => {
            const title = item.title || "İsimsiz Haber";
            const link = item.link || "#";
            const sentiment = item.sentiment || "Neutral";
            const reason = item.reason || "";

            let color = "var(--text-muted)";
            let icon = "minus";
            if (sentiment.toLowerCase().includes("bull")) { color = "var(--success)"; icon = "arrow-trend-up"; }
            else if (sentiment.toLowerCase().includes("bear")) { color = "var(--danger)"; icon = "arrow-trend-down"; }

            html += `
            <a href="${link}" target="_blank" style="text-decoration:none; color:inherit; outline:none;">
                <div class="card" style="padding:1.2rem; background:var(--card-bg); border:1px solid var(--card-border); border-radius:var(--radius); transition:transform 0.2s, box-shadow 0.2s; cursor:pointer;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.4)'; this.style.borderColor='rgba(255,255,255,0.1)'" onmouseout="this.style.transform='none'; this.style.boxShadow='none'; this.style.borderColor='var(--card-border)'">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem;">
                        <h4 style="margin:0; font-size:1.05rem; line-height:1.4; color:var(--text-main); flex:1;">${title}</h4>
                        <span style="display:inline-flex; align-items:center; gap:0.4rem; padding:0.3rem 0.6rem; border-radius:1rem; font-size:0.75rem; font-weight:700; background:rgba(255,255,255,0.05); color:${color}">
                            <i class="fas fa-${icon}"></i> ${sentiment}
                        </span>
                    </div>
                    ${reason ? `<p style="margin:0.75rem 0 0 0; font-size:0.85rem; color:var(--text-muted); line-height:1.5;">${reason}</p>` : ""}
                </div>
            </a>`;
        });

        container.innerHTML = html;

    } catch (err) {
        container.innerHTML = `<div class="card" style="padding:1rem; color:var(--danger)">Haberler yüklenirken hata oluştu: ${err.message}</div>`;
    }
}

// ═══════════════════════════════════════
// EXPORT
// ═══════════════════════════════════════
async function exportResults(format) {
    if (!lastResults) { showToast(t("toast.noTickers"), "warning"); return; }
    showToast(`${format.toUpperCase()} ${t("toast.exporting")}`, "info");

    // Client-side Excel Export using SheetJS (XLSX)
    if (format === 'excel' && typeof XLSX !== 'undefined') {
        try {
            const rows = lastResults.map(res => {
                const fin = res.financials || {};
                const val = res.valuation || {};
                return {
                    "Hisse/Fon": res.ticker || "",
                    "Pazar": res.market || "",
                    "Durum": res.status || "-",
                    "Arındırma Oranı (%)": res.purification_ratio !== undefined ? res.purification_ratio : "-",
                    "Borçluluk Oranı (%)": res.debt_ratio !== undefined ? res.debt_ratio : "-",
                    "5Y Reel Getiri (%)": fin.s5 !== undefined ? fin.s5 : "-",
                    "3Y Reel Getiri (%)": fin.s3 !== undefined ? fin.s3 : "-",
                    "P/E": val.pe !== undefined ? val.pe : "-",
                    "P/B": val.pb !== undefined ? val.pb : "-",
                    "Beta": val.beta !== undefined ? val.beta : "-"
                };
            });

            const ws = XLSX.utils.json_to_sheet(rows);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, "Portföy Analizi");
            XLSX.writeFile(wb, "portfoy_analizi.xlsx");
            showToast(t("toast.exported"), "success");
            return;
        } catch (err) {
            console.error("XLSX Export Error:", err);
        }
    }

    try {
        const res = await fetch(`${API_BASE}/api/export/${format}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ results: lastResults, format }) });
        if (!res.ok) throw new Error("Export failed");
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `portfoy_analizi.${format === "excel" ? "xlsx" : format}`;
        document.body.appendChild(a); a.click(); a.remove();
        URL.revokeObjectURL(url);
        showToast(t("toast.exported"), "success");
    } catch (err) { showToast(`Export hatası: ${err.message}`, "error"); }
}

async function exportPortfolioImage() {
    const resultsElem = document.getElementById("results");
    if (!lastResults || lastResults.length === 0) { showToast(t("toast.noTickers"), "warning"); return; }

    showToast("Görsel hazırlanıyor...", "info");
    try {
        const canvas = await html2canvas(resultsElem, {
            scale: 2,
            backgroundColor: getComputedStyle(document.documentElement).getPropertyValue('--bg-body') || '#0f172a',
            ignoreElements: (el) => el.classList.contains('toolbar-actions') // Hide buttons in screenshot
        });

        const url = canvas.toDataURL("image/png");
        const a = document.createElement("a");
        a.href = url;
        a.download = `portfoy_analizi.png`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        showToast("Görsel indirildi!", "success");
    } catch (err) {
        console.error(err);
        showToast(`Görsel oluşturma hatası: ${err.message}`, "error");
    }
}

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

        tickers.forEach(t => {
            if (cachedItems.some(r => r.ticker === t)) return; // Skip cached ones
            const card = document.createElement("div");
            card.className = "result-card glass-panel skeleton-card";
            card.id = `skeleton-${t}`;
            card.innerHTML = `
                <div class="card-header"><span class="ticker-name">${t}</span></div>
                <div class="skeleton-line"></div>
                <div class="skeleton-line medium"></div>
                <div class="skeleton-line short"></div>
            `;
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
    if (results.length === 0) return null;

    const initialBalance = payload.initial_balance || 10000;
    const monthlyContribution = payload.monthly_contribution || 0;
    const rebalanceFreq = payload.rebalancing_freq || "none";

    const minLength = Math.min(...results.map(r => r.technicals.relative_performance.stock_history.length));
    if (minLength < 2) return null;

    const totalWeight = results.reduce((sum, r) => sum + (r.weight || 1.0), 0);
    const initialWeights = results.map(r => (r.weight || 1.0) / totalWeight);

    let currentBalance = initialBalance;
    const balanceHistory = [currentBalance];
    const drawdownSeries = [0];
    let maxBalance = currentBalance;
    let maxDrawdown = 0;

    for (let t = 1; t < minLength; t++) {
        let periodReturn = 0;
        results.forEach((r, idx) => {
            const hist = r.technicals.relative_performance.stock_history;
            const singleRet = (hist[t] / hist[t-1]) - 1;
            periodReturn += singleRet * initialWeights[idx];
        });

        currentBalance = currentBalance * (1 + periodReturn) + monthlyContribution;
        balanceHistory.push(currentBalance);

        if (currentBalance > maxBalance) maxBalance = currentBalance;
        const dd = maxBalance > 0 ? ((maxBalance - currentBalance) / maxBalance) * 100 : 0;
        drawdownSeries.push(-dd);
        if (dd > maxDrawdown) maxDrawdown = dd;
    }

    const finalBalance = currentBalance;
    const totalReturn = (finalBalance - (initialBalance + monthlyContribution * (minLength - 1))) / (initialBalance + monthlyContribution * (minLength - 1));
    const years = (minLength - 1) / 12; // Assuming monthly increments
    const cagr = years > 0 ? (Math.pow(1 + totalReturn, 1 / years) - 1) * 100 : 0;

    const periodReturns = [];
    for (let t = 1; t < balanceHistory.length; t++) {
        periodReturns.push((balanceHistory[t] / balanceHistory[t-1]) - 1);
    }
    const meanRet = periodReturns.reduce((a, b) => a + b, 0) / periodReturns.length;
    const downsideDiff = periodReturns.map(v => v < 0 ? Math.pow(v, 2) : 0);
    const downsideDev = Math.sqrt(downsideDiff.reduce((a, b) => a + b, 0) / periodReturns.length);
    const stdDev = Math.sqrt(periodReturns.map(v => Math.pow(v - meanRet, 2)).reduce((a, b) => a + b, 0) / periodReturns.length);

    const sharpe = stdDev > 0 ? (meanRet / stdDev) * Math.sqrt(12) : 0;
    const sortino = downsideDev > 0 ? (meanRet / downsideDev) * Math.sqrt(12) : 0;
    const calmar = maxDrawdown > 0 ? (cagr / maxDrawdown) : 0;

    return {
        metrics: {
            cagr: parseFloat(cagr.toFixed(1)),
            max_drawdown: parseFloat(maxDrawdown.toFixed(1)),
            sharpe: parseFloat(sharpe.toFixed(2)),
            sortino: parseFloat(sortino.toFixed(2)),
            calmar: parseFloat(calmar.toFixed(2)),
            drawdown_series: drawdownSeries
        },
        final_balance: Math.round(finalBalance)
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
        const response = await fetch(`${API_BASE}/api/analyze-macro`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
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
