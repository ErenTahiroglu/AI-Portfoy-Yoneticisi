// ═══════════════════════════════════════
// GLOBAL STATE MANAGEMENT
// ═══════════════════════════════════════
const AppState = createStore({
    viewMode: localStorage.getItem("viewMode") || "beginner",
    isHalalOnly: localStorage.getItem("isHalalOnly") === "true",
    results: [],
    extras: null
});
window.AppState = AppState; // Global Access

AppState.subscribe((prop, val, oldValue) => {
    if (prop === "viewMode") {
        if (val === "pro") {
            document.body.classList.add("professional-mode");
        } else {
            document.body.classList.remove("professional-mode");
        }
        localStorage.setItem("viewMode", val);
        const profToggle = document.getElementById("prof-mode-toggle");
        if (profToggle) profToggle.checked = (val === "pro");
    }
    
    if (prop === "isHalalOnly") {
        if (val) {
            document.body.classList.add("halal-only");
        } else {
            document.body.classList.remove("halal-only");
        }
        localStorage.setItem("isHalalOnly", val);
        const halalToggle = document.getElementById("check-islamic-toggle");
        if (halalToggle) halalToggle.checked = val;
    }

    if (prop === "results") {
        const grid = document.getElementById("results-grid");
        const summaryBody = document.getElementById("summary-table-body");
        const resultsSection = document.getElementById("results");
        
        if (!val || val.length === 0) {
            if (grid) grid.innerHTML = "";
            if (summaryBody) summaryBody.innerHTML = "";
            if (resultsSection) resultsSection.classList.add("hidden");
            return;
        }

        if (resultsSection) resultsSection.classList.remove("hidden");

        // Incremental streaming render is handled by renderSingleCard directly from api.js
        if (oldValue && val.length > oldValue.length) {
            return; 
        } else {
            // Full reset or cache load
            if (grid) grid.innerHTML = "";
            if (summaryBody) summaryBody.innerHTML = "";
            val.forEach((res, idx) => {
                appendResultItem(res, idx, grid, summaryBody);
            });
        }

        window.lastResults = val;
        try { renderHeatmap(val); } catch (e) { }
        try { renderScenarios(val); } catch (e) { }
    }

    if (prop === "extras") {
        window.lastExtras = val;
        if (!val) return;
        try {
            const scoreBadge = document.getElementById("portfolio-score-badge");
            const scoreVal = document.getElementById("weighted-return-val");
            if (val.weighted_return_5y !== undefined) {
                if (scoreVal) scoreVal.textContent = val.weighted_return_5y;
                if (scoreBadge) scoreBadge.classList.remove("hidden");
            } else {
                if (scoreBadge) scoreBadge.classList.add("hidden");
            }
        } catch (e) { }

        try { renderExtras(val); } catch (e) { }
        try { updateHeroCards(AppState.results, val); } catch (e) { }
        
        try {
            if (val.optimized_weights) {
                renderOptimization(val.optimized_weights, AppState.results);
            } else {
                const optWrap = document.getElementById("optimization-wrap");
                if (optWrap) optWrap.classList.add("hidden");
            }
        } catch (e) { }
    }
});

