const IS_LOCAL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const API_BASE = IS_LOCAL ? "" : "https://ai-portfoy-yoneticisi.onrender.com";
let lastResults = null;
let lastExtras = null;
let chartInstances = {};

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
                    dropdown.innerHTML = data.suggestions.map(s => `<div class="autocomplete-item" data-ticker="${s.ticker}">
                        <div style="flex:1; display:flex; align-items:center; gap:8px;" class="autocomplete-clickable">
                            <span class="ticker-symbol">${s.ticker}</span><span class="ticker-name">${s.name}</span>
                        </div>
                        <i class="fas fa-info-circle ticker-info-btn" style="color:var(--primary); padding:8px;" data-ticker="${s.ticker}"></i>
                    </div>`).join("");
                    dropdown.classList.remove("hidden");

                    dropdown.querySelectorAll(".autocomplete-clickable").forEach(el => {
                        el.addEventListener("click", (e) => {
                            const ticker = e.currentTarget.parentElement.dataset.ticker;
                            words[words.length - 1] = ticker;
                            textarea.value = words.join(", ") + ", ";
                            dropdown.classList.add("hidden");
                            textarea.focus();
                        });
                    });

                    dropdown.querySelectorAll(".ticker-info-btn").forEach(btn => {
                        btn.addEventListener("click", (e) => {
                            e.stopPropagation();
                            showTickerQuickModal(e.currentTarget.dataset.ticker);
                        });
                    });
                } else { dropdown.classList.add("hidden"); }
            } catch { dropdown.classList.add("hidden"); }
        }, 200);
    });
    textarea.addEventListener("blur", () => setTimeout(() => dropdown.classList.add("hidden"), 200));
}

