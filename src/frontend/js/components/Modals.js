// ═══════════════════════════════════════
// METRIC DETAILS & MODALS MODULE
// ═══════════════════════════════════════

export const METRIC_DESCRIPTIONS = {
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

export function openMetricModal(ticker, metricKey, label, aiCommentRaw) {
    const modal = document.getElementById("metric-modal");
    const title = document.getElementById("metric-detail-title");
    const tickerEl = document.getElementById("metric-detail-ticker");
    const desc = document.getElementById("metric-static-desc");
    const aiBox = document.getElementById("metric-ai-insight");

    if (!modal || !title || !tickerEl || !desc || !aiBox) return;

    title.textContent = label;
    tickerEl.textContent = ticker;

    const lang = typeof getLang === "function" ? getLang() : "tr";
    desc.textContent = METRIC_DESCRIPTIONS[metricKey] ? METRIC_DESCRIPTIONS[metricKey][lang] : "Bu metrik hakkında detaylı bilgi bulunmuyor.";

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
