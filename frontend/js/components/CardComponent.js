/**
 * 🧩 CardComponent.js — ES Module
 * =====================================
 * Sonuç kartlarının ve özet satırlarının HTML inşasını yönetir.
 * app.js içindeki appendResultItem mantığının izole edilmiş halidir.
 */

export function createSummaryRow(res) {
    const fin = res.financials || {};
    const val = res.valuation || {};
    const sonFiyat = fin.son_fiyat ? `${fin.son_fiyat.fiyat?.toFixed(2) || "-"}` : "-";
    const purRatio = res.purification_ratio !== undefined ? `%${parseFloat(res.purification_ratio).toFixed(2)}` : "-";

    let statusText = res.status || "-";
    if (getLang() === "en") {
        if (statusText === "Uygun") statusText = "Compliant";
        else if (statusText === "Uygun Değil") statusText = "Non-Compliant";
        else if (statusText === "Katılım Fonu Değil") statusText = "Non-Participation";
    }
    const statusClass = res.status === "Uygun" ? "status-approved" : (res.status === "Uygun Değil" || res.status === "Katılım Fonu Değil" ? "status-rejected" : "");

    const summaryFullName = res.full_name || fin.ad || "";
    const tickerDisplay = summaryFullName ? `<div style="font-weight:700">${res.ticker}</div><div style="font-size:0.7rem; color:var(--text-muted)">${summaryFullName}</div>` : `<span style="font-weight:700">${res.ticker}</span>`;

    const tr = document.createElement("tr");
    if (statusClass) tr.className = statusClass; 
    let marketText = res.market || "?";
    if (getLang() === "tr" && marketText === "US") marketText = "ABD";

    tr.innerHTML = `<td>${tickerDisplay}</td><td><span class="market-badge">${marketText}</span></td><td>${res.weight || 1}</td><td>${sonFiyat}</td><td>${purRatio}</td><td>${statusText !== "-" ? `<span class="${statusClass}">${statusText}</span>` : "-"}</td><td>${fmtNum(val.pe)}</td><td>${fmtNum(val.pb)}</td><td>${fmtNum(val.beta)}</td>`;
    return tr;
}

