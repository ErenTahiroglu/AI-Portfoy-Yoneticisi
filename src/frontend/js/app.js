// ═══════════════════════════════════════
// COMPARISON MODE
// ═══════════════════════════════════════
function showComparison() {
    if (!lastResults || lastResults.length < 2) { showToast(t("toast.compareMin"), "warning"); return; }
    const view = document.getElementById("comparison-view");
    const content = document.getElementById("comparison-content");
    view.classList.remove("hidden");
    const metrics = [
        ["Son Fiyat", r => r.financials?.son_fiyat?.fiyat?.toFixed(2) || "-"],
        ["Değişim", r => fmtNum(r.financials?.son_fiyat?.degisim, "%")],
        ["P/E", r => fmtNum(r.valuation?.pe)], ["P/B", r => fmtNum(r.valuation?.pb)],
        ["Beta", r => fmtNum(r.valuation?.beta)], ["Piyasa Değeri", r => formatMarketCap(r.valuation?.market_cap)],
        ["Temettü", r => fmtNum(r.valuation?.div_yield, "%")], ["EPS", r => fmtNum(r.valuation?.eps)],
        ["ROE", r => fmtNum(r.valuation?.roe, "%")], ["52H Yüksek", r => fmtNum(r.valuation?.high_52w)],
        ["52H Düşük", r => fmtNum(r.valuation?.low_52w)],
        ["RSI (14)", r => r.technicals?.rsi_14 !== undefined ? r.technicals.rsi_14 : "-"],
        ["MACD", r => r.technicals?.macd !== undefined ? r.technicals.macd : "-"],
        ["5Y Getiri", r => fmtNum(r.financials?.s5, "%")], ["3Y Getiri", r => fmtNum(r.financials?.s3, "%")],
        ["Sharpe", r => fmtNum(r.financials?.risk?.sharpe_ratio)], ["Max DD", r => fmtNum(r.financials?.risk?.max_drawdown, "%")],
        ["Sektör", r => r.sector || "-"],
    ];
    const tickers = lastResults.filter(r => !r.error);
    let html = `<table class="comparison-table"><thead><tr><th>Metrik</th>`;
    tickers.forEach(r => { html += `<th>${r.ticker}</th>`; });
    html += `</tr></thead><tbody>`;
    metrics.forEach(([label, fn]) => {
        const vals = tickers.map(fn);
        if (vals.every(v => v === "-")) return;
        html += `<tr><td>${label}</td>`;
        vals.forEach(v => { html += `<td>${v}</td>`; });
        html += `</tr>`;
    });
    html += `</tbody></table>`;
    content.innerHTML = html;
    view.scrollIntoView({ behavior: "smooth" });
}