// ═══════════════════════════════════════
// COLLAPSIBLE SECTIONS
// ═══════════════════════════════════════
function toggleCollapsible(header) {
    header.classList.toggle("open");
    header.nextElementSibling.classList.toggle("open");
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

async function saveApiKeys() {
    const gemini = document.getElementById("api-key").value;
    const av = document.getElementById("av-api-key").value;
    if (gemini) {
        localStorage.setItem("_gk", await encryptApiKey(gemini));
        const icon = document.getElementById("api-key-saved-icon");
        if (icon) { icon.classList.remove("hidden"); setTimeout(() => icon.classList.add("hidden"), 3000); }
    }
    if (av) {
        localStorage.setItem("_ak", await encryptApiKey(av));
        const icon = document.getElementById("av-key-saved-icon");
        if (icon) { icon.classList.remove("hidden"); setTimeout(() => icon.classList.add("hidden"), 3000); }
    }
}

async function loadApiKeys() {
    const gk = await decryptApiKey(localStorage.getItem("_gk") || "");
    const ak = await decryptApiKey(localStorage.getItem("_ak") || "");
    if (gk) {
        document.getElementById("api-key").value = gk;
        const icon = document.getElementById("api-key-saved-icon");
        if (icon) icon.classList.remove("hidden");
    }
    if (ak) {
        document.getElementById("av-api-key").value = ak;
        const icon = document.getElementById("av-key-saved-icon");
        if (icon) icon.classList.remove("hidden");
    }
}

// ═══════════════════════════════════════
// TICKER QUICK VIEW MODAL
// ═══════════════════════════════════════
async function showTickerQuickModal(ticker) {
    let overlay = document.getElementById("ticker-modal-overlay");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "ticker-modal-overlay";
        overlay.className = "modal-overlay";
        document.body.appendChild(overlay);
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) overlay.remove();
        });
    }

    // Yükleme durumu (Skeleton UI)
    overlay.innerHTML = `
        <div class="modal-content glass-panel" style="animation: slideUpFade 0.3s ease;">
            <button class="modal-close" onclick="document.getElementById('ticker-modal-overlay').remove()"><i class="fas fa-times"></i></button>
            <h3 style="margin-bottom:1rem;font-size:1.2rem;color:var(--text-main);"><i class="fas fa-search"></i> ${ticker} Hızlı Görünüm</h3>
            <div class="skeleton-title" style="width: 40%"></div>
            <div class="skeleton-box" style="margin-bottom: 1rem;"></div>
            <div class="skeleton-text"></div>
            <div class="skeleton-text" style="width: 80%"></div>
        </div>
    `;

    try {
        const payload = {
            tickers: [ticker],
            use_ai: false,
            api_key: "",
            av_api_key: "",
            model: "gemini-2.5-flash",
            check_islamic: document.getElementById("check-islamic-toggle").checked,
            check_financials: true,
            lang: getLang()
        };
        const res = await fetch(`${API_BASE}/api/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        const r = data.results && data.results[0];

        if (!r || r.error) {
            overlay.innerHTML = `
                <div class="modal-content glass-panel">
                    <button class="modal-close" onclick="document.getElementById('ticker-modal-overlay').remove()"><i class="fas fa-times"></i></button>
                    <h3 style="margin-bottom:1rem;"><i class="fas fa-exclamation-triangle" style="color:var(--danger)"></i> ${ticker}</h3>
                    <p style="color:var(--danger);">${r?.error || "Veri alınamadı."}</p>
                </div>
            `;
            return;
        }

        const fin = r.financials || {};
        const val = r.valuation || {};
        const price = fin.son_fiyat?.fiyat ? fin.son_fiyat.fiyat.toFixed(2) : "-";
        const ccy = fin.son_fiyat?.para_birimi || "";
        const mcap = val.market_cap ? formatMarketCap(val.market_cap) : "-";

        let statusText = r.status || "-";
        if (getLang() === "en") {
            if (statusText === "Uygun") statusText = "Compliant";
            else if (statusText === "Uygun Değil") statusText = "Non-Compliant";
            else if (statusText === "Katılım Fonu Değil") statusText = "Non-Participation";
        }
        const statusHTML = statusText !== "-" ? `<span style="padding:0.2rem 0.5rem; border-radius:4px; font-size:0.75rem; background:rgba(34,197,94,0.1); color:var(--success); border:1px solid rgba(34,197,94,0.2);">${statusText}</span>` : "";

        overlay.innerHTML = `
            <div class="modal-content glass-panel" style="animation: slideUpFade 0.3s ease;">
                <button class="modal-close" onclick="document.getElementById('ticker-modal-overlay').remove()"><i class="fas fa-times"></i></button>
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1.5rem;">
                    <div>
                        <h2 style="font-size:1.5rem;font-weight:800;letter-spacing:-0.5px;color:var(--text-main); margin-bottom:0.2rem;">${r.ticker}</h2>
                        <div style="font-size:0.85rem;color:var(--text-muted);">${r.full_name || fin.ad || ""}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:1.5rem;font-weight:700;color:var(--primary);">${price} ${ccy}</div>
                        ${statusHTML}
                    </div>
                </div>
                
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-bottom:1.5rem;">
                    <div style="background:rgba(14,165,233,0.05); padding:1rem; border-radius:8px; border:1px solid var(--glass-border);">
                        <div style="font-size:0.7rem; color:var(--text-muted); text-transform:uppercase;">P/E</div>
                        <div style="font-size:1.1rem; font-weight:600; color:var(--text-main);">${fmtNum(val.pe)}</div>
                    </div>
                    <div style="background:rgba(14,165,233,0.05); padding:1rem; border-radius:8px; border:1px solid var(--glass-border);">
                        <div style="font-size:0.7rem; color:var(--text-muted); text-transform:uppercase;">P/B</div>
                        <div style="font-size:1.1rem; font-weight:600; color:var(--text-main);">${fmtNum(val.pb)}</div>
                    </div>
                    <div style="background:rgba(14,165,233,0.05); padding:1rem; border-radius:8px; border:1px solid var(--glass-border);">
                        <div style="font-size:0.7rem; color:var(--text-muted); text-transform:uppercase;">Piyasa Değeri</div>
                        <div style="font-size:1.1rem; font-weight:600; color:var(--text-main);">${mcap}</div>
                    </div>
                    <div style="background:rgba(14,165,233,0.05); padding:1rem; border-radius:8px; border:1px solid var(--glass-border);">
                        <div style="font-size:0.7rem; color:var(--text-muted); text-transform:uppercase;">Beta</div>
                        <div style="font-size:1.1rem; font-weight:600; color:var(--text-main);">${fmtNum(val.beta)}</div>
                    </div>
                </div>
                
                <button class="btn-primary" onclick="
                    const tarea = document.getElementById('ticker-input');
                    let words = tarea.value.split(/[\\s,;]+/);
                    words = words.filter(w=>w.trim());
                    if (words[words.length-1] !== '${r.ticker}') words.push('${r.ticker}');
                    tarea.value = words.join(', ') + ', ';
                    document.getElementById('ticker-modal-overlay').remove();
                    tarea.focus();
                ">
                    <i class="fas fa-plus"></i> Listeye Ekle
                </button>
            </div>
        `;
    } catch (err) {
        overlay.innerHTML = `
            <div class="modal-content glass-panel">
                <button class="modal-close" onclick="document.getElementById('ticker-modal-overlay').remove()"><i class="fas fa-times"></i></button>
                <h3 style="margin-bottom:1rem;color:var(--danger)"><i class="fas fa-times-circle"></i> Hatası</h3>
                <p>Beklenmeyen bir hata oluştu: ${err.message}</p>
            </div>
        `;
    }
}
