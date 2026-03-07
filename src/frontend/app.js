/**
 * Portföy Analiz Platformu — app.js v4.0
 * =========================================
 * Features: Toast, Watchlist, Autocomplete, Collapse, Chart.js,
 * Comparison, Export, Theme toggle, i18n, Technical indicators,
 * Sector chart, Correlation heatmap, Monte Carlo fan chart, API encryption
 */

const API_BASE = "";
let lastResults = null;
let lastExtras = null;
let chartInstances = {};      // chart ID → Chart instance (for destroy)

// ═══════════════════════════════════════
// TOAST NOTIFICATIONS
// ═══════════════════════════════════════
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    const icons = { success: "fa-check-circle", error: "fa-exclamation-circle", warning: "fa-exclamation-triangle", info: "fa-info-circle" };
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// ═══════════════════════════════════════
// THEME TOGGLE
// ═══════════════════════════════════════
function initTheme() {
    const saved = localStorage.getItem("theme");
    if (saved) {
        document.documentElement.setAttribute("data-theme", saved);
        updateThemeIcon(saved);
    }
}

function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    updateThemeIcon(next);
}

function updateThemeIcon(theme) {
    const icon = document.getElementById("theme-icon");
    if (icon) icon.className = theme === "light" ? "fas fa-sun" : "fas fa-moon";
}

// ═══════════════════════════════════════
// WATCHLIST (localStorage)
// ═══════════════════════════════════════
function getWatchlists() {
    try { return JSON.parse(localStorage.getItem("portfolioWatchlists") || "[]"); }
    catch { return []; }
}

function saveWatchlists(lists) {
    localStorage.setItem("portfolioWatchlists", JSON.stringify(lists));
}

function renderWatchlists() {
    const container = document.getElementById("watchlist-container");
    const lists = getWatchlists();
    container.innerHTML = "";
    if (lists.length === 0) {
        container.innerHTML = `<p style="font-size:0.75rem; color:var(--text-muted); text-align:center; padding:0.5rem;">${t("sidebar.noWatchlist")}</p>`;
        return;
    }
    lists.forEach((item, idx) => {
        const el = document.createElement("div");
        el.className = "watchlist-item";
        el.innerHTML = `<div><div class="watchlist-name">${item.name}</div><div class="watchlist-count">${item.tickers.length} hisse</div></div><button class="watchlist-delete" data-idx="${idx}" title="Sil"><i class="fas fa-trash-alt"></i></button>`;
        el.addEventListener("click", (e) => {
            if (e.target.closest(".watchlist-delete")) return;
            document.getElementById("ticker-input").value = item.tickers.join(", ");
            showToast(`"${item.name}" ${t("toast.loaded")}`, "success");
        });
        el.querySelector(".watchlist-delete").addEventListener("click", (e) => {
            e.stopPropagation();
            const updated = getWatchlists().filter((_, i) => i !== idx);
            saveWatchlists(updated);
            renderWatchlists();
            showToast(`"${item.name}" ${t("toast.deleted")}`, "info");
        });
        container.appendChild(el);
    });
}

function saveCurrentPortfolio() {
    const input = document.getElementById("ticker-input").value.trim();
    if (!input) { showToast(t("toast.enterTickers"), "warning"); return; }
    const tickers = input.split(/[\s,;]+/).filter(t => t.length > 0).map(t => t.toUpperCase());
    const name = prompt(t("toast.portfolioName"));
    if (!name) return;
    const lists = getWatchlists();
    lists.push({ name, tickers });
    saveWatchlists(lists);
    renderWatchlists();
    showToast(`"${name}" ${t("toast.saved")} (${tickers.length} hisse)`, "success");
}

