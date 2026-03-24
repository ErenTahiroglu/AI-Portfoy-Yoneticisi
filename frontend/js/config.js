/**
 * ⚙️ Global Configuration (SRE Production Stack)
 * ============================================
 * Centralized API Base URL management to avoid hardcoded duplication.
 */

const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" 
    ? "http://localhost:8000" 
    : "https://ai-portfoy-yoneticisi.onrender.com";

// 🛡️ Expose to Global Scope
window.API_BASE = API_BASE;
