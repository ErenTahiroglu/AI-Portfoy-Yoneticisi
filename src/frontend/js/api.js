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
// MAIN ANALYSIS
// ═══════════════════════════════════════
async function runAnalysis(payload, endpoint) {
    const btn = document.getElementById("analyze-btn");
    const progressContainer = document.getElementById("progress-container");
    const progressFill = document.getElementById("progress-fill");
    const progressText = document.getElementById("progress-text");
    const results = document.getElementById("results");

    btn.disabled = true; results.classList.add("hidden");
    document.getElementById("loader").classList.add("hidden");
    progressContainer.classList.remove("hidden");

    let progress = 0;
    const pInt = setInterval(() => {
        progress += Math.random() * 5;
        if (progress > 95) progress = 95;
        progressFill.style.width = `${progress}%`;
        if (progress < 30) progressText.textContent = getLang() === "en" ? "Scanning markets..." : "Piyasalar taranıyor...";
        else if (progress < 60) progressText.textContent = getLang() === "en" ? "Analyzing financials..." : "Finansal veriler analiz ediliyor...";
        else if (progress < 90) progressText.textContent = payload.use_ai ? (getLang() === "en" ? "AI is generating report..." : "Yapay Zeka rapor hazırlıyor...") : (getLang() === "en" ? "Processing data..." : "Veriler işleniyor...");
        else progressText.textContent = getLang() === "en" ? "Finalizing results..." : "Sonuçlar derleniyor...";
    }, 400);

    await saveApiKeys();
    try {
        const res = await fetch(`${API_BASE}${endpoint}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        clearInterval(pInt); progressFill.style.width = "100%"; progressText.textContent = getLang() === "en" ? "Done!" : "Tamamlandı!";
        setTimeout(() => progressContainer.classList.add("hidden"), 500);

        if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || `Sunucu hatası (${res.status})`); }
        const data = await res.json();
        renderResults(data);
        showToast(`${(data.results || []).length} ${t("toast.analysisComplete")}`, "success");
    } catch (err) {
        clearInterval(pInt); progressContainer.classList.add("hidden");
        showToast(err.message, "error");
    }
    finally { btn.disabled = false; }
}

async function runFileAnalysis(file) {
    const btn = document.getElementById("analyze-btn");
    const progressContainer = document.getElementById("progress-container");
    const progressFill = document.getElementById("progress-fill");
    const progressText = document.getElementById("progress-text");
    const results = document.getElementById("results");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("use_ai", document.getElementById("use-ai-toggle").checked);
    formData.append("check_islamic", document.getElementById("check-islamic-toggle").checked);
    formData.append("check_financials", document.getElementById("check-financials-toggle").checked);
    formData.append("model", document.getElementById("model-select").value);
    formData.append("lang", getLang());
    const apiKey = document.getElementById("api-key").value;
    if (apiKey) formData.append("api_key", apiKey);
    const avKey = document.getElementById("av-api-key").value;
    if (avKey) formData.append("av_api_key", avKey);

    btn.disabled = true; results.classList.add("hidden");
    document.getElementById("loader").classList.add("hidden");
    progressContainer.classList.remove("hidden");

    let progress = 0;
    const pInt = setInterval(() => {
        progress += Math.random() * 5;
        if (progress > 95) progress = 95;
        progressFill.style.width = `${progress}%`;
        if (progress < 30) progressText.textContent = getLang() === "en" ? "Scanning file..." : "Dosya taranıyor...";
        else if (progress < 60) progressText.textContent = getLang() === "en" ? "Analyzing financials..." : "Finansal veriler analiz ediliyor...";
        else if (progress < 90) progressText.textContent = formData.get("use_ai") === "true" ? (getLang() === "en" ? "AI is generating report..." : "Yapay Zeka rapor hazırlıyor...") : (getLang() === "en" ? "Processing data..." : "Veriler işleniyor...");
        else progressText.textContent = getLang() === "en" ? "Finalizing results..." : "Sonuçlar derleniyor...";
    }, 400);

    await saveApiKeys();
    try {
        const res = await fetch(`${API_BASE}/api/analyze/file`, { method: "POST", body: formData });
        clearInterval(pInt); progressFill.style.width = "100%"; progressText.textContent = getLang() === "en" ? "Done!" : "Tamamlandı!";
        setTimeout(() => progressContainer.classList.add("hidden"), 500);

        if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || `Sunucu hatası (${res.status})`); }
        const data = await res.json();
        renderResults(data);
        showToast(`${(data.results || []).length} ${t("toast.analysisComplete")}`, "success");
    } catch (err) {
        clearInterval(pInt); progressContainer.classList.add("hidden");
        showToast(err.message, "error");
    }
    finally { btn.disabled = false; }
}