// ═══════════════════════════════════════
// AUTOCOMPLETE
// ═══════════════════════════════════════
let autocompleteTimeout = null;
function setupAutocomplete() {
    const textarea = document.getElementById("ticker-input");
    const dropdown = document.getElementById("autocomplete-dropdown");
    textarea.addEventListener("input", () => {
        clearTimeout(autocompleteTimeout);
        const words = textarea.value.split(/[\s,;]+/);
        const lastWord = words[words.length - 1];
        if (!lastWord || lastWord.length < 1) { dropdown.classList.add("hidden"); return; }
        autocompleteTimeout = setTimeout(async () => {
            try {
                const res = await fetch(`${API_BASE}/api/suggest?q=${encodeURIComponent(lastWord)}`);
                const data = await res.json();
                if (data.suggestions && data.suggestions.length > 0) {
                    dropdown.innerHTML = data.suggestions.map(s => `<div class="autocomplete-item" data-ticker="${s.ticker}"><span class="ticker-symbol">${s.ticker}</span><span class="ticker-name">${s.name}</span></div>`).join("");
                    dropdown.classList.remove("hidden");
                    dropdown.querySelectorAll(".autocomplete-item").forEach(item => {
                        item.addEventListener("click", () => { words[words.length - 1] = item.dataset.ticker; textarea.value = words.join(", ") + ", "; dropdown.classList.add("hidden"); textarea.focus(); });
                    });
                } else { dropdown.classList.add("hidden"); }
            } catch { dropdown.classList.add("hidden"); }
        }, 200);
    });
    textarea.addEventListener("blur", () => setTimeout(() => dropdown.classList.add("hidden"), 200));
}

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
            body: JSON.stringify({ prompt: promptText, api_key: apiKey, model: currModel })
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
// COLLAPSIBLE SECTIONS
// ═══════════════════════════════════════
function toggleCollapsible(header) {
    header.classList.toggle("open");
    header.nextElementSibling.classList.toggle("open");
}

// ═══════════════════════════════════════
// CHART HELPERS
// ═══════════════════════════════════════
function destroyChart(id) {
    if (chartInstances[id]) { chartInstances[id].destroy(); delete chartInstances[id]; }
}

function getChartColors() {
    const isDark = document.documentElement.getAttribute("data-theme") !== "light" || (!localStorage.getItem("theme") && window.matchMedia("(prefers-color-scheme: dark)").matches);
    return {
        grid: isDark ? "rgba(148,163,184,0.1)" : "rgba(0,0,0,0.06)",
        text: isDark ? "#94a3b8" : "#64748b",
    };
}

function createReturnChart(canvasId, fin) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !fin) return;
    const years = Object.keys(fin.yg || {}).sort();
    if (years.length === 0) return;
    const { grid, text } = getChartColors();
    destroyChart(canvasId);
    chartInstances[canvasId] = new Chart(canvas, {
        type: "bar",
        data: {
            labels: years,
            datasets: [
                { label: "Nominal (%)", data: years.map(y => fin.yg[y]), backgroundColor: years.map(y => fin.yg[y] >= 0 ? "rgba(99,102,241,0.7)" : "rgba(239,68,68,0.6)"), borderRadius: 4, barPercentage: 0.7 },
                { label: "Reel (%)", data: years.map(y => fin.yr[y]), backgroundColor: years.map(y => fin.yr[y] >= 0 ? "rgba(56,189,248,0.6)" : "rgba(245,158,11,0.6)"), borderRadius: 4, barPercentage: 0.7 },
            ],
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "top", labels: { color: text, font: { size: 11, family: "Inter" }, boxWidth: 12 } } }, scales: { x: { grid: { display: false }, ticks: { color: text, font: { size: 11 } } }, y: { grid: { color: grid }, ticks: { color: text, font: { size: 11 }, callback: v => v + "%" } } } },
    });
}

// ═══════════════════════════════════════
// FORMAT HELPERS
// ═══════════════════════════════════════
function formatMarketCap(val) {
    if (!val) return "-";
    if (val >= 1e12) return (val / 1e12).toFixed(2) + "T";
    if (val >= 1e9) return (val / 1e9).toFixed(2) + "B";
    if (val >= 1e6) return (val / 1e6).toFixed(1) + "M";
    return val.toLocaleString();
}
function fmtNum(val, suffix = "") {
    if (val === undefined || val === null || val === "-") return "-";
    return (typeof val === "number" ? val.toFixed(2) : val) + suffix;
}
function colorClass(val) {
    if (val === undefined || val === null) return "";
    return val >= 0 ? "positive" : "negative";
}

