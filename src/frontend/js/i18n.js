/**
 * i18n — Çoklu Dil Desteği (TR / EN)
 */
const TRANSLATIONS = {
    tr: {
        // Header
        "header.badge": "AI Destekli Analiz",
        "header.title": "Portföy Analiz Platformu",
        "header.subtitle": "Hisselerinizi ve fonlarınızı yapay zeka ile saniyeler içinde derinlemesine analiz edin.",
        // Sidebar
        "sidebar.settings": "ANALİZ AYARLARI",
        "sidebar.compliance": "Uygunluk Taraması",
        "sidebar.compliance.desc": "İslami uygunluk analizi",
        "sidebar.financial": "Finansal Analiz",
        "sidebar.financial.desc": "Getiri & performans",
        "sidebar.ai": "AI Yorumları",
        "sidebar.ai.desc": "Gemini ile akıllı analiz",
        "sidebar.apiKey": "Gemini API Anahtarı",
        "sidebar.avKey": "Alpha Vantage API",
        "sidebar.model": "Model Seçimi",
        "sidebar.aiNote": "⚠ Pro modeller için faturalandırma açık olmalıdır.",
        "sidebar.watchlist": "KAYITLI PORTFÖYLER",
        "sidebar.savePortfolio": "Portföy Kaydet",
        "sidebar.noWatchlist": "Henüz kayıtlı portföy yok",
        "sidebar.quickStart": "Hızlı Başlangıç",
        "sidebar.quickStartDesc": "ABD (NYSE/NASDAQ) ve Türkiye (BIST/TEFAS) hisselerini & fonlarını aynı anda analiz edebilirsiniz.",
        // Input
        "input.tickers": "Hisse Sembolleri",
        "input.tickerPlaceholder": "Örnek: AAPL, MSFT, TSLA veya THYAO, AKB, KCHOL...",
        "input.tickerHelper": "Virgülle veya boşlukla ayırarak girebilirsiniz.",
        "input.tickerHelperBold": "ABD ve Türkiye (BIST/TEFAS) hisse/fonları aynı anda analiz edilebilir.",
        "input.file": "Dosya Yükle",
        "input.fileFormats": "Desteklenen formatlar: .txt, .csv, .xlsx, .docx",
        "input.fileDrop": "Sürükle bırak veya",
        "input.fileBrowse": "göz at",
        "input.or": "VEYA",
        // Buttons
        "btn.analyze": "Portföyü Analiz Et",
        "btn.compare": "Karşılaştır",
        // Results
        "results.title": "Analiz Sonuçları",
        "results.summary": "Portföy Özeti",
        "results.weightedReturn": "Ağırlıklı Getiri (5Y)",
        "results.comparison": "Karşılaştırma",
        "results.sectors": "Sektör Dağılımı",
        "results.correlation": "Korelasyon Matrisi",
        // Table headers
        "th.ticker": "Hisse / Fon",
        "th.market": "Pazar",
        "th.weight": "Ağırlık",
        "th.price": "Son Fiyat",
        "th.compliance": "Uyg. Tarama Oranı",
        "th.status": "Durum",
        // Cards
        "card.returns": "Dönemsel Getiriler",
        "card.chart": "Yıllık Getiri Grafiği",
        "card.ai": "AI Yorumu",
        "card.technicals": "Teknik Göstergeler",
        // Loader
        "loader.text": "Analiz ediliyor...",
        "progress.preparing": "Hazırlanıyor...",
        // Toasts
        "toast.analysisComplete": "hisse başarıyla analiz edildi",
        "toast.noAnalysis": "Lütfen en az bir analiz türü seçin.",
        "toast.noApiKey": "AI yorumları için Gemini API anahtarı gereklidir.",
        "toast.noTickers": "Lütfen hisse sembollerini girin veya dosya yükleyin.",
        "toast.exported": "Dosya indirildi!",
        "toast.exporting": "dosyası oluşturuluyor...",
        "toast.compareMin": "Karşılaştırma için en az 2 hisse gerekli",
        "toast.saved": "kaydedildi",
        "toast.loaded": "yüklendi",
        "toast.deleted": "silindi",
        "toast.enterTickers": "Önce hisse sembolleri girin",
        "toast.portfolioName": "Portföy adı:",
        // Monte Carlo
        "monte.title": "Monte Carlo Simülasyonu (1 Yıl)",
        // Theme
        "theme.toggle": "Tema",
        // Language
        "lang.toggle": "Language",
    },
    en: {
        "header.badge": "AI-Powered Analysis",
        "header.title": "Portfolio Analysis Platform",
        "header.subtitle": "Analyze your stocks and funds in-depth with artificial intelligence in seconds.",
        "sidebar.settings": "ANALYSIS SETTINGS",
        "sidebar.compliance": "Compliance Scan",
        "sidebar.compliance.desc": "Islamic compliance analysis",
        "sidebar.financial": "Financial Analysis",
        "sidebar.financial.desc": "Returns & performance",
        "sidebar.ai": "AI Commentary",
        "sidebar.ai.desc": "Smart analysis with Gemini",
        "sidebar.apiKey": "Gemini API Key",
        "sidebar.avKey": "Alpha Vantage API",
        "sidebar.model": "Model Selection",
        "sidebar.aiNote": "⚠ Billing must be enabled for Pro models.",
        "sidebar.watchlist": "SAVED PORTFOLIOS",
        "sidebar.savePortfolio": "Save Portfolio",
        "sidebar.noWatchlist": "No saved portfolios",
        "sidebar.quickStart": "Quick Start",
        "sidebar.quickStartDesc": "You can analyze US (NYSE/NASDAQ) and Turkey (BIST/TEFAS) stocks & funds simultaneously.",
        "input.tickers": "Ticker Symbols",
        "input.tickerPlaceholder": "Example: AAPL, MSFT, TSLA or THYAO, AKB, KCHOL...",
        "input.tickerHelper": "Separate with commas or spaces.",
        "input.tickerHelperBold": "US and Turkey (BIST/TEFAS) tickers can be analyzed together.",
        "input.file": "Upload File",
        "input.fileFormats": "Supported formats: .txt, .csv, .xlsx, .docx",
        "input.fileDrop": "Drag & drop or",
        "input.fileBrowse": "browse",
        "input.or": "OR",
        "btn.analyze": "Analyze Portfolio",
        "btn.compare": "Compare",
        "results.title": "Analysis Results",
        "results.summary": "Portfolio Summary",
        "results.weightedReturn": "Weighted Return (5Y)",
        "results.comparison": "Comparison",
        "results.sectors": "Sector Distribution",
        "results.correlation": "Correlation Matrix",
        "th.ticker": "Ticker / Fund",
        "th.market": "Market",
        "th.weight": "Weight",
        "th.price": "Last Price",
        "th.compliance": "Compliance Ratio",
        "th.status": "Status",
        "card.returns": "Periodic Returns",
        "card.chart": "Yearly Return Chart",
        "card.ai": "AI Commentary",
        "card.technicals": "Technical Indicators",
        "loader.text": "Analyzing...",
        "progress.preparing": "Preparing...",
        "toast.analysisComplete": "stocks successfully analyzed",
        "toast.noAnalysis": "Please select at least one analysis type.",
        "toast.noApiKey": "Gemini API key is required for AI commentary.",
        "toast.noTickers": "Please enter ticker symbols or upload a file.",
        "toast.exported": "File downloaded!",
        "toast.exporting": "file is being created...",
        "toast.compareMin": "At least 2 stocks required for comparison",
        "toast.saved": "saved",
        "toast.loaded": "loaded",
        "toast.deleted": "deleted",
        "toast.enterTickers": "Enter ticker symbols first",
        "toast.portfolioName": "Portfolio name:",
        "monte.title": "Monte Carlo Simulation (1 Year)",
        "theme.toggle": "Theme",
        "lang.toggle": "Dil",
    },
};

let currentLang = localStorage.getItem("lang") || "tr";

function t(key) {
    return TRANSLATIONS[currentLang]?.[key] || TRANSLATIONS.tr[key] || key;
}

function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem("lang", lang);
    document.querySelectorAll("[data-i18n]").forEach((el) => {
        const key = el.getAttribute("data-i18n");
        if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
            el.placeholder = t(key);
        } else {
            el.textContent = t(key);
        }
    });
    // Update the language button text
    const langBtn = document.getElementById("lang-toggle-btn");
    if (langBtn) langBtn.textContent = t("lang.toggle");
}

function toggleLanguage() {
    setLanguage(currentLang === "tr" ? "en" : "tr");
}
