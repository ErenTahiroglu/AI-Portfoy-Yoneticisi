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
        const statusClass = res.status === "Uygun" ? "status-approved" : (res.status === "Uygun Değil" ? "status-rejected" : "");
        const statusText = res.status || "-";

        // Summary row
        const tr = document.createElement("tr");
        tr.innerHTML = `<td style="font-weight:700">${res.ticker}</td><td><span class="market-badge">${res.market || "?"}</span></td><td>${res.weight || 1}</td><td>${sonFiyat}</td><td>${purRatio}</td><td>${statusText !== "-" ? `<span class="${statusClass}">${statusText}</span>` : "-"}</td><td>${fmtNum(val.pe)}</td><td>${fmtNum(val.pb)}</td><td>${fmtNum(val.beta)}</td>`;
        summaryBody.appendChild(tr);

        // Card
        const card = document.createElement("div");
        card.className = "result-card";
        const chartId = `chart-${idx}`;

        if (res.error) {
            card.innerHTML = `<div class="card-header"><span class="ticker-name">${res.ticker}</span><span class="market-badge">${res.market || "?"}</span></div><p style="color:var(--danger);font-size:0.85rem">${res.error}</p>`;
            grid.appendChild(card);
            return;
        }

        // Metrics
        let metricsHTML = "";
        if (val.pe) metricsHTML += `<div class="metric-box"><div class="metric-label">P/E</div><div class="metric-value">${fmtNum(val.pe)}</div></div>`;
        if (val.pb) metricsHTML += `<div class="metric-box"><div class="metric-label">P/B</div><div class="metric-value">${fmtNum(val.pb)}</div></div>`;
        if (val.beta) metricsHTML += `<div class="metric-box"><div class="metric-label">Beta</div><div class="metric-value">${fmtNum(val.beta)}</div></div>`;
        if (val.market_cap) metricsHTML += `<div class="metric-box"><div class="metric-label">Piyasa Değeri</div><div class="metric-value">${formatMarketCap(val.market_cap)}</div></div>`;
        if (val.div_yield) metricsHTML += `<div class="metric-box"><div class="metric-label">Temettü</div><div class="metric-value">${fmtNum(val.div_yield, "%")}</div></div>`;
        if (val.eps) metricsHTML += `<div class="metric-box"><div class="metric-label">EPS</div><div class="metric-value">${fmtNum(val.eps)}</div></div>`;
        if (val.roe) metricsHTML += `<div class="metric-box"><div class="metric-label">ROE</div><div class="metric-value">${fmtNum(val.roe, "%")}</div></div>`;
        if (val.high_52w) metricsHTML += `<div class="metric-box"><div class="metric-label">52H Yüksek</div><div class="metric-value">${fmtNum(val.high_52w)}</div></div>`;
        if (val.low_52w) metricsHTML += `<div class="metric-box"><div class="metric-label">52H Düşük</div><div class="metric-value">${fmtNum(val.low_52w)}</div></div>`;
        if (fin.risk) {
            if (fin.risk.sharpe_ratio !== null) metricsHTML += `<div class="metric-box"><div class="metric-label">Sharpe</div><div class="metric-value ${colorClass(fin.risk.sharpe_ratio)}">${fmtNum(fin.risk.sharpe_ratio)}</div></div>`;
            if (fin.risk.max_drawdown !== null) metricsHTML += `<div class="metric-box"><div class="metric-label">Max DD</div><div class="metric-value negative">${fmtNum(fin.risk.max_drawdown, "%")}</div></div>`;
        }
        if (fin.son_fiyat) {
            metricsHTML += `<div class="metric-box"><div class="metric-label">Son Fiyat</div><div class="metric-value">${fmtNum(fin.son_fiyat.fiyat)}</div></div>`;
            if (fin.son_fiyat.degisim !== undefined) metricsHTML += `<div class="metric-box"><div class="metric-label">Değişim</div><div class="metric-value ${colorClass(fin.son_fiyat.degisim)}">${fmtNum(fin.son_fiyat.degisim, "%")}</div></div>`;
        }
        if (fin.s5 !== null && fin.s5 !== undefined) metricsHTML += `<div class="metric-box"><div class="metric-label">5Y Getiri</div><div class="metric-value ${colorClass(fin.s5)}">${fmtNum(fin.s5, "%")}</div></div>`;
        if (fin.s3 !== null && fin.s3 !== undefined) metricsHTML += `<div class="metric-box"><div class="metric-label">3Y Getiri</div><div class="metric-value ${colorClass(fin.s3)}">${fmtNum(fin.s3, "%")}</div></div>`;
        if (res.purification_ratio !== undefined) metricsHTML += `<div class="metric-box"><div class="metric-label">Arındırma</div><div class="metric-value">${fmtNum(res.purification_ratio, "%")}</div></div>`;
        if (res.debt_ratio !== undefined) metricsHTML += `<div class="metric-box"><div class="metric-label">Borçluluk</div><div class="metric-value">${fmtNum(res.debt_ratio, "%")}</div></div>`;

        // Sector badge
        let sectorBadge = res.sector ? `<span class="market-badge" style="font-size:0.65rem">${res.sector}</span>` : "";

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

        let statusBadge = res.status ? `<span class="${res.status === "Uygun" ? "status-approved" : (res.status === "Uygun Değil" || res.status === "Katılım Fonu Değil" ? "status-rejected" : "")}">${res.status}</span>` : "";

        card.innerHTML = `
            <div class="card-header">
                <div><span class="ticker-name">${res.ticker}</span>${fin.ad && fin.ad !== res.ticker ? `<span style="font-size:0.75rem; color:var(--text-muted); margin-left:0.5rem">${fin.ad}</span>` : ""}</div>
                <div style="display:flex; align-items:center; gap:0.5rem"><span class="market-badge">${res.market || "?"}</span>${sectorBadge}${statusBadge}</div>
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

    // Render portfolio-level extras
    const scoreBadge = document.getElementById("portfolio-score-badge");
    const scoreVal = document.getElementById("weighted-return-val");
    if (lastExtras && lastExtras.weighted_return_5y !== undefined) {
        scoreVal.textContent = lastExtras.weighted_return_5y;
        scoreBadge.classList.remove("hidden");
    } else {
        scoreBadge.classList.add("hidden");
    }

    renderExtras(lastExtras);
    updateHeroCards(results, lastExtras);
    renderHeatmap(results);
    renderScenarios(results);
    if (lastExtras && lastExtras.optimized_weights) {
        renderOptimization(lastExtras.optimized_weights, results);
    } else {
        document.getElementById("optimization-wrap").classList.add("hidden");
    }

    // Load News async so it doesn't block rendering
    loadNews(results);

    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
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

    // AI settings toggle
    const aiToggle = document.getElementById("use-ai-toggle");
    const aiSettings = document.getElementById("ai-settings");
    const toggleAIVisibility = () => aiSettings.classList.toggle("hidden", !aiToggle.checked);
    aiToggle.addEventListener("change", toggleAIVisibility);
    toggleAIVisibility();

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
    document.getElementById("analyze-btn").addEventListener("click", () => {
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
        runAnalysis({ tickers, use_ai: useAI, api_key: apiKey, av_api_key: avKey, model, check_islamic: checkIslamic, check_financials: checkFinancials }, "/api/analyze");
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
});