// ═══════════════════════════════════════
// TECHNICAL INDICATORS RENDERER
// ═══════════════════════════════════════
function renderTechnicals(tech) {
    if (!tech) return "";
    let html = `<div class="collapsible-header" onclick="toggleCollapsible(this)"><h4><i class="fas fa-chart-area"></i> ${t("card.technicals")}</h4><i class="fas fa-chevron-down collapse-icon"></i></div><div class="collapsible-body"><div class="technicals-grid">`;

    // RSI
    if (tech.rsi_14 !== undefined) {
        const cls = tech.rsi_14 > 70 ? "rsi-overbought" : (tech.rsi_14 < 30 ? "rsi-oversold" : "rsi-neutral");
        const label = tech.rsi_14 > 70 ? "Aşırı Alım" : (tech.rsi_14 < 30 ? "Aşırı Satım" : "Nötr");
        html += `<div class="tech-box"><div class="tech-label">RSI (14)</div><div class="tech-value ${cls}">${tech.rsi_14}</div><div class="tech-label">${label}</div></div>`;
    }
    // MACD
    if (tech.macd !== undefined) {
        const cls = tech.macd_hist > 0 ? "macd-bullish" : "macd-bearish";
        html += `<div class="tech-box"><div class="tech-label">MACD</div><div class="tech-value ${cls}">${tech.macd}</div></div>`;
        html += `<div class="tech-box"><div class="tech-label">Sinyal</div><div class="tech-value">${tech.macd_signal}</div></div>`;
    }
    // EMA
    [20, 50, 100, 200].forEach(p => {
        const key = `ema_${p}`;
        if (tech[key] !== undefined) {
            const above = tech.last_close >= tech[key];
            html += `<div class="tech-box"><div class="tech-label">EMA ${p}</div><div class="tech-value ${above ? 'positive' : 'negative'}">${tech[key]}</div></div>`;
        }
    });
    // SMA
    [20, 50, 100, 200].forEach(p => {
        const key = `sma_${p}`;
        if (tech[key] !== undefined) {
            const above = tech.last_close >= tech[key];
            html += `<div class="tech-box"><div class="tech-label">SMA ${p}</div><div class="tech-value ${above ? 'positive' : 'negative'}">${tech[key]}</div></div>`;
        }
    });

    html += `</div></div>`;
    return html;
}

// ═══════════════════════════════════════
// RENDER PORTFOLIO EXTRAS
// ═══════════════════════════════════════
function renderExtras(extras) {
    if (!extras) return;

    // Sector Distribution
    const sectorCard = document.getElementById("sector-card");
    if (extras.sector_distribution && Object.keys(extras.sector_distribution).length > 0) {
        sectorCard.classList.remove("hidden");
        const sectors = extras.sector_distribution;
        const labels = Object.keys(sectors);
        const values = Object.values(sectors);
        const colors = ["#6366f1", "#38bdf8", "#22c55e", "#f59e0b", "#ef4444", "#a855f7", "#ec4899", "#14b8a6", "#f97316", "#84cc16"];
        destroyChart("sector-chart");
        chartInstances["sector-chart"] = new Chart(document.getElementById("sector-chart"), {
            type: "doughnut",
            data: { labels, datasets: [{ data: values, backgroundColor: colors.slice(0, labels.length), borderWidth: 0 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "right", labels: { color: getChartColors().text, font: { size: 11, family: "Inter" }, boxWidth: 12, padding: 8 } } } },
        });
    } else { sectorCard.classList.add("hidden"); }

    // Correlation Matrix
    const corrCard = document.getElementById("correlation-card");
    if (extras.correlation && extras.correlation.tickers && extras.correlation.tickers.length >= 2) {
        corrCard.classList.remove("hidden");
        const { tickers, matrix } = extras.correlation;
        let html = `<table class="correlation-table"><thead><tr><th></th>`;
        tickers.forEach(t => { html += `<th>${t}</th>`; });
        html += `</tr></thead><tbody>`;
        matrix.forEach((row, i) => {
            html += `<tr><th>${tickers[i]}</th>`;
            row.forEach(v => {
                const hue = v > 0 ? 130 : 0;
                const lightness = 100 - Math.abs(v) * 40;
                const color = `hsl(${hue}, 70%, ${lightness}%)`;
                html += `<td class="corr-cell" style="background:${color};color:${lightness < 60 ? '#fff' : '#000'}">${v.toFixed(2)}</td>`;
            });
            html += `</tr>`;
        });
        html += `</tbody></table>`;
        document.getElementById("correlation-content").innerHTML = html;
    } else { corrCard.classList.add("hidden"); }

    // Monte Carlo
    const mcCard = document.getElementById("monte-carlo-card");
    if (extras.monte_carlo) {
        mcCard.classList.remove("hidden");
        const mc = extras.monte_carlo;
        const labels = mc.months.map(m => `${m}ay`);
        const { grid, text } = getChartColors();
        destroyChart("monte-carlo-chart");
        chartInstances["monte-carlo-chart"] = new Chart(document.getElementById("monte-carlo-chart"), {
            type: "line",
            data: {
                labels,
                datasets: [
                    { label: "%5", data: mc.percentiles.p5, borderColor: "rgba(239,68,68,0.5)", backgroundColor: "transparent", borderWidth: 1, pointRadius: 0, borderDash: [4, 2] },
                    { label: "%25", data: mc.percentiles.p25, borderColor: "rgba(245,158,11,0.5)", backgroundColor: "transparent", borderWidth: 1, pointRadius: 0, borderDash: [4, 2] },
                    { label: "%50 (Medyan)", data: mc.percentiles.p50, borderColor: "#6366f1", backgroundColor: "rgba(99,102,241,0.1)", borderWidth: 2.5, pointRadius: 0, fill: false },
                    { label: "%75", data: mc.percentiles.p75, borderColor: "rgba(56,189,248,0.5)", backgroundColor: "transparent", borderWidth: 1, pointRadius: 0, borderDash: [4, 2] },
                    { label: "%95", data: mc.percentiles.p95, borderColor: "rgba(34,197,94,0.5)", backgroundColor: "transparent", borderWidth: 1, pointRadius: 0, borderDash: [4, 2] },
                ],
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "top", labels: { color: text, font: { size: 10, family: "Inter" }, boxWidth: 10 } } }, scales: { x: { grid: { display: false }, ticks: { color: text, font: { size: 10 } } }, y: { grid: { color: grid }, ticks: { color: text, font: { size: 10 }, callback: v => (v * 100 - 100).toFixed(0) + "%" } } } },
        });
    } else { mcCard.classList.add("hidden"); }
}