// ═══════════════════════════════════════
// COMPARISON MODE
// ═══════════════════════════════════════
async function showComparison() {
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
    const { createComparisonTable } = await import('./components/CardComponent.js');
    content.innerHTML = createComparisonTable(tickers, metrics);
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
window.renderSingleCard = function(item) {
    const grid = document.getElementById("results-grid");
    const summaryBody = document.getElementById("summary-table-body");
    const resultsSection = document.getElementById("results");

    if (resultsSection) resultsSection.classList.remove("hidden");

    const skeleton = document.getElementById(`skeleton-${item.ticker}`);
    if (skeleton) {
        skeleton.remove();
    }

    const idx = AppState.results.length; 
    appendResultItem(item, idx, grid, summaryBody);
}

let CardComponent = null;
async function getCardComponent() {
    if (!CardComponent) {
        CardComponent = await import('./components/CardComponent.js');
    }
    return CardComponent;
}

// APPEND SINGLE RESULT ITEM
// ═══════════════════════════════════════
async function appendResultItem(res, idx, grid, summaryBody) {
    const { createCard, createSummaryRow } = await getCardComponent();

    // 1. Summary table row
    if (summaryBody) {
        const tr = createSummaryRow(res);
        summaryBody.appendChild(tr);
    }

    // 2. Individual result card
    if (grid) {
        const { card, chartId } = createCard(res, idx);
        grid.appendChild(card);

        if (res.error) return; // Hata kartı ise grafik çizme

        const fin = res.financials || {};
        // Grafiklerin render edilmesi (TV Charts)
        if ((fin.yg && Object.keys(fin.yg).length > 0) || res.klines) {
            setTimeout(() => typeof createTVChart === "function" && createTVChart(chartId, res), 50);
        }
        if (res.radar_score) setTimeout(() => typeof createRadarChart === "function" && createRadarChart(`radar-${chartId}`, res), 50);
        if (res.technicals && res.technicals.gauge_score !== undefined) setTimeout(() => typeof createGaugeChart === "function" && createGaugeChart(`gauge-${chartId}`, res.technicals.gauge_score, `gauge-lbl-${chartId}`, `gauge-val-${chartId}`), 50);
        if (res.technicals && res.technicals.relative_performance) setTimeout(() => typeof createRelativePerformanceChart === "function" && createRelativePerformanceChart(`relperf-${chartId}`, res.technicals.relative_performance), 50);
    }
}

// RENDER RESULTS
// ═══════════════════════════════════════
function renderResults(data) {
    document.getElementById("comparison-view").classList.add("hidden");
    AppState.results = data.results || [];
    if (data.extras) AppState.extras = data.extras;
    
    const resultsSection = document.getElementById("results");
    if (resultsSection) {
        resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    try {
        if (document.getElementById("use-ai-toggle").checked && AppState.results.length > 0) {
            document.getElementById("copilot-fab").classList.remove("hidden");
        }
    } catch (e) { }

    try { loadNews(AppState.results); } catch (e) { }
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

        renderResults({ results: lastResults, extras: calculateClientSideExtras(lastResults) });
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

    // ── Server Status & Proactive Cold Start Check ──
    const statusDot = document.getElementById("server-status-dot");
    if (statusDot) {
        statusDot.className = "status-dot dot-yellow"; 
        checkServerHealth().then(h => {
            if (h.online) {
                statusDot.className = "status-dot dot-green";
                statusDot.title = "Online";
            } else {
                statusDot.className = "status-dot dot-yellow"; 
                statusDot.title = "Waking up...";
                showToast(getLang() === "en" ? "Server waking up (Free Tier)..." : "Sunucu uyandırılıyor (Free Tier)...", "info");
                
                let pollInt = setInterval(async () => {
                    const h2 = await checkServerHealth();
                    if (h2.online) {
                        statusDot.className = "status-dot dot-green";
                        statusDot.title = "Online";
                        clearInterval(pollInt);
                        showToast(getLang() === "en" ? "Server is ready!" : "Sunucu hazır!", "success");
                    }
                }, 8000);
            }
        });
    }

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
    if (profToggle) {
        profToggle.checked = (AppState.viewMode === "pro");
        profToggle.addEventListener("change", (e) => {
            AppState.viewMode = e.target.checked ? "pro" : "beginner";
        });
    }

    // Halal Filter Toggle
    const halalToggle = document.getElementById("check-islamic-toggle");
    if (halalToggle) {
        AppState.isHalalOnly = halalToggle.checked; // Init from DOM if checked
        halalToggle.addEventListener("change", (e) => {
            AppState.isHalalOnly = e.target.checked;
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

    // Heatmap Filter
    const heatmapFilter = document.getElementById("heatmap-filter");
    if (heatmapFilter) {
        heatmapFilter.addEventListener("change", () => {
            if (window.lastResults && window.lastResults.length > 0) {
                renderHeatmap(window.lastResults);
            }
        });
    }

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

    initCopilot();
});

// ═══════════════════════════════════════
// AI COPILOT CHAT
// ═══════════════════════════════════════
function initCopilot() {
    const fab = document.getElementById("copilot-fab");
    const widget = document.getElementById("copilot-widget");
    const closeBtn = document.getElementById("copilot-close-btn");
    const input = document.getElementById("copilot-input");
    const sendBtn = document.getElementById("copilot-send-btn");
    const body = document.getElementById("copilot-body");
    
    if(!fab || !widget) return;

    let chatHistory = [];
    
    // Show FAB if AI is enabled
    document.getElementById("use-ai-toggle").addEventListener("change", (e) => {
        if (e.target.checked && lastResults && lastResults.length > 0) fab.classList.remove("hidden");
        else { fab.classList.add("hidden"); widget.classList.add("hidden"); }
    });
    
    fab.addEventListener("click", () => {
        widget.classList.toggle("hidden");
        if (!widget.classList.contains("hidden")) input.focus();
    });
    
    closeBtn.addEventListener("click", () => widget.classList.add("hidden"));
    
    function appendMsg(text, isUser) {
        const div = document.createElement("div");
        div.className = `copilot-msg ${isUser ? 'user-msg' : 'ai-msg'}`;
        div.innerHTML = isUser ? text : marked.parse(text); // markdown for AI
        body.appendChild(div);
        body.scrollTop = body.scrollHeight;
    }
    
    async function sendMessage() {
        const text = input.value.trim();
        if(!text) return;
        
        const apiKey = document.getElementById("api-key").value;
        if(!apiKey) {
            showToast("AI bağlantısı için API anahtarı gereklidir.", "warning");
            return;
        }
        
        appendMsg(text, true);
        chatHistory.push({ role: "user", content: text });
        input.value = "";
        
        // Show loading indicator
        const loadDiv = document.createElement("div");
        loadDiv.className = "copilot-msg ai-msg";
        loadDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Düşünüyor...';
        body.appendChild(loadDiv);
        body.scrollTop = body.scrollHeight;
        
        try {
            const contextMsg = {
                results: (lastResults || []).map(r => ({ ticker: r.ticker, metrics: r.valuation, risk: r.financials?.risk, performance: r.financials?.s5 })),
                extras: lastExtras || {}
            };
            
            const payload = {
                messages: chatHistory,
                portfolio_context: contextMsg,
                api_key: apiKey,
                model: document.getElementById("model-select").value,
                lang: getLang()
            };
            
            const res = await fetch(`${API_BASE}/api/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            
            loadDiv.remove();
            
            if(!res.ok) throw new Error("API Hatası");
            const data = await res.json();
            
            const reply = data.reply;
            appendMsg(reply, false);
            chatHistory.push({ role: "assistant", content: reply });
        } catch(err) {
            loadDiv.remove();
            appendMsg("Bağlantı hatası: " + err.message, false);
        }
    }
    
    sendBtn.addEventListener("click", sendMessage);
    input.addEventListener("keypress", (e) => { if (e.key === "Enter") sendMessage(); });
}

// ═══════════════════════════════════════
// MACRO AI RENDERER
// ═══════════════════════════════════════
let macroBuffer = "";

window.renderMacroAI = function(chunk, isDone) {
    let container = document.getElementById("macro-advice-container");
    
    if (!container) {
        const grid = document.getElementById("results-grid");
        if (!grid) return; // Grid yoksa çizme
        
        container = document.createElement("div");
        container.id = "macro-advice-container";
        container.className = "macro-advice-card glass-panel stagger-enter";
        container.style.marginTop = "2rem";
        container.style.padding = "1.5rem";
        container.style.width = "100%";
        
        container.innerHTML = `
            <div class="card-header" style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem; margin-bottom: 1rem;">
                <h3 style="display:flex; align-items:center; gap:0.5rem; color:var(--primary); margin:0;">
                    <i class="fas fa-brain"></i> AI Portföy Yöneticisi Özeti
                </h3>
            </div>
            <div class="macro-content markdown-body" id="macro-content" style="font-size: 0.92rem; line-height: 1.6;"></div>
        `;
        
        // Grid'in bulunduğu container'a ekle (Grid'in altına)
        grid.parentNode.appendChild(container);
        macroBuffer = ""; // Tamponu sıfırla
    }

    const contentDiv = document.getElementById("macro-content");

    if (chunk) {
        macroBuffer += chunk;
        if (typeof marked !== "undefined") {
            try {
                contentDiv.innerHTML = marked.parse(macroBuffer);
            } catch (e) {
                contentDiv.innerText = macroBuffer; // Fallback
            }
        } else {
            contentDiv.innerText = macroBuffer;
        }
        
        // Bulunduğu alanı odağa al
        container.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    if (isDone) {
        if (typeof marked !== "undefined") {
            try {
                contentDiv.innerHTML = marked.parse(macroBuffer);
            } catch (e) {}
        }
        showToast("Makro AI Analizi Hazır!", "success");
    }
}
