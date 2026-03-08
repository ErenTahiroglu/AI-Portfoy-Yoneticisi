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
        type: "line",
        data: {
            labels: years,
            datasets: [
                { type: "bar", label: "Nominal (%)", data: years.map(y => fin.yg[y]), backgroundColor: years.map(y => fin.yg[y] >= 0 ? "rgba(99,102,241,0.7)" : "rgba(239,68,68,0.6)"), borderRadius: 4, barPercentage: 0.7 },
                { type: "line", label: "Reel (%)", data: years.map(y => fin.yr[y]), backgroundColor: "rgba(56,189,248,0.2)", borderColor: "rgba(56,189,248,1)", borderWidth: 2, fill: true, tension: 0.4, pointRadius: 3, pointHoverRadius: 6 },
            ],
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "top", labels: { color: text, font: { size: 11, family: "Inter" }, boxWidth: 12 } } }, scales: { x: { grid: { display: false }, ticks: { color: text, font: { size: 11 } } }, y: { grid: { color: grid }, ticks: { color: text, font: { size: 11 }, callback: v => v + "%" } } } },
    });
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