export function createCard(res, idx) {
    const fin = res.financials || {};
    const val = res.valuation || {};
    let statusText = res.status || "-";
    if (getLang() === "en") {
        if (statusText === "Uygun") statusText = "Compliant";
        else if (statusText === "Uygun Değil") statusText = "Non-Compliant";
        else if (statusText === "Katılım Fonu Değil") statusText = "Non-Participation";
    }
    const statusClass = res.status === "Uygun" ? "status-approved" : (res.status === "Uygun Değil" || res.status === "Katılım Fonu Değil" ? "status-rejected" : "");

    const card = document.createElement("div");
    card.className = `result-card glass-panel ${statusClass} stagger-enter stagger-` + ((idx % 5) + 1);
    const chartId = `chart-${idx}`;

    if (res.error) {
        let aiHTML = "";
        if (res.ai_comment) {
            const parsedAI = typeof marked !== "undefined" ? marked.parse(res.ai_comment) : res.ai_comment;
            // t is presumably global or available based on existing code structure
            const aiTitle = typeof t === "function" ? t("card.ai") : "AI Yorumu";
            aiHTML = `<div class="collapsible-header open" onclick="toggleCollapsible(this)"><h4><i class="fas fa-robot"></i> ${aiTitle}</h4><i class="fas fa-chevron-down collapse-icon"></i></div><div class="collapsible-body open"><div class="ai-content markdown-body">${parsedAI}</div></div>`;
        }

        card.innerHTML = `
            <div class="card-header">
                <div><span class="ticker-name">${res.ticker}</span></div>
                <div style="display:flex; align-items:center; gap:0.5rem"><span class="market-badge">${res.market || "?"}</span></div>
            </div>
            <div style="margin: 1rem 0; padding: 0.8rem; background: rgba(239, 68, 68, 0.1); border-left: 4px solid var(--danger); border-radius: 4px;">
                <p style="color:var(--danger); font-size:0.9rem; margin:0; font-weight:600;"><i class="fas fa-exclamation-circle"></i> Sistem Uyarısı</p>
                <p style="color:var(--text-main); font-size:0.85rem; margin:0.4rem 0 0.8rem 0;">${res.error}</p>
                <button class="btn btn-outline" style="font-size:0.75rem; padding:0.3rem 0.6rem;" onclick="retryAnalysis('${res.ticker}')"><i class="fas fa-redo"></i> Yeniden Dene</button>
            </div>
            ${aiHTML}
        `;
        return { card, chartId };
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
        const priceChange = fin.son_fiyat.degisim || 0;
        const flashClass = priceChange > 0 ? "fx-flash-up" : (priceChange < 0 ? "fx-flash-down" : "");
        metricsHTML += `<div class="metric-box no-modal"><div class="metric-label">Son Fiyat</div><div class="metric-value ${flashClass}">${fmtNum(fin.son_fiyat.fiyat)}</div></div>`;
        if (fin.son_fiyat.degisim !== undefined) metricsHTML += `<div class="metric-box no-modal"><div class="metric-label">Değişim</div><div class="metric-value ${colorClass(fin.son_fiyat.degisim)}">${fmtNum(fin.son_fiyat.degisim, "%")}</div></div>`;
    }
    if (fin.s5 !== null && fin.s5 !== undefined) metricsHTML += createMetricBox("5Y Getiri", fmtNum(fin.s5, "%"), "s5", colorClass(fin.s5));
    if (fin.s3 !== null && fin.s3 !== undefined) metricsHTML += `<div class="metric-box no-modal"><div class="metric-label">3Y Getiri</div><div class="metric-value ${colorClass(fin.s3)}">${fmtNum(fin.s3, "%")}</div></div>`;
    
    let marketText = res.market || "?";
    if (getLang() === "tr" && marketText === "US") marketText = "ABD";
    
    let sectorLabel = res.sector_localized ? res.sector_localized[getLang()] : (res.sector || "Bilinmiyor");
    let sectorBadge = `<span class="market-badge" style="font-size:0.65rem">${sectorLabel}</span>`;

    let compHTML = "";
    if (res.compliance_details) {
        const det = res.compliance_details;
        const haram = det.haram_income || {};
        const debt = det.debt || {};
        const liq = det.liquidity || {};
        
        const hClass = haram.pass ? "comp-pass" : "comp-fail";
        const dClass = debt.pass ? "comp-pass" : "comp-fail";
        const lClass = liq.pass ? "comp-pass" : "comp-fail";
        
        const hVal = Number(haram.value || 0);
        const dVal = Number(debt.value || 0);
        const lVal = Number(liq.value || 0);

        compHTML = `
        <div class="compliance-bars">
            <div class="comp-bar-row"><span>Haram Gelir (%${hVal.toFixed(2)})</span><span>Sınır: %5</span></div>
            <div class="comp-bar-bg"><div class="comp-bar-fill ${hClass}" style="width:${Math.min((hVal / 5) * 100, 100)}%"></div></div>
            
            <div class="comp-bar-row" style="margin-top:0.4rem"><span>Faizli Borç (%${dVal.toFixed(2)})</span><span>Sınır: %30</span></div>
            <div class="comp-bar-bg"><div class="comp-bar-fill ${dClass}" style="width:${Math.min((dVal / 30) * 100, 100)}%"></div></div>
            
            <div class="comp-bar-row" style="margin-top:0.4rem"><span>Likidite (%${lVal.toFixed(2)})</span><span>Sınır: %30</span></div>
            <div class="comp-bar-bg"><div class="comp-bar-fill ${lClass}" style="width:${Math.min((lVal / 30) * 100, 100)}%"></div></div>
        </div>`;
    }

    let radarHTML = "";
    if (res.radar_score) radarHTML = `<div class="radar-container"><canvas id="radar-${chartId}"></canvas></div>`;
    
    let gaugeHTML = "";
    if (res.technicals && res.technicals.gauge_score !== undefined) {
        gaugeHTML = `<div class="gauge-container"><div class="gauge-canvas-wrap"><canvas id="gauge-${chartId}"></canvas><div class="gauge-val" id="gauge-val-${chartId}">${res.technicals.gauge_score}</div></div><div class="gauge-label" id="gauge-lbl-${chartId}">Nötr</div></div>`;
    }
    
    let relPerfHTML = "";
    if (res.technicals && res.technicals.relative_performance) relPerfHTML = `<div class="relative-perf-container"><canvas id="relperf-${chartId}"></canvas></div>`;

    // renderTechnicals is global
    let techHTML = typeof renderTechnicals === "function" ? renderTechnicals(res.technicals) : ""; 

    let returnTableHTML = "";
    if (fin.ay && Object.keys(fin.ay).length > 0) {
        let rows = "";
        for (const [ay, d] of Object.entries(fin.ay)) {
            rows += `<tr><td>Son ${ay} ay</td><td class="${colorClass(d.g)}">${fmtNum(d.g, "%")}</td><td class="${colorClass(d.r)}">${fmtNum(d.r, "%")}</td><td>${fmtNum(d.enf, "%")}</td></tr>`;
        }
        returnTableHTML = `<div class="collapsible-header" onclick="toggleCollapsible(this)"><h4><i class="fas fa-chart-bar"></i> ${t("card.returns")}</h4><i class="fas fa-chevron-down collapse-icon"></i></div><div class="collapsible-body"><table class="return-table"><thead><tr><th>Dönem</th><th>Getiri</th><th>Reel</th><th>Enflasyon</th></tr></thead><tbody>${rows}</tbody></table></div>`;
    }

    let chartHTML = "";
    if ((fin.yg && Object.keys(fin.yg).length > 0) || res.klines) {
        chartHTML = `<div class="collapsible-header open" onclick="toggleCollapsible(this)"><h4><i class="fas fa-chart-line"></i> ${t("card.chart")}</h4><i class="fas fa-chevron-down collapse-icon"></i></div><div class="collapsible-body open"><div class="chart-container" id="${chartId}" style="height: 250px; margin-top: 0.5rem;"></div></div>`;
    }

    let aiHTML = "";
    if (res.ai_comment) {
        // marked is global
        const parsedAI = typeof marked !== "undefined" ? marked.parse(res.ai_comment) : res.ai_comment;
        aiHTML = `<div class="collapsible-header" onclick="toggleCollapsible(this)"><h4><i class="fas fa-robot"></i> ${t("card.ai")}</h4><i class="fas fa-chevron-down collapse-icon"></i></div><div class="collapsible-body"><div class="ai-content markdown-body">${parsedAI}</div></div>`;
    }

    let fundHTML = res.fund_note ? `<p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:0.75rem">${res.fund_note}</p>` : "";
    let errHTML = res.islamic_error ? `<p style="font-size:0.78rem; color:var(--warning); margin:0.5rem 0"><i class="fas fa-exclamation-triangle"></i> ${res.islamic_error}</p>` : "";
    errHTML += res.fin_error ? `<p style="font-size:0.78rem; color:var(--warning); margin:0.5rem 0"><i class="fas fa-exclamation-triangle"></i> ${res.fin_error}</p>` : "";

    let statusBadgeFinal = statusText !== "-" ? `<span class="${statusClass}">${statusText}</span>` : "";
    const nameBadge = (res.full_name && res.full_name !== res.ticker) ? `<span style="font-size:0.85rem; color:var(--text-muted); margin-left:0.5rem; font-weight:normal">${res.full_name}</span>` : "";

    // ── Sentiment & Islamic Risk (Phase 3) ──
    let sentimentHTML = "";
    let islamicRiskBarHTML = "";
    if (res.sentiment) {
        const sent = res.sentiment;
        const score = sent.score !== undefined ? sent.score : 50;
        const label = sent.sentiment_label || "Nötr";
        
        let color = "#eab308";
        if (score <= 35) color = "#ef4444";
        else if (score >= 66) color = "#22c55e";
        
        sentimentHTML = `
        <div class="sentiment-box" style="margin-top:0.75rem; padding:0.85rem; background:rgba(255,255,255,0.02); border-radius:8px; border:1px solid rgba(255,255,255,0.05);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
                <span style="font-size:0.78rem; color:var(--text-muted);"><i class="fas fa-newspaper"></i> Haber Duyarlılığı</span>
                <span style="font-size:0.82rem; font-weight:700; color:${color};">${label}</span>
            </div>
            <div class="progress-bar-bg" style="height:6px; background:rgba(255,255,255,0.08); border-radius:3px; overflow:hidden;">
                <div class="progress-bar-fill" style="width:${score}%; height:100%; background:${color};"></div>
            </div>
        </div>`;

        if (sent.islamic_risk_flag === true) {
            islamicRiskBarHTML = `
            <div class="islamic-risk-bar" style="margin: 0.5rem 0 0.85rem 0; padding:0.75rem 1rem; background:rgba(239, 68, 68, 0.12); border:1px solid rgba(239, 68, 68, 0.3); border-radius:8px; color:#f87171; font-size:0.82rem; font-weight:600; display:flex; align-items:center; gap:8px;">
                 <i class="fas fa-exclamation-triangle" style="font-size:0.95rem;"></i>
                 <span>🚨 İSLAMİ RİSK UYARISI: <span style="font-weight:normal;color:var(--text-main);">${sent.risk_reason || "Bilinmeyen risk"}</span></span>
            </div>`;
        }
    }

    card.innerHTML = `
        <div class="card-header"><div><span class="ticker-name">${res.ticker}</span>${nameBadge}</div><div style="display:flex; align-items:center; gap:0.5rem"><span class="market-badge">${marketText}</span>${sectorBadge}${statusBadgeFinal}</div></div>
        ${islamicRiskBarHTML}
        ${fundHTML}${errHTML}${compHTML}
        ${(radarHTML || gaugeHTML) ? `<div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem; align-items:center;">${radarHTML}${gaugeHTML}</div>` : ""}
        ${sentimentHTML}
        ${metricsHTML ? `<div class="metrics-grid">${metricsHTML}</div>` : ""}
        ${techHTML}${relPerfHTML}${chartHTML}${returnTableHTML}${aiHTML}
    `;
    
    return { card, chartId };
}

export function createNewsCard(item) {
    const title = item.title || "İsimsiz Haber";
    const link = item.link || "#";
    const sentiment = item.sentiment || "Neutral";
    const reason = item.reason || "";

    let color = "var(--text-muted)";
    let icon = "minus";
    if (sentiment.toLowerCase().includes("bull")) { color = "var(--success)"; icon = "arrow-trend-up"; }
    else if (sentiment.toLowerCase().includes("bear")) { color = "var(--danger)"; icon = "arrow-trend-down"; }

    const div = document.createElement("div");
    div.innerHTML = `
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
    return div.firstElementChild;
}

export function createMessageCard(message, type = "info") {
    const color = type === "error" ? "var(--danger)" : "var(--text-muted)";
    return `<div class="card" style="padding:1rem; text-align:center; color:${color}">${message}</div>`;
}

export function createComparisonTable(tickers, metrics) {
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
    return html;
}

// ── New Helpers for Pure Modularity ──

export function createSkeletonCard(t) {
    const card = document.createElement("div");
    card.className = "result-card glass-panel skeleton-card";
    card.id = `skeleton-${t}`;
    card.innerHTML = `
        <div class="card-header"><span class="ticker-name">${t}</span></div>
        <div class="skeleton-line"></div>
        <div class="skeleton-line medium"></div>
        <div class="skeleton-line short"></div>
    `;
    return card;
}

export function createLoadingSpinnerCard(message) {
    return `
    <div style="text-align:center; padding:2rem; color:var(--text-muted);">
        <i class="fas fa-spinner fa-spin fa-2x" style="margin-bottom:1rem"></i><br>
        ${message}
    </div>`;
}

export function createMacroCardHolder() {
    const container = document.createElement("div");
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
    return container;
}