// ═══════════════════════════════════════
// HERO CARDS
// ═══════════════════════════════════════
function updateHeroCards(results, extras) {
    const cardsContainer = document.getElementById("hero-cards");
    const scoreVal = document.getElementById("hero-score-val");
    const bestVal = document.getElementById("hero-best-val");
    const riskVal = document.getElementById("hero-risk-val");

    if (!results || results.length === 0) {
        cardsContainer.classList.add("hidden");
        return;
    }

    cardsContainer.classList.remove("hidden");

    // Portföy Skoru (Ağırlıklı Getiri veya Ortalama)
    if (extras && extras.weighted_return_5y !== undefined) {
        scoreVal.textContent = `%${extras.weighted_return_5y}`;
    } else {
        scoreVal.textContent = "-";
    }

    // En İyi Hisse (5Y getiriye göre veya Son Değişim)
    let bestStock = null;
    let maxRet = -Infinity;
    results.forEach(r => {
        if (!r.error && r.financials && r.financials.s5 !== undefined && r.financials.s5 !== null) {
            if (r.financials.s5 > maxRet) {
                maxRet = r.financials.s5;
                bestStock = r.ticker;
            }
        }
    });
    if (bestStock) {
        bestVal.innerHTML = `${bestStock} <span style="font-size:0.8rem;color:var(--success)">(%${maxRet.toFixed(1)})</span>`;
    } else {
        bestVal.textContent = "-";
    }

    // Risk Seviyesi (Ortalama Max DD)
    let totalRisk = 0;
    let riskCount = 0;
    results.forEach(r => {
        if (!r.error && r.financials && r.financials.risk && r.financials.risk.max_drawdown !== null) {
            totalRisk += Math.abs(r.financials.risk.max_drawdown);
            riskCount++;
        }
    });

    if (riskCount > 0) {
        const avgRisk = totalRisk / riskCount;
        let riskLabel = "Düşük";
        let riskColor = "var(--success)";
        if (avgRisk > 30) { riskLabel = "Yüksek"; riskColor = "var(--danger)"; }
        else if (avgRisk > 15) { riskLabel = "Orta"; riskColor = "var(--warning)"; }
        riskVal.innerHTML = `<span style="color:${riskColor}">${riskLabel}</span> <span style="font-size:0.8rem;color:var(--text-muted)">(MaxDD: %${avgRisk.toFixed(1)})</span>`;
    } else {
        riskVal.textContent = "-";
    }
}

