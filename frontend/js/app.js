/**
 * 🧩 Frontend Orchestrator (app.js) — v6.0 (Deterministic Lifecycle)
 * ==========================================================================
 * Manages modular components and application startup sequence.
 */

import { toggleNotifications, markAllAlertsRead, fetchAutonomousAlerts } from './components/Notifications.js';
import { openMetricModal } from './components/Modals.js';
import { showComparison } from './components/Comparison.js';
import { initCopilot, renderMacroAI } from './components/Chat.js';
import { setupBacktestBindings, setupOptimization, setupRiskAnalysis, setupPaperTrades } from './components/Analysis.js';
import { initAdminDashboard } from './components/AdminDashboard.js';
import { runWizard } from './services/WizardService.js';
import { updateHeroCards, showEmptyPortfolioState, hideEmptyPortfolioState } from './components/HeroCardsComponent.js';
import { renderHeatmap } from './components/HeatmapComponent.js';
import { setupAuthModal, updateAuthUI } from './network/supabaseClient.js';
import { initOnboardingWizard, getUserProfile, skipWizard } from './services/OnboardingWizard.js';
import { checkServerHealth, runAnalysis } from './network/api.js';
import { initTheme, toggleTheme, loadApiKeys, saveApiKeys, setupAutocomplete, showToast } from './utils.js';

// ── Globals ──────────────────────────────────────────────────────────────
window.toggleNotifications = toggleNotifications;
window.markAllAlertsRead = markAllAlertsRead;
window.fetchAutonomousAlerts = fetchAutonomousAlerts;
window.openMetricModal = openMetricModal;
window.showComparison = showComparison;
window.renderMacroAI = renderMacroAI;
window.getUserProfile = getUserProfile;
window.skipOnboardingWizard = skipWizard;

// ── State Management v2 (Granular) ────────────────────────────────────────
const AppState = createStore({
    viewMode: localStorage.getItem("viewMode") || "beginner",
    isHalalOnly: localStorage.getItem("isHalalOnly") === "true",
    results: [],
    extras: null
});
window.AppState = AppState;

// 🔗 Granular Subscriptions
AppState.subscribe('viewMode', (val) => {
    document.body.classList.toggle("professional-mode", val === "pro");
    localStorage.setItem("viewMode", val);
    ['prof-mode-toggle', 'ui-mode-toggle'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.checked = (val === "pro");
    });
});

AppState.subscribe('isHalalOnly', (val) => {
    document.body.classList.toggle("halal-only", val);
    localStorage.setItem("isHalalOnly", val);
    const halalToggle = document.getElementById("check-islamic-toggle");
    if (halalToggle) halalToggle.checked = val;
});

AppState.subscribe('results', (val) => {
    const resultsSection = document.getElementById("results");
    if (!val || val.length === 0) {
        if (resultsSection) resultsSection.classList.add("hidden");
        return;
    }
    if (resultsSection) resultsSection.classList.remove("hidden");
    window.lastResults = val;
    
    // Non-blocking renders
    try { renderHeatmap(val); } catch (e) { console.error("Heatmap error:", e); }
});

AppState.subscribe('extras', (val) => {
    window.lastExtras = val;
    if (!val) return;
    
    const scoreVal = document.getElementById("weighted-return-val");
    if (val.weighted_return_5y !== undefined && scoreVal) {
        scoreVal.textContent = val.weighted_return_5y;
        document.getElementById("portfolio-score-badge")?.classList.remove("hidden");
    }

    updateHeroCards(AppState.results, val);
    
    if (val.optimized_weights) {
        // renderOptimization(val.optimized_weights, AppState.results);
    }
});

AppState.subscribe('systemStatus', (val) => {
    if (val === 'waking_up') {
        showToast("🚀 Sunucu uyanıyor (Free Tier), bu işlem ilk seferde 30-40 saniye sürebilir...", "info");
    }
});

// ── Application Lifecycle ──────────────────────────────────────────────────

class App {
    constructor() {
        this.phases = {
            1: "Core Infrastructure",
            2: "Authentication",
            3: "Services & Data",
            4: "UI & Bindings"
        };
    }

    async init() {
        console.log("🚀 Starting App Lifecycle...");
        try {
            await this.phase1_Core();
            await this.phase2_Auth();
            await this.phase3_Services();
            await this.phase4_UI();
            console.log("✅ App Initialized Successfully.");
        } catch (err) {
            this.handleInitError(err);
        }
    }

    // Phase 1: Core Setup (Theme, i18n, Error Handlers)
    async phase1_Core() {
        initTheme();
        if (typeof setLanguage === 'function') setLanguage(window.currentLang || 'tr');
        await loadApiKeys();
        
        // Global Error Boundary
        window.onerror = (msg, url, line) => {
            console.error(`[Global Error] ${msg} at ${url}:${line}`);
            return false;
        };
    }

    // Phase 2: Auth & Session
    async phase2_Auth() {
        setupAuthModal();
        if (!window.SupabaseAuth) return;

        const user = await window.SupabaseAuth.getUser();
        updateAuthUI(user);

        const landing = document.getElementById("landing-page");
        const sidebar = document.getElementById("sidebar");
        const mainContent = document.querySelector(".main-content");

        if (!user) {
            if (landing) landing.style.display = "flex";
            if (sidebar) sidebar.style.display = "none";
            if (mainContent) mainContent.style.display = "none";
        } else {
            document.getElementById("guest-logout-btn")?.style.setProperty("display", "none");
            
            await initOnboardingWizard((profile, wasShown) => {
                if (wasShown) {
                    if (landing) landing.style.display = "none";
                    if (sidebar) sidebar.style.display = "";
                    if (mainContent) mainContent.style.display = "";
                }
            });

            // Hydrate Portfolio
            const portfolio = await window.SupabaseAuth.loadPortfolio();
            if (!portfolio || portfolio.length === 0) {
                showEmptyPortfolioState();
            }
        }
    }

