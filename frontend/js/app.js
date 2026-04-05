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
import { httpClient } from './network/HttpClient.js';
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
let initialViewMode = localStorage.getItem("viewMode") || "beginner";
if (initialViewMode === "pro" && localStorage.getItem("admin_bypass") !== "true") {
    initialViewMode = "beginner";
    localStorage.setItem("viewMode", "beginner");
}

const AppState = createStore({
    viewMode: initialViewMode,
    isHalalOnly: localStorage.getItem("isHalalOnly") === "true",
    commissionRate: parseFloat(localStorage.getItem("commissionRate")) || 0.2,
    slippageRate: parseFloat(localStorage.getItem("slippageRate")) || 0.1,
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

AppState.subscribe('results', async (val) => {
    const resultsSection = document.getElementById("results");
    if (!val || val.length === 0) {
        if (resultsSection) resultsSection.classList.add("hidden");
        return;
    }
    if (resultsSection) resultsSection.classList.remove("hidden");
    window.lastResults = val;
    
    // Non-blocking renders
    try { renderHeatmap(val); } catch (e) { console.error("Heatmap error:", e); }

    // Client-Side Persistence
    if (val && val.length > 0 && typeof window.setCache === 'function') {
        window.setCache('last_known_results', val);
    }
});

AppState.subscribe('extras', async (val) => {
    window.lastExtras = val;
    if (!val) return;
    
    const scoreVal = document.getElementById("weighted-return-val");
    if (val.weighted_return_5y !== undefined && scoreVal) {
        scoreVal.textContent = val.weighted_return_5y;
        document.getElementById("portfolio-score-badge")?.classList.remove("hidden");
    }

    updateHeroCards(AppState.results, val);
    
    // Client-Side Persistence
    if (typeof window.setCache === 'function') {
        window.setCache('last_known_extras', val);
    }
});

AppState.subscribe('systemStatus', (val) => {
    let syncIndicator = document.getElementById("sync-indicator");
    if (!syncIndicator) {
        syncIndicator = document.createElement("div");
        syncIndicator.id = "sync-indicator";
        syncIndicator.className = "sync-indicator";
        document.body.appendChild(syncIndicator);
    }

    if (val === 'waking_up' || val === 'syncing') {
        syncIndicator.innerHTML = '<i class="fas fa-sync fa-spin"></i> Senkronize ediliyor...';
        syncIndicator.classList.add("active");
    } else if (val === 'ready') {
        syncIndicator.innerHTML = '<i class="fas fa-check-circle" style="color:var(--success)"></i> Güncel';
        setTimeout(() => syncIndicator.classList.remove("active"), 2000);
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
            
            try {
                await initOnboardingWizard((profile, wasShown) => {
                    if (wasShown) {
                        if (landing) landing.style.display = "none";
                        if (sidebar) sidebar.style.display = "";
                        if (mainContent) mainContent.style.display = "";
                    }
                });

                // Hydrate Portfolio & Settings
                const portfolio = await window.SupabaseAuth.loadPortfolio();
                if (!portfolio || portfolio.length === 0) {
                    showEmptyPortfolioState();
                }

                // Sync user settings (including new rates)
                const settings = await httpClient.get('/api/user-settings');
                if (settings) {
                    AppState.commissionRate = (settings.commission_rate * 100) || 0.2;
                    AppState.slippageRate = (settings.slippage_rate * 100) || 0.1;
                    
                    const commInput = document.getElementById("settings-commission-rate");
                    const slipInput = document.getElementById("settings-slippage-rate");
                    if (commInput) commInput.value = AppState.commissionRate;
                    if (slipInput) slipInput.value = AppState.slippageRate;
                }
            } catch (err) {
                console.warn("🛡️ Auth hydration failed (Invalid token or expired):", err);
                if (err.status === 401 || err.status === 403 || err.message?.includes("token")) {
                    console.log("Stale session detected, auto-logging out...");
                    if (window.SupabaseAuth && window.SupabaseAuth.signOut) {
                        await window.SupabaseAuth.signOut();
                    }
                    window.location.reload();
                    return; // Halt further init
                }
                throw err; // If it's a critical non-auth error, let it crash or show fallback
            }
        }
    }

    // Phase 3: Services & Data Hydration
    async phase3_Services() {
        // ⚡ Zero-Latency UX: Instant Hydration from Cache
        if (typeof window.getCache === 'function') {
            const cachedResults = await window.getCache('last_known_results');
            const cachedExtras = await window.getCache('last_known_extras');
            
            if (cachedResults && cachedResults.length > 0) {
                console.log("⚡ SWR: Yüklendi (Results)");
                AppState.results = cachedResults;
            }
            if (cachedExtras) {
                console.log("⚡ SWR: Yüklendi (Extras)");
                AppState.extras = cachedExtras;
            }
        }

        // Background Health Check (Revalidate)
        AppState.systemStatus = 'syncing';
        checkServerHealth().then(h => {
            const dot = document.getElementById("server-status-dot");
            if (dot) {
                dot.className = h.online ? "status-dot dot-green" : "status-dot dot-red";
                dot.title = h.online ? "Online" : "Offline";
            }
            if (h.online) AppState.systemStatus = 'ready';
        }).catch(() => {
            // Sessiz fail
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

        const handleModeToggle = (e) => {
            const isDev = localStorage.getItem("admin_bypass") === "true";
            if (e.target.checked && !isDev) {
                e.preventDefault();
                e.target.checked = false;
                if (typeof showToast === 'function') {
                    showToast("Profesyonel mod şimdilik sadece geliştiricilere açıktır.", "warning");
                }
                return;
            }
            AppState.viewMode = e.target.checked ? "pro" : "beginner";
        };
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

        // Dynamic Cost Logic
        const saveRates = async () => {
            const rawComm = parseFloat(document.getElementById("settings-commission-rate").value) || 0;
            const rawSlip = parseFloat(document.getElementById("settings-slippage-rate").value) || 0;
            
            // 🛡️ Clamp between 0 and 50%
            AppState.commissionRate = Math.min(50, Math.max(0, rawComm));
            AppState.slippageRate = Math.min(50, Math.max(0, rawSlip));
            
            // Sync back to UI if clamped
            document.getElementById("settings-commission-rate").value = AppState.commissionRate;
            document.getElementById("settings-slippage-rate").value = AppState.slippageRate;
            
            localStorage.setItem("commissionRate", AppState.commissionRate);
            localStorage.setItem("slippageRate", AppState.slippageRate);
            
            // Sync with backend
            try {
                await httpClient.post('/api/user-settings', {
                    commission_rate: AppState.commissionRate / 100,
                    slippage_rate: AppState.slippageRate / 100,
                    risk_tolerance: AppState.riskTolerance || "Orta" // Keep existing
                });
                showToast("Maliyet ayarları kaydedildi", "success");
            } catch (e) {
                console.error("Settings sync failed:", e);
            }
        };

        document.getElementById("settings-commission-rate")?.addEventListener("change", saveRates);
        document.getElementById("settings-slippage-rate")?.addEventListener("change", saveRates);
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
        
        const data = await httpClient.get('/api/portfolio/history');
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