// ═══════════════════════════════════════
// HEATMAP (TREEMAP)
// ═══════════════════════════════════════
function renderHeatmap(results) {
    const wrap = document.getElementById("portfolio-heatmap-wrap");
    const container = document.getElementById("portfolio-heatmap");
    container.innerHTML = "";

    const validResults = results.filter(r => !r.error && r.financials && r.financials.son_fiyat && r.financials.son_fiyat.degisim !== undefined);

    if (validResults.length === 0) {
        wrap.classList.add("hidden");
        return;
    }

    wrap.classList.remove("hidden");

    // Total weight sum for flex-basis calculations
    const totalWeight = validResults.reduce((sum, r) => sum + (r.weight || 1), 0);

    // Calculate colors properly like S&P 500 heatmaps
    function getHeatmapColor(val) {
        if (val === null || val === undefined) return "#334155"; // bg-slate-700
        if (val > 3) return "#166534"; // Strong green
        if (val > 1) return "#22c55e"; // Mid green
        if (val > 0) return "#86efac"; // Light green (black text usually)
        if (val > -1) return "#fca5a5"; // Light red
        if (val > -3) return "#ef4444"; // Mid red
        return "#991b1b"; // Strong red
    }

    // Determine text color based on background luminance
    function getTextColor(val) {
        if (val > 0 && val <= 1) return "#064e3b"; // Dark green text on light green bg
        if (val < 0 && val >= -1) return "#7f1d1d"; // Dark red text on light red bg
        return "white";
    }

    validResults.forEach(r => {
        const change = r.financials.son_fiyat.degisim;
        const weight = r.weight || 1;
        const percentArea = (weight / totalWeight) * 100;

        const cell = document.createElement("div");
        cell.className = "heatmap-cell";

        // Use flex-basis to size proportionally. For a true 2D treemap, CSS Grid would be highly complex, 
        // flex-wrap provides a decent approximation for small portfolios.
        cell.style.flex = `1 1 calc(${percentArea}% - 0.5rem)`;
        cell.style.backgroundColor = getHeatmapColor(change);
        cell.style.color = getTextColor(change);

        // Hide text if the cell is too small
        if (percentArea < 3 && validResults.length > 10) {
            cell.title = `${r.ticker}: %${change.toFixed(2)}`;
        } else {
            cell.innerHTML = `
                <span class="hm-ticker">${r.ticker}</span>
                <span class="hm-val">%${change.toFixed(2)}</span>
            `;
            cell.title = `${r.ticker} (Ağırlık: ${weight})`;
        }

        container.appendChild(cell);
    });
}

// ═══════════════════════════════════════
// SCENARIOS & DIVIDEND CALCULATOR
// ═══════════════════════════════════════
function renderScenarios(results) {
    const wrap = document.getElementById("scenarios-wrap");
    if (!results || results.length === 0) {
        wrap.classList.add("hidden");
        return;
    }
    wrap.classList.remove("hidden");

    let totalWeight = 0;
    let weightedBeta = 0;
    let weightedDiv = 0;

    results.forEach(r => {
        if (!r.error && r.financials && r.valuation) {
            const w = r.weight || 1;
            totalWeight += w;
            const beta = r.valuation.beta || 1;
            const div = r.valuation.div_yield || 0;
            weightedBeta += beta * w;
            weightedDiv += div * w;
        }
    });

    const avgBeta = totalWeight > 0 ? weightedBeta / totalWeight : 1;
    const avgDivYield = totalWeight > 0 ? weightedDiv / totalWeight : 0; // percentage, e.g. 5 means 5%

    // Stress Tests
    const resStress = document.getElementById("scenario-stress-result");
    const btn2008 = document.getElementById("btn-scenario-2008");
    const btnCovid = document.getElementById("btn-scenario-covid");

    function calcStress(dropPct, name) {
        const expectedDrop = dropPct * avgBeta;
        resStress.innerHTML = `${name} Senaryosunda: <br><span style="color:var(--danger)"> Tahmini Düşüş: -%${expectedDrop.toFixed(1)}</span> <br><span style="font-size:0.8rem;color:var(--text-muted)">(Portföy Beta: ${avgBeta.toFixed(2)})</span>`;
    }

    btn2008.onclick = () => calcStress(50, "2008 Krizi");
    btnCovid.onclick = () => calcStress(33, "Covid-19");

    // Set default view
    calcStress(50, "2008 Krizi");

    // Dividend FI/RE Calculator
    const resDiv = document.getElementById("scenario-div-result");
    const inMonthlyAdd = document.getElementById("div-monthly-add");
    const inTargetIncome = document.getElementById("div-target-income");

    function calcDivFIRE() {
        if (avgDivYield <= 0.1) {
            resDiv.innerHTML = `<span style="color:var(--warning)">Portföy temettü verimi çok düşük (%${avgDivYield.toFixed(2)}). Hedefe ulaşmak mümkün görünmüyor.</span>`;
            return;
        }

        const P = parseFloat(inMonthlyAdd.value);
        const targetMonthly = parseFloat(inTargetIncome.value);
        if (!P || !targetMonthly || P <= 0 || targetMonthly <= 0) {
            resDiv.textContent = "Lütfen geçerli değerler girin."; return;
        }

        const r = avgDivYield / 100; // e.g. 0.05
        const targetCapital = (targetMonthly * 12) / r;

        // n (months) = Math.log((Capital * r/12 + P) / P) / Math.log(1 + r/12)
        const rateMonthly = r / 12;
        const months = Math.log((targetCapital * rateMonthly + P) / P) / Math.log(1 + rateMonthly);
        const years = months / 12;

        resDiv.innerHTML = `Ortalama Verim: <strong>%${avgDivYield.toFixed(2)}</strong><br>Hedef Sermaye: <strong>${targetCapital.toLocaleString("tr-TR", { maximumFractionDigits: 0 })}</strong><br> Süre: <strong>${years.toFixed(1)} Yıl</strong>`;
    }

    inMonthlyAdd.addEventListener("input", calcDivFIRE);
    inTargetIncome.addEventListener("input", calcDivFIRE);
    calcDivFIRE();
}

