// ═══════════════════════════════════════
// HERO CARDS COMPONENT
// ═══════════════════════════════════════

export function updateHeroCards(results, extras) {
    const cardsContainer = document.getElementById("hero-cards");
    const scoreVal = document.getElementById("hero-score-val");
    const bestVal = document.getElementById("hero-best-val");
    const riskVal = document.getElementById("hero-risk-val");

    if (!cardsContainer) return; // Guard

    if (!results || results.length === 0) {
        cardsContainer.classList.add("hidden");
        return;
    }

    cardsContainer.classList.remove("hidden");

    // Portföy Skoru (Ağırlıklı Getiri veya Ortalama)
    if (extras && extras.weighted_return_5y !== undefined) {
        if (scoreVal) scoreVal.textContent = `%${extras.weighted_return_5y}`;
    } else {
        if (scoreVal) scoreVal.textContent = "-";
    }

    // En İyi Hisse (5Y getiriye göre veya Son Değişim)
    let bestStock = null;
    let maxRet = -Infinity;
    results.forEach(r => {
        if (!r.error && r.financials && r.financials.s5 !== undefined && r.financials.s5 !== null) {
            let currentRet = parseFloat(r.financials.s5);
            if (!isNaN(currentRet) && currentRet > maxRet) {
                maxRet = currentRet;
                bestStock = r.ticker;
            }
        }
    });
    
    if (bestVal) {
        if (bestStock) {
            bestVal.innerHTML = `${bestStock} <span style="font-size:0.8rem;color:var(--success)">(%${maxRet.toFixed(1)})</span>`;
        } else {
            bestVal.textContent = "-";
        }
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

    if (riskVal) {
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
}
