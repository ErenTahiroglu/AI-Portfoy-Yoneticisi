// ══════════════════════════════════════════════════════════════════════════
// 🧩 Puzzle Parça: Frontend Orkestratörü (app.js) — v5.0
// ==========================================================================
// ES6 Modülleri kullanarak parçalanmış component'leri yönetir ve başlatır.
// ══════════════════════════════════════════════════════════════════════════

import { toggleNotifications, markAllAlertsRead, fetchAutonomousAlerts } from './components/Notifications.js';
import { openMetricModal } from './components/Modals.js';
import { showComparison } from './components/Comparison.js';
import { initCopilot, renderMacroAI } from './components/Chat.js';
import { setupBacktestBindings, fetchAndRenderSignals, setupOptimization, setupRiskAnalysis, setupPaperTrades } from './components/Analysis.js';
import { initAdminDashboard } from './components/AdminDashboard.js';
import { runWizard } from './services/WizardService.js';
import { updateHeroCards } from './components/HeroCardsComponent.js';
import { renderHeatmap } from './components/HeatmapComponent.js';
import { setupAuthModal, updateAuthUI } from './supabaseClient.js';

// ── Globale Bağlama (Backward Compatibility) ──────────────────────────────
window.toggleNotifications = toggleNotifications;
window.markAllAlertsRead = markAllAlertsRead;
window.fetchAutonomousAlerts = fetchAutonomousAlerts;
window.openMetricModal = openMetricModal;
window.showComparison = showComparison;
window.renderMacroAI = renderMacroAI;

const API_BASE = window.API_BASE;

// ── State Yönetimi ────────────────────────────────────────────────────────
const AppState = createStore({
    viewMode: localStorage.getItem("viewMode") || "beginner",
    isHalalOnly: localStorage.getItem("isHalalOnly") === "true",
    results: [],
    extras: null
});
window.AppState = AppState;

AppState.subscribe((prop, val, oldValue) => {
    if (prop === "viewMode") {
        document.body.classList.toggle("professional-mode", val === "pro");
        localStorage.setItem("viewMode", val);
        const profToggle = document.getElementById("prof-mode-toggle");
        if (profToggle) profToggle.checked = (val === "pro");
        const uiToggle = document.getElementById("ui-mode-toggle");
        if (uiToggle) uiToggle.checked = (val === "pro");
    }
    
    if (prop === "isHalalOnly") {
        document.body.classList.toggle("halal-only", val);
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

        if (!(oldValue && val.length > oldValue.length)) {
            if (grid) grid.innerHTML = "";
            if (summaryBody) summaryBody.innerHTML = "";
            val.forEach((res, idx) => appendResultItem(res, idx, grid, summaryBody));
        }
        window.lastResults = val;
        try { renderHeatmap(val); renderScenarios(val); } catch (e) { }
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
            }
        } catch (e) { }

        try { renderExtras(val); updateHeroCards(AppState.results, val); } catch (e) { }

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

// ── Yardımcı Render Fonksiyonu ───────────────────────────────────────────
window.renderSingleCard = function(item) {
    const grid = document.getElementById("results-grid");
    const summaryBody = document.getElementById("summary-table-body");
    const resultsSection = document.getElementById("results");

    if (resultsSection) resultsSection.classList.remove("hidden");

    const skeleton = document.getElementById(`skeleton-${item.ticker}`);
    if (skeleton) skeleton.remove();

    const idx = AppState.results.length; 
    appendResultItem(item, idx, grid, summaryBody);
}

async function appendResultItem(res, idx, grid, summaryBody) {
    const { createCard, createSummaryRow } = await import('./components/CardComponent.js');
    if (summaryBody) summaryBody.appendChild(createSummaryRow(res));
    if (grid) {
        const { card, chartId } = createCard(res, idx);
        grid.appendChild(card);
        if (res.error) return;

        setTimeout(() => {
            if (typeof createTVChart === "function") createTVChart(chartId, res);
            if (res.radar_score && typeof createRadarChart === "function") createRadarChart(`radar-${chartId}`, res);
            if (res.technicals && res.technicals.gauge_score !== undefined && typeof createGaugeChart === "function") createGaugeChart(`gauge-${chartId}`, res.technicals.gauge_score, `gauge-lbl-${chartId}`, `gauge-val-${chartId}`);
            if (res.technicals && res.technicals.relative_performance && typeof createRelativePerformanceChart === "function") createRelativePerformanceChart(`relperf-${chartId}`, res.technicals.relative_performance);
        }, 50);
    }
}

// ── DOMContentLoaded Event Listener ──────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
    // ── Auth Check for Landing Page ──
    if (window.SupabaseAuth) {
        try {
            const user = await window.SupabaseAuth.getUser();
            const landing = document.getElementById("landing-page");
            const sidebar = document.getElementById("sidebar");
            const mainContent = document.querySelector(".main-content");

            // Fix: updateAuthUI handles button state reactively (both logged-in and guest cases)
            updateAuthUI(user);

            if (!user) {
                if (landing) landing.style.display = "flex";
                if (sidebar) sidebar.style.display = "none";
                if (mainContent) mainContent.style.display = "none";
                const mobBtn = document.getElementById("mobile-menu-btn");
                if (mobBtn) mobBtn.style.display = "none";
            } else {
                const guestLogoutBtn = document.getElementById("guest-logout-btn");
                if (guestLogoutBtn) guestLogoutBtn.style.display = "none";
            }
        } catch (e) {
            console.error("Auth status loading error:", e);
        }
    }

    // Fix 1: setup auth modal events (wires form, tabs, close, onAuthStateChange)
    setupAuthModal();

    initTheme();
    setLanguage(currentLang);
    await loadApiKeys();

    // Server Health Check
    const statusDot = document.getElementById("server-status-dot");
    if (statusDot) {
        statusDot.className = "status-dot dot-yellow"; 
        checkServerHealth().then(h => {
            if (h.online) { statusDot.className = "status-dot dot-green"; statusDot.title = "Online"; }
            else { showToast("Sunucu uyandırılıyor (Free Tier)...", "info"); }
        });
    }

    // Static Event Listeners
    document.getElementById("theme-toggle-btn").addEventListener("click", toggleTheme);
    document.getElementById("metric-modal-close").addEventListener("click", () => document.getElementById("metric-modal").classList.add("hidden"));
    
    // AI Toggles
    const aiToggle = document.getElementById("use-ai-toggle");
    aiToggle.addEventListener("change", () => {
        const isAI = aiToggle.checked;
        document.getElementById("api-key").disabled = !isAI;
        document.getElementById("gemini-key-group").classList.toggle("disabled", !isAI);
        document.getElementById("gemini-model-group").classList.toggle("disabled", !isAI);
    });

    document.getElementById("api-key").addEventListener("blur", saveApiKeys);
    document.getElementById("av-api-key").addEventListener("blur", saveApiKeys);

    const handleModeToggle = async (e) => {
        AppState.viewMode = e.target.checked ? "pro" : "beginner";
    };

    const profToggle = document.getElementById("prof-mode-toggle");
    if (profToggle) profToggle.addEventListener("change", handleModeToggle);

    const uiToggle = document.getElementById("ui-mode-toggle");
    if (uiToggle) uiToggle.addEventListener("change", handleModeToggle);

    const halalToggle = document.getElementById("check-islamic-toggle");
    if (halalToggle) halalToggle.addEventListener("change", (e) => AppState.isHalalOnly = e.target.checked);

    // Analyze Click Handler
    const analyzeBtn = document.getElementById("analyze-btn");
    analyzeBtn.addEventListener("click", () => {
        const checkIslamic = document.getElementById("check-islamic-toggle").checked;
        const checkFinancials = document.getElementById("check-financials-toggle").checked;
        const useAI = aiToggle.checked;
        const apiKey = document.getElementById("api-key").value;
        const text = document.getElementById("ticker-input").value.trim();

        if (useAI && !apiKey) { showToast("AI Analizi için API key gereklidir", "warning"); return; }
        if (!text) { showToast("Hisse sembolü giriniz", "warning"); return; }
        
        const tickers = text.split(/[\s,;]+/).filter(t => t).map(t => t.toUpperCase());
        runAnalysis({ tickers, use_ai: useAI, api_key: apiKey, check_islamic: checkIslamic, check_financials: checkFinancials }, "/api/analyze");
    });

    document.getElementById("btn-run-wizard").addEventListener("click", runWizard);
    document.getElementById("compare-btn").addEventListener("click", showComparison);

    setupAutocomplete();
    initCopilot();
});