// ═══════════════════════════════════════
// OPTIMIZATION
// ═══════════════════════════════════════
function renderOptimization(optWeights, results) {
    const wrap = document.getElementById("optimization-wrap");
    const container = document.getElementById("opt-bars");

    if (!optWeights || Object.keys(optWeights).length === 0) {
        wrap.classList.add("hidden");
        return;
    }

    wrap.classList.remove("hidden");
    container.innerHTML = "";

    let totalCurWeight = results.reduce((sum, r) => sum + ((!r.error && r.weight) ? r.weight : 1), 0);

    let html = `<div style="display:grid; grid-template-columns: 80px 1fr 1fr; gap:1rem; font-size:0.85rem; font-weight:600; color:var(--text-muted); margin-bottom:1rem; border-bottom:1px solid var(--card-border); padding-bottom:0.5rem;"><div>Hisse</div><div>Mevcut Ağırlık</div><div>İdeal (Optimize) Ağırlık</div></div>`;

    for (const [ticker, idealPct] of Object.entries(optWeights)) {
        const r = results.find(x => x.ticker === ticker);
        let curPct = 0;
        if (r && !r.error) {
            curPct = ((r.weight || 1) / totalCurWeight) * 100;
        }

        html += `
        <div style="display:grid; grid-template-columns: 80px 1fr 1fr; gap:1rem; align-items:center; margin-bottom:0.75rem;">
            <div style="font-weight:700;">${ticker}</div>
            
            <div style="display:flex; align-items:center; gap:0.5rem;">
                <div style="flex:1; height:8px; background:rgba(255,255,255,0.05); border-radius:4px; overflow:hidden;">
                    <div style="height:100%; width:${curPct}%; background:var(--text-muted); border-radius:4px;"></div>
                </div>
                <span style="width:50px; text-align:right">%${curPct.toFixed(1)}</span>
            </div>
            
            <div style="display:flex; align-items:center; gap:0.5rem;">
                <div style="flex:1; height:8px; background:rgba(255,255,255,0.05); border-radius:4px; overflow:hidden;">
                    <div style="height:100%; width:${idealPct}%; background:var(--primary); box-shadow:0 0 8px rgba(14, 165, 233, 0.4); border-radius:4px;"></div>
                </div>
                <span style="width:50px; text-align:right; color:var(--primary); font-weight:700;">%${idealPct.toFixed(1)}</span>
            </div>
        </div>`;
    }

    container.innerHTML = html;
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
            body: JSON.stringify({ tickers: tickers.slice(0, 5), api_key: aKey, model: currModel })
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
// EXPORT
// ═══════════════════════════════════════
async function exportResults(format) {
    if (!lastResults) { showToast(t("toast.noTickers"), "warning"); return; }
    showToast(`${format.toUpperCase()} ${t("toast.exporting")}`, "info");
    try {
        const res = await fetch(`${API_BASE}/api/export/${format}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ results: lastResults, format }) });
        if (!res.ok) throw new Error("Export failed");
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `portfolio_analysis.${format === "excel" ? "xlsx" : format}`;
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
// API KEY ENCRYPTION (AES-GCM)
// ═══════════════════════════════════════
async function getEncKey() {
    const raw = localStorage.getItem("_ek");
    if (raw) return await crypto.subtle.importKey("jwk", JSON.parse(raw), { name: "AES-GCM" }, true, ["encrypt", "decrypt"]);
    const key = await crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, true, ["encrypt", "decrypt"]);
    localStorage.setItem("_ek", JSON.stringify(await crypto.subtle.exportKey("jwk", key)));
    return key;
}

async function encryptApiKey(plaintext) {
    if (!plaintext) return "";
    const key = await getEncKey();
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const ct = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, new TextEncoder().encode(plaintext));
    const combined = new Uint8Array(iv.length + ct.byteLength);
    combined.set(iv); combined.set(new Uint8Array(ct), iv.length);
    return btoa(String.fromCharCode(...combined));
}

async function decryptApiKey(b64) {
    if (!b64) return "";
    try {
        const key = await getEncKey();
        const data = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
        const iv = data.slice(0, 12);
        const ct = data.slice(12);
        const pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv }, key, ct);
        return new TextDecoder().decode(pt);
    } catch { return ""; }
}

// Save/load encrypted keys
async function saveApiKeys() {
    const gemini = document.getElementById("api-key").value;
    const av = document.getElementById("av-api-key").value;
    if (gemini) localStorage.setItem("_gk", await encryptApiKey(gemini));
    if (av) localStorage.setItem("_ak", await encryptApiKey(av));
}

async function loadApiKeys() {
    const gk = await decryptApiKey(localStorage.getItem("_gk") || "");
    const ak = await decryptApiKey(localStorage.getItem("_ak") || "");
    if (gk) document.getElementById("api-key").value = gk;
    if (ak) document.getElementById("av-api-key").value = ak;
}

// ═══════════════════════════════════════
// MAIN ANALYSIS
// ═══════════════════════════════════════
async function runAnalysis(payload, endpoint) {
    const btn = document.getElementById("analyze-btn");
    const loader = document.getElementById("loader");
    const results = document.getElementById("results");
    btn.disabled = true; results.classList.add("hidden"); loader.classList.remove("hidden");
    await saveApiKeys();
    try {
        const res = await fetch(`${API_BASE}${endpoint}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || `Sunucu hatası (${res.status})`); }
        const data = await res.json();
        loader.classList.add("hidden");
        renderResults(data);
        showToast(`${(data.results || []).length} ${t("toast.analysisComplete")}`, "success");
    } catch (err) { loader.classList.add("hidden"); showToast(err.message, "error"); }
    finally { btn.disabled = false; }
}