// ═══════════════════════════════════════
// ═══════════════════════════════════════
// METRIC DETAILS & MODAL
// ═══════════════════════════════════════
const METRIC_DESCRIPTIONS = {
    pe: {
        tr: "Fiyat/Kazanç Oranı (P/E): Şirketin piyasa değerinin yıllık karına oranıdır. Şirketin her 1 TL'lik karı için piyasanın ne kadar ödemeye razı olduğunu gösterir. Düşük oran 'ucuz', yüksek oran 'büyüme beklentisi' veya 'pahalı' olarak yorumlanabilir.",
        en: "Price-to-Earnings Ratio (P/E): The ratio of a company's share price to its earnings per share. High P/E could mean that a stock's price is high relative to earnings and possibly overvalued. Conversely, a low P/E might indicate that the current stock price is low relative to earnings."
    },
    pb: {
        tr: "Piyasa Değeri/Defter Değeri (P/B): Şirketin piyasa değerinin, özsermayesine (net varlıklarına) oranıdır. 1'in altı genellikle şirketin varlıklarından daha ucuza satıldığını gösterir.",
        en: "Price-to-Book Ratio (P/B): Compares a firm's market capitalization to its book value. A P/B ratio under 1.0 is considered a good P/B value, indicating a potentially undervalued stock."
    },
    beta: {
        tr: "Beta: Hissenin piyasaya (endekse) göre oynaklığını ölçer. Beta > 1 ise hisse piyasadan daha hareketli, Beta < 1 ise daha durağandır. Risk iştahınıza göre kritik bir göstergedir.",
        en: "Beta: A measure of a stock's volatility in relation to the overall market. A beta greater than 1.0 suggests that the stock is more volatile than the market, while a beta less than 1.0 indicates it is less volatile."
    },
    sharpe: {
        tr: "Sharpe Oranı: Risk birimi başına elde edilen getiriyi ölçer. Oranın yüksek olması (özellikle 1 ve üzeri), alınan riskin karşılığının iyi bir getiriyle alındığını gösterir.",
        en: "Sharpe Ratio: Measures the performance of an investment compared to a risk-free asset, after adjusting for its risk. A higher Sharpe ratio is better."
    },
    max_dd: {
        tr: "Maximum Drawdown (Max DD): Bir varlığın zirve noktasından en dip noktasına kadar yaşadığı en büyük değer kaybıdır. Portföyün 'en kötü senaryoda' ne kadar düşebileceğini gösterir.",
        en: "Maximum Drawdown (Max DD): The maximum observed loss from a peak to a trough of a portfolio, before a new peak is attained. It's a key indicator of downside risk."
    },
    div: {
        tr: "Temettü Verimi: Şirketin dağıttığı temettünün hisse fiyatına oranıdır. Pasif gelir odaklı yatırımcılar için ana performans göstergesidir.",
        en: "Dividend Yield: A financial ratio that shows how much a company pays out in dividends each year relative to its stock price."
    },
    s5: {
        tr: "5 Yıllık Reel Getiri: Son 5 yıldaki toplam getirinin enflasyondan arındırılmış halidir. Paranızı enflasyona karşı ne kadar koruduğunuzu ve büyüttüğünüzü temsil eder.",
        en: "5-Year Real Return: The total return over the last 5 years adjusted for inflation. Represents how much you have grown your purchasing power."
    }
};

function openMetricModal(ticker, metricKey, label, aiCommentRaw) {
    const modal = document.getElementById("metric-modal");
    const title = document.getElementById("metric-detail-title");
    const tickerEl = document.getElementById("metric-detail-ticker");
    const desc = document.getElementById("metric-static-desc");
    const aiBox = document.getElementById("metric-ai-insight");

    title.textContent = label;
    tickerEl.textContent = ticker;

    const lang = getLang();
    desc.textContent = METRIC_DESCRIPTIONS[metricKey] ? METRIC_DESCRIPTIONS[metricKey][lang] : "Bu metrik hakkında detaylı bilgi bulunmuyor.";

    // Parse AI Insights from commentary
    let insight = "Bu metrik için yapay zeka analizi henüz hazır değil veya analiz sırasında üretilmedi.";
    if (aiCommentRaw) {
        const match = aiCommentRaw.match(/<!--METRIC_INSIGHTS:\s*([\s\S]*?)\s*-->/);
        if (match) {
            try {
                const insights = JSON.parse(match[1]);
                if (insights[metricKey]) insight = insights[metricKey];
            } catch (e) { console.error("JSON parse error for metric insights:", e); }
        }
    }

    aiBox.textContent = insight;
    modal.classList.remove("hidden");
}