async function loadEquityCurve() {
    if (!window.SupabaseAuth) return;
    try {
        const session = await window.SupabaseAuth.getValidSession();
        if (!session) return;
        const token = session.access_token;
        
        const resp = await fetch(`${API_BASE}/api/portfolio/history`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await resp.json();
        if (data && data.length > 0) {
            const widget = document.getElementById("equity-curve-widget");
            if (widget) widget.classList.remove("hidden");
            if (typeof createEquityCurveChart === "function") {
                createEquityCurveChart("equity-chart-container", data);
            }
        }
    } catch (e) {
        console.error("Equity Curve load failed:", e);
        const widget = document.getElementById("equity-curve-widget");
        if (widget) {
            widget.classList.remove("hidden");
            const container = document.getElementById("equity-chart-container");
            if (container) {
                container.innerHTML = `<div style="padding:1.5rem; text-align:center; color:var(--text-muted); font-size:0.85rem;"><i class="fas fa-exclamation-triangle" style="color:var(--warning)"></i> Geçmiş bakiye grafiği yüklenemedi.</div>`;
            }
        }
    }
}

// ── Bindings & Triggers ───────────────────────────────────────────────────
setTimeout(() => {
    setupBacktestBindings();
    setupOptimization();
    setupRiskAnalysis();
    setupPaperTrades();
    if (typeof setupSupabaseAuth === "function") setupSupabaseAuth();
    
    // Yükleme Sonrası Kayıtlı Grafik Çek
    loadEquityCurve();

    // Admin Dashboard Kontrolü
    initAdminDashboard();

    // ── Global Paywall Interceptor (402 Payment Required) ──
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        const rs = await originalFetch(...args);
        if (rs.status === 402) {
             import('./components/Modals.js').then(m => m.openPaywallModal());
        }
        return rs;
    };
}, 1000);

function renderResults(data) {
    AppState.results = data.results || [];
    if (data.extras) AppState.extras = data.extras;
}

// ── Secret Admin Bypass Trigger (5-clicks on title) ──────────────────────
let secretClicks = 0;
document.addEventListener("click", (e) => {
    if (e.target.closest(".main-title")) {
        secretClicks++;
        if (secretClicks >= 5) {
            const current = localStorage.getItem("admin_bypass") === "true";
            localStorage.setItem("admin_bypass", !current ? "true" : "false");
            if (typeof showToast === "function") {
                showToast(`Sistem Durumu: ${!current ? "Yönetici" : "Normal"}`, "info");
            }
            secretClicks = 0;
            setTimeout(() => window.location.reload(), 1000);
        }
        setTimeout(() => { if (secretClicks > 0) secretClicks--; }, 3000);
    }
});