async function runFileAnalysis(file) {
    const btn = document.getElementById("analyze-btn");
    const loader = document.getElementById("loader");
    const results = document.getElementById("results");
    const formData = new FormData();
    formData.append("file", file);
    formData.append("use_ai", document.getElementById("use-ai-toggle").checked);
    formData.append("check_islamic", document.getElementById("check-islamic-toggle").checked);
    formData.append("check_financials", document.getElementById("check-financials-toggle").checked);
    formData.append("model", document.getElementById("model-select").value);
    const apiKey = document.getElementById("api-key").value;
    if (apiKey) formData.append("api_key", apiKey);
    const avKey = document.getElementById("av-api-key").value;
    if (avKey) formData.append("av_api_key", avKey);
    btn.disabled = true; results.classList.add("hidden"); loader.classList.remove("hidden");
    await saveApiKeys();
    try {
        const res = await fetch(`${API_BASE}/api/analyze/file`, { method: "POST", body: formData });
        if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || `Sunucu hatası (${res.status})`); }
        const data = await res.json();
        loader.classList.add("hidden");
        renderResults(data);
        showToast(`${(data.results || []).length} ${t("toast.analysisComplete")}`, "success");
    } catch (err) { loader.classList.add("hidden"); showToast(err.message, "error"); }
    finally { btn.disabled = false; }
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