// RENDER RESULTS
// ═══════════════════════════════════════
function renderResults(data) {
    const results = data.results || [];
    lastResults = results;
    lastExtras = data.extras || {};
    const resultsSection = document.getElementById("results");
    const grid = document.getElementById("results-grid");
    const summaryBody = document.getElementById("summary-table-body");
    resultsSection.classList.remove("hidden");
    grid.innerHTML = "";
    summaryBody.innerHTML = "";
    document.getElementById("comparison-view").classList.add("hidden");

    results.forEach((res, idx) => {
        const fin = res.financials || {};
        const val = res.valuation || {};
        const sonFiyat = fin.son_fiyat ? `${fin.son_fiyat.fiyat?.toFixed(2) || "-"}` : "-";
        const purRatio = res.purification_ratio !== undefined ? `%${res.purification_ratio}` : "-";

        let statusText = res.status || "-";
        if (getLang() === "en") {
            if (statusText === "Uygun") statusText = "Compliant";
            else if (statusText === "Uygun Değil") statusText = "Non-Compliant";
            else if (statusText === "Katılım Fonu Değil") statusText = "Non-Participation";
        }
        const statusClass = res.status === "Uygun" ? "status-approved" : (res.status === "Uygun Değil" || res.status === "Katılım Fonu Değil" ? "status-rejected" : "");

        // Summary row
        const summaryFullName = res.full_name || fin.ad || "";
        const tickerDisplay = summaryFullName ? `<div style="font-weight:700">${res.ticker}</div><div style="font-size:0.7rem; color:var(--text-muted)">${summaryFullName}</div>` : `<span style="font-weight:700">${res.ticker}</span>`;

        const tr = document.createElement("tr");
        let marketText = res.market || "?";
        if (getLang() === "tr" && marketText === "US") marketText = "ABD";

        tr.innerHTML = `<td>${tickerDisplay}</td><td><span class="market-badge">${marketText}</span></td><td>${res.weight || 1}</td><td>${sonFiyat}</td><td>${purRatio}</td><td>${statusText !== "-" ? `<span class="${statusClass}">${statusText}</span>` : "-"}</td><td>${fmtNum(val.pe)}</td><td>${fmtNum(val.pb)}</td><td>${fmtNum(val.beta)}</td>`;
        summaryBody.appendChild(tr);

        // Card
        const card = document.createElement("div");
        card.className = "result-card glass-panel stagger-enter stagger-" + ((idx % 5) + 1);
        const chartId = `chart-${idx}`;

        if (res.error) {
            card.innerHTML = `<div class="card-header"><span class="ticker-name">${res.ticker}</span><span class="market-badge">${res.market || "?"}</span></div>
            <p style="color:var(--danger);font-size:0.85rem;margin-bottom:0.75rem;">${res.error}</p>
            <button class="btn btn-outline" style="font-size:0.75rem; padding:0.3rem 0.6rem;" onclick="retryAnalysis('${res.ticker}')"><i class="fas fa-redo"></i> Yeniden Dene</button>`;
            grid.appendChild(card);
            return;
        }

        // Metrics
        let metricsHTML = "";
        const ticker = res.ticker;
        const aiRaw = res.ai_comment || "";

        function createMetricBox(label, value, key, classes = "") {
            return `<div class="metric-box ${classes}" onclick='openMetricModal("${ticker}", "${key}", "${label}", ${JSON.stringify(aiRaw)})'>
                <div class="metric-label">${label} <i class="fas fa-info-circle" style="font-size:0.65rem;opacity:0.6"></i></div>
                <div class="metric-value">${value}</div>
            </div>`;
        }

        if (val.pe) metricsHTML += createMetricBox("P/E", fmtNum(val.pe), "pe");
        if (val.pb) metricsHTML += createMetricBox("P/B", fmtNum(val.pb), "pb");
        if (val.beta) metricsHTML += createMetricBox("Beta", fmtNum(val.beta), "beta");
        if (val.market_cap) metricsHTML += `<div class="metric-box no-modal"><div class="metric-label">Piyasa Değeri</div><div class="metric-value">${formatMarketCap(val.market_cap)}</div></div>`;
        if (val.div_yield) metricsHTML += createMetricBox("Temettü", fmtNum(val.div_yield, "%"), "div");
        if (val.eps) metricsHTML += `<div class="metric-box no-modal"><div class="metric-label">EPS</div><div class="metric-value">${fmtNum(val.eps)}</div></div>`;
        if (val.roe) metricsHTML += `<div class="metric-box no-modal"><div class="metric-label">ROE</div><div class="metric-value">${fmtNum(val.roe, "%")}</div></div>`;
        if (val.high_52w) metricsHTML += `<div class="metric-box no-modal"><div class="metric-label">52H Yüksek</div><div class="metric-value">${fmtNum(val.high_52w)}</div></div>`;
        if (val.low_52w) metricsHTML += `<div class="metric-box no-modal"><div class="metric-label">52H Düşük</div><div class="metric-value">${fmtNum(val.low_52w)}</div></div>`;
        if (fin.risk) {
            if (fin.risk.sharpe_ratio !== null) metricsHTML += createMetricBox("Sharpe", fmtNum(fin.risk.sharpe_ratio), "sharpe", colorClass(fin.risk.sharpe_ratio));
            if (fin.risk.max_drawdown !== null) metricsHTML += createMetricBox("Max DD", fmtNum(fin.risk.max_drawdown, "%"), "max_dd", "negative");
        }
        if (fin.son_fiyat) {
            metricsHTML += `<div class="metric-box no-modal"><div class="metric-label">Son Fiyat</div><div class="metric-value">${fmtNum(fin.son_fiyat.fiyat)}</div></div>`;
            if (fin.son_fiyat.degisim !== undefined) metricsHTML += `<div class="metric-box no-modal"><div class="metric-label">Değişim</div><div class="metric-value ${colorClass(fin.son_fiyat.degisim)}">${fmtNum(fin.son_fiyat.degisim, "%")}</div></div>`;
        }
        if (fin.s5 !== null && fin.s5 !== undefined) metricsHTML += createMetricBox("5Y Getiri", fmtNum(fin.s5, "%"), "s5", colorClass(fin.s5));
        if (fin.s3 !== null && fin.s3 !== undefined) metricsHTML += `<div class="metric-box no-modal"><div class="metric-label">3Y Getiri</div><div class="metric-value ${colorClass(fin.s3)}">${fmtNum(fin.s3, "%")}</div></div>`;
        if (res.purification_ratio !== undefined) metricsHTML += `<div class="metric-box no-modal"><div class="metric-label">Arındırma</div><div class="metric-value">${fmtNum(res.purification_ratio, "%")}</div></div>`;
        if (res.debt_ratio !== undefined) metricsHTML += `<div class="metric-box no-modal"><div class="metric-label">Borçluluk</div><div class="metric-value">${fmtNum(res.debt_ratio, "%")}</div></div>`;

        // Sector badge
        let sectorLabel = res.sector_localized ? res.sector_localized[getLang()] : (res.sector || "Bilinmiyor");
        let sectorBadge = `<span class="market-badge" style="font-size:0.65rem">${sectorLabel}</span>`;

        // Technical indicators
        let techHTML = renderTechnicals(res.technicals);

        // Return table
        let returnTableHTML = "";
        if (fin.ay && Object.keys(fin.ay).length > 0) {
            let rows = "";
            for (const [ay, d] of Object.entries(fin.ay)) {
                rows += `<tr><td>Son ${ay} ay</td><td class="${colorClass(d.g)}">${fmtNum(d.g, "%")}</td><td class="${colorClass(d.r)}">${fmtNum(d.r, "%")}</td><td>${fmtNum(d.enf, "%")}</td></tr>`;
            }
            returnTableHTML = `<div class="collapsible-header" onclick="toggleCollapsible(this)"><h4><i class="fas fa-chart-bar"></i> ${t("card.returns")}</h4><i class="fas fa-chevron-down collapse-icon"></i></div><div class="collapsible-body"><table class="return-table"><thead><tr><th>Dönem</th><th>Getiri</th><th>Reel</th><th>Enflasyon</th></tr></thead><tbody>${rows}</tbody></table></div>`;
        }

        // Chart
        let chartHTML = "";
        if (fin.yg && Object.keys(fin.yg).length > 0) {
            chartHTML = `<div class="collapsible-header open" onclick="toggleCollapsible(this)"><h4><i class="fas fa-chart-line"></i> ${t("card.chart")}</h4><i class="fas fa-chevron-down collapse-icon"></i></div><div class="collapsible-body open"><div class="chart-container"><canvas id="${chartId}"></canvas></div></div>`;
        }

        // AI
        let aiHTML = "";
        if (res.ai_comment) {
            aiHTML = `<div class="collapsible-header" onclick="toggleCollapsible(this)"><h4><i class="fas fa-robot"></i> ${t("card.ai")}</h4><i class="fas fa-chevron-down collapse-icon"></i></div><div class="collapsible-body"><div class="ai-content markdown-body">${marked.parse(res.ai_comment)}</div></div>`;
        }

        // Fund info
        let fundHTML = res.fund_note ? `<p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:0.75rem">${res.fund_note}</p>` : "";
        let errHTML = res.islamic_error ? `<p style="font-size:0.78rem; color:var(--warning); margin:0.5rem 0"><i class="fas fa-exclamation-triangle"></i> ${res.islamic_error}</p>` : "";
        errHTML += res.fin_error ? `<p style="font-size:0.78rem; color:var(--warning); margin:0.5rem 0"><i class="fas fa-exclamation-triangle"></i> ${res.fin_error}</p>` : "";

        let statusBadgeFinal = statusText !== "-" ? `<span class="${statusClass}">${statusText}</span>` : "";

        const fullName = res.full_name || fin.ad || "";
        const nameBadge = (fullName && fullName !== res.ticker) ? `<span style="font-size:0.85rem; color:var(--text-muted); margin-left:0.5rem; font-weight:normal">${fullName}</span>` : "";

        card.innerHTML = `
            <div class="card-header">
                <div><span class="ticker-name">${res.ticker}</span>${nameBadge}</div>
                <div style="display:flex; align-items:center; gap:0.5rem"><span class="market-badge">${marketText}</span>${sectorBadge}${statusBadgeFinal}</div>
            </div>
            ${fundHTML}${errHTML}
            ${metricsHTML ? `<div class="metrics-grid">${metricsHTML}</div>` : ""}
            ${techHTML}
            ${chartHTML}
            ${returnTableHTML}
            ${aiHTML}
        `;
        grid.appendChild(card);
        if (fin.yg && Object.keys(fin.yg).length > 0) setTimeout(() => createReturnChart(chartId, fin), 50);
    });

    // Render portfolio-level extras with error guards
    try {
        const scoreBadge = document.getElementById("portfolio-score-badge");
        const scoreVal = document.getElementById("weighted-return-val");
        if (lastExtras && lastExtras.weighted_return_5y !== undefined) {
            scoreVal.textContent = lastExtras.weighted_return_5y;
            scoreBadge.classList.remove("hidden");
        } else {
            scoreBadge.classList.add("hidden");
        }
    } catch (e) { console.error("Score badge error:", e); }

    try { renderExtras(lastExtras); } catch (e) { console.error("Extras error:", e); }
    try { updateHeroCards(results, lastExtras); } catch (e) { console.error("Hero cards error:", e); }
    try { renderHeatmap(results); } catch (e) { console.error("Heatmap error:", e); }
    try { renderScenarios(results); } catch (e) { console.error("Scenarios error:", e); }

    try {
        if (lastExtras && lastExtras.optimized_weights) {
            renderOptimization(lastExtras.optimized_weights, results);
        } else {
            document.getElementById("optimization-wrap").classList.add("hidden");
        }
    } catch (e) { console.error("Optimization error:", e); }

    // Load News async so it doesn't block rendering
    try { loadNews(results); } catch (e) { console.error("News load error:", e); }

    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ═══════════════════════════════════════
// RETRY ANALYSIS
// ═══════════════════════════════════════
window.retryAnalysis = async function (ticker) {
    const checkIslamic = document.getElementById("check-islamic-toggle").checked;
    const checkFinancials = document.getElementById("check-financials-toggle").checked;
    const useAI = document.getElementById("use-ai-toggle").checked;
    const apiKey = document.getElementById("api-key").value;
    const avKey = document.getElementById("av-api-key").value;
    const model = document.getElementById("model-select").value;

    const payload = {
        tickers: [ticker],
        use_ai: useAI,
        api_key: apiKey,
        av_api_key: avKey,
        model: model,
        check_islamic: checkIslamic,
        check_financials: checkFinancials,
        lang: getLang(),
        initial_balance: parseFloat(document.getElementById("sim-initial-balance").value) || 10000,
        monthly_contribution: parseFloat(document.getElementById("sim-monthly-contribution").value) || 0,
        rebalancing_freq: document.getElementById("sim-rebalance-freq").value || "none"
    };

    showToast(`${ticker} analiz ediliyor...`, "info");
    try {
        const res = await fetch(`${API_BASE}/api/analyze`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        if (!res.ok) throw new Error("Sunucu hatası");
        const data = await res.json();
        const newResult = data.results[0];

        const idx = lastResults.findIndex(r => r.ticker === ticker);
        if (idx !== -1) {
            lastResults[idx] = newResult;
        } else {
            lastResults.push(newResult);
        }

        renderResults({ results: lastResults, extras: lastExtras });
        showToast(`${ticker} analizi yenilendi!`, "success");
    } catch (err) {
        showToast(`${ticker} hatası: ${err.message}`, "error");
    }
}

// ═══════════════════════════════════════
// DOM READY
// ═══════════════════════════════════════
document.addEventListener("DOMContentLoaded", async () => {
    initTheme();
    setLanguage(currentLang);
    await loadApiKeys();

    // Theme toggle
    document.getElementById("theme-toggle-btn").addEventListener("click", toggleTheme);
    document.getElementById("metric-modal-close").addEventListener("click", () => document.getElementById("metric-modal").classList.add("hidden"));
    window.addEventListener("click", (e) => {
        if (e.target === document.getElementById("metric-modal")) document.getElementById("metric-modal").classList.add("hidden");
    });

    // AI settings toggle
    const aiToggle = document.getElementById("use-ai-toggle");
    const apiKeyInput = document.getElementById("api-key");
    const modelSelect = document.getElementById("model-select");
    const geminiKeyGroup = document.getElementById("gemini-key-group");
    const geminiModelGroup = document.getElementById("gemini-model-group");
    const aiNote = document.getElementById("ai-note");

    const toggleAIVisibility = () => {
        const isAIEnabled = aiToggle.checked;
        apiKeyInput.disabled = !isAIEnabled;
        modelSelect.disabled = !isAIEnabled;

        if (isAIEnabled) {
            geminiKeyGroup.classList.remove("disabled");
            geminiModelGroup.classList.remove("disabled");
            aiNote.classList.remove("disabled");
        } else {
            geminiKeyGroup.classList.add("disabled");
            geminiModelGroup.classList.add("disabled");
            aiNote.classList.add("disabled");
        }
    };
    aiToggle.addEventListener("change", toggleAIVisibility);
    toggleAIVisibility();

    // Auto-save API keys
    document.getElementById("api-key").addEventListener("blur", saveApiKeys);
    document.getElementById("av-api-key").addEventListener("blur", saveApiKeys);

    // Professional Mode
    const profToggle = document.getElementById("prof-mode-toggle");
    if(profToggle) {
        profToggle.addEventListener("change", (e) => {
            if(e.target.checked) document.body.classList.add("professional-mode");
            else document.body.classList.remove("professional-mode");
        });
    }

    // Mobile menu
    const menuBtn = document.getElementById("mobile-menu-btn");
    const sidebar = document.getElementById("sidebar");
    menuBtn.addEventListener("click", () => sidebar.classList.toggle("open"));
    document.addEventListener("click", (e) => { if (sidebar.classList.contains("open") && !sidebar.contains(e.target) && !menuBtn.contains(e.target)) sidebar.classList.remove("open"); });

    // File upload
    const fileInput = document.getElementById("file-input");
    const dropArea = document.getElementById("file-drop-area");
    const fileNameDisplay = document.getElementById("file-name-display");
    const selectedFileName = document.getElementById("selected-file-name");
    const removeFileBtn = document.getElementById("remove-file-btn");
    dropArea.addEventListener("click", () => fileInput.click());
    dropArea.addEventListener("dragover", (e) => { e.preventDefault(); dropArea.classList.add("dragover"); });
    dropArea.addEventListener("dragleave", () => dropArea.classList.remove("dragover"));
    dropArea.addEventListener("drop", (e) => { e.preventDefault(); dropArea.classList.remove("dragover"); if (e.dataTransfer.files.length > 0) { fileInput.files = e.dataTransfer.files; showFile(e.dataTransfer.files[0]); } });
    fileInput.addEventListener("change", () => { if (fileInput.files[0]) showFile(fileInput.files[0]); });
    function showFile(file) { selectedFileName.textContent = file.name; fileNameDisplay.classList.remove("hidden"); dropArea.classList.add("hidden"); }
    removeFileBtn.addEventListener("click", () => { fileInput.value = ""; fileNameDisplay.classList.add("hidden"); dropArea.classList.remove("hidden"); });

    // Analyze & Wizard buttons
    document.getElementById("btn-run-wizard").addEventListener("click", runWizard);

    const analyzeBtn = document.getElementById("analyze-btn");
    analyzeBtn.addEventListener("click", () => {
        const checkIslamic = document.getElementById("check-islamic-toggle").checked;
        const checkFinancials = document.getElementById("check-financials-toggle").checked;
        const useAI = aiToggle.checked;
        const apiKey = document.getElementById("api-key").value;
        const avKey = document.getElementById("av-api-key").value;
        const model = document.getElementById("model-select").value;
        if (!checkIslamic && !checkFinancials) { showToast(t("toast.noAnalysis"), "warning"); return; }
        if (useAI && !apiKey) { showToast(t("toast.noApiKey"), "warning"); return; }
        if (fileInput.files[0]) { runFileAnalysis(fileInput.files[0]); return; }
        const text = document.getElementById("ticker-input").value.trim();
        if (!text) { showToast(t("toast.noTickers"), "warning"); return; }
        const tickers = text.split(/[\s,;]+/).filter(t => t.length > 0).map(t => t.toUpperCase());
        
        const initBal = parseFloat(document.getElementById("sim-initial-balance").value) || 10000;
        const moCont = parseFloat(document.getElementById("sim-monthly-contribution").value) || 0;
        const rebFreq = document.getElementById("sim-rebalance-freq").value || "none";

        runAnalysis({ tickers, use_ai: useAI, api_key: apiKey, av_api_key: avKey, model, check_islamic: checkIslamic, check_financials: checkFinancials, lang: getLang(), initial_balance: initBal, monthly_contribution: moCont, rebalancing_freq: rebFreq }, "/api/analyze");
    });

    // Enter key triggers analysis
    const tickerInput = document.getElementById("ticker-input");
    tickerInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            analyzeBtn.click();
        }
    });

    // Export & Compare
    document.getElementById("share-btn").addEventListener("click", exportPortfolioImage);
    document.getElementById("export-excel-btn").addEventListener("click", () => exportResults("excel"));
    document.getElementById("export-pdf-btn").addEventListener("click", () => exportResults("pdf"));
    document.getElementById("export-docx-btn").addEventListener("click", () => exportResults("docx"));
    document.getElementById("compare-btn").addEventListener("click", showComparison);

    // Watchlist
    document.getElementById("save-portfolio-btn").addEventListener("click", saveCurrentPortfolio);
    renderWatchlists();

    // Autocomplete
    setupAutocomplete();

    // Tabs Navigation
    const tabBtns = document.querySelectorAll(".tabs-nav .tab-btn");
    const tabContents = document.querySelectorAll(".input-tabs-container .tab-content");
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => {
                b.classList.remove("active");
                b.style.borderColor = "var(--glass-border)";
                b.style.background = "var(--card-bg)";
                b.style.color = "var(--text-muted)";
            });
            tabContents.forEach(c => c.classList.add("hidden"));

            btn.classList.add("active");
            btn.style.borderColor = "var(--primary)";
            btn.style.background = "var(--primary-glow)";
            btn.style.color = "var(--text-main)";

            const targetId = btn.getAttribute("data-target");
            const targetContent = document.getElementById(targetId);
            if (targetContent) targetContent.classList.remove("hidden");
        });
    });
});