    // Phase 3: Services & Data Hydration
    async phase3_Services() {
        // Health Check (Async, don't block if slow)
        checkServerHealth().then(h => {
            const dot = document.getElementById("server-status-dot");
            if (dot) {
                dot.className = h.online ? "status-dot dot-green" : "status-dot dot-red";
                dot.title = h.online ? "Online" : "Offline";
            }
        });

        // Background Data
        if (window.SupabaseAuth) loadEquityCurve();
        
        // Worker check (Warm up)
        if (window.Worker) {
            console.log("🧵 Math Worker Ready");
        }
    }

    // Phase 4: UI Mount & Event Listeners
    async phase4_UI() {
        this.bindEvents();
        setupBacktestBindings();
        setupOptimization();
        setupRiskAnalysis();
        setupPaperTrades();
        setupAutocomplete();
        initCopilot();
        initAdminDashboard();

        // PWA Registration
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('./sw.js').catch(e => console.warn("SW Error", e));
        }
    }

    bindEvents() {
        document.getElementById("theme-toggle-btn")?.addEventListener("click", toggleTheme);
        document.getElementById("analyze-btn")?.addEventListener("click", () => this.handleAnalyze());
        
        const aiToggle = document.getElementById("use-ai-toggle");
        aiToggle?.addEventListener("change", () => {
            const isAI = aiToggle.checked;
            document.getElementById("api-key").disabled = !isAI;
            document.getElementById("gemini-key-group")?.classList.toggle("disabled", !isAI);
        });

        const handleModeToggle = (e) => AppState.viewMode = e.target.checked ? "pro" : "beginner";
        document.getElementById("prof-mode-toggle")?.addEventListener("change", handleModeToggle);
        document.getElementById("ui-mode-toggle")?.addEventListener("change", handleModeToggle);
        document.getElementById("check-islamic-toggle")?.addEventListener("change", (e) => AppState.isHalalOnly = e.target.checked);
        
        document.getElementById("api-key")?.addEventListener("blur", saveApiKeys);
        document.getElementById("btn-run-wizard")?.addEventListener("click", runWizard);
        document.getElementById("compare-btn")?.addEventListener("click", showComparison);

        // Mobile Menu
        const mobBtn = document.getElementById("mobile-menu-btn");
        const sidebar = document.getElementById("sidebar");
        mobBtn?.addEventListener("click", (e) => {
            e.stopPropagation();
            sidebar?.classList.toggle("open");
        });
    }

    async handleAnalyze() {
        hideEmptyPortfolioState();
        const text = document.getElementById("ticker-input")?.value.trim();
        if (!text) return showToast("Hisse sembolü giriniz", "warning");

        const tickers = text.split(/[\s,;]+/).filter(t => t).map(t => t.toUpperCase());
        const payload = {
            tickers,
            use_ai: document.getElementById("use-ai-toggle")?.checked,
            api_key: document.getElementById("api-key")?.value,
            check_islamic: document.getElementById("check-islamic-toggle")?.checked,
            check_financials: document.getElementById("check-financials-toggle")?.checked,
            model: document.getElementById("model-select")?.value || "gemini-2.5-flash",
            lang: window.getLang ? window.getLang() : 'tr'
        };

        runAnalysis(payload, "/api/analyze");
    }

    handleInitError(err) {
        console.error("❌ Critical Initialization Error:", err);
        showToast("Uygulama başlatılırken bir hata oluştu. Lütfen sayfayı yenileyin.", "error");
        
        const loader = document.getElementById("loader");
        if (loader) {
            loader.innerHTML = `
                <div class="error-state" style="text-align:center; padding:2rem;">
                    <i class="fas fa-exclamation-triangle" style="font-size:3rem; color:var(--danger); margin-bottom:1rem;"></i>
                    <h3>Başlatma Hatası</h3>
                    <p>${err.message}</p>
                    <button class="btn-primary" onclick="location.reload()">Tekrar Dene</button>
                </div>
            `;
        }
    }
}

// 🚀 Boot
const app = new App();
document.addEventListener("DOMContentLoaded", () => app.init());

// ── Legacy Functions (kept for inline HTML calls) ──────────────────────────
window.renderSingleCard = function(item) {
    document.getElementById("results")?.classList.remove("hidden");
    document.getElementById(`skeleton-${item.ticker}`)?.remove();
};

async function loadEquityCurve() {
    try {
        const session = await window.SupabaseAuth?.getValidSession();
        if (!session) return;
        
        const data = await http.get('/api/portfolio/history');
        if (data && data.length > 0) {
            const widget = document.getElementById("equity-curve-widget");
            widget?.classList.remove("hidden");
            if (typeof createEquityCurveChart === "function") {
                createEquityCurveChart("equity-chart-container", data);
            }
        }
    } catch (e) {
        console.warn("Equity Curve failed:", e);
    }
}

// ── Secret Admin Bypass ──────────────────────────────────────────────────
let secretClicks = 0;
document.addEventListener("click", (e) => {
    if (e.target.closest(".main-title")) {
        secretClicks++;
        if (secretClicks >= 5) {
            const current = localStorage.getItem("admin_bypass") === "true";
            localStorage.setItem("admin_bypass", !current ? "true" : "false");
            showToast(`Sistem: ${!current ? "Geliştirici" : "Standart"}`, "info");
            secretClicks = 0;
            setTimeout(() => window.location.reload(), 1000);
        }
    }
});
