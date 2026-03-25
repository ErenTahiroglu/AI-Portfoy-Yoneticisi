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

    // Portföy Skoru
    if (extras && extras.weighted_return_5y !== undefined) {
        const val = parseFloat(extras.weighted_return_5y);
        const color = val >= 0 ? "var(--success)" : "var(--danger)";
        if (scoreVal) scoreVal.innerHTML = `<span style="color:${color}">%${val.toFixed(1)}</span>`;
    } else {
        if (scoreVal) scoreVal.textContent = "-";
    }

    // En İyi Hisse
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
            bestVal.innerHTML = `<span class="ticker-box">${bestStock}</span> <small style="color:var(--success); font-weight:700;">(+%${maxRet.toFixed(1)})</small>`;
        } else {
            bestVal.textContent = "-";
        }
    }

    // Risk Seviyesi
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
            let riskIcon = "fa-shield-check";
            
            if (avgRisk > 30) { 
                riskLabel = "Yüksek"; 
                riskColor = "var(--danger)"; 
                riskIcon = "fa-radiation";
            } else if (avgRisk > 15) { 
                riskLabel = "Orta"; 
                riskColor = "var(--warning)"; 
                riskIcon = "fa-exclamation-triangle";
            }
            
            riskVal.innerHTML = `<span style="color:${riskColor}">${riskLabel}</span> <small>(MaxDD: %${avgRisk.toFixed(1)})</small>`;
            
            // Update Icon based on risk
            const riskCardIcon = document.querySelector('#hero-risk-val').closest('.hero-card').querySelector('.hero-icon i');
            if (riskCardIcon) {
                riskCardIcon.className = `fas ${riskIcon}`;
                riskCardIcon.style.color = riskColor;
            }
        } else {
            riskVal.textContent = "-";
        }
    }
}
