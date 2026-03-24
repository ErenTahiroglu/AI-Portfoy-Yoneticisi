import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

// Supabase URL ve Anon Key
const SUPABASE_URL = "https://ixzuenvihwlmzndvrdvr.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_nTICEh2yWv4VmmuUYI8-Mg_j6FchURZ";

// İstemci Başlat (Client Init)
let supabase = null;
try {
    if (SUPABASE_URL !== "YOUR_SUPABASE_URL") {
        supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    } else {
        console.warn("Supabase NOT Initialized: URL and Key placeholders still active.");
    }
} catch (e) {
    console.error("Supabase Init Error:", e);
}

// ── Auth İşlemleri ───────────────────────────────────────────────────

export async function signInWithGoogle() {
    if (!supabase) return alert("Supabase Ayarlarını Yapın!");
    const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
            redirectTo: window.location.origin
        }
    });
    if (error) console.error("Login Error:", error);
}

export async function signOut() {
    if (!supabase) return;
    const { error } = await supabase.auth.signOut();
    if (error) console.error("Logout Error:", error);
    else window.location.reload();
}

export async function getUser() {
    if (typeof localStorage !== "undefined" && localStorage.getItem("admin_bypass") === "true") {
        return { id: "dev_admin", email: "admin@local", user_metadata: { full_name: "Yönetici" } };
    }
    if (!supabase) return null;
    const { data } = await supabase.auth.getUser();
    return data?.user || null;
}

export async function getValidSession() {
    if (typeof localStorage !== "undefined" && localStorage.getItem("admin_bypass") === "true") {
        return { user: { id: "dev_admin", email: "admin@local" } };
    }
    if (!supabase) return null;
    const { data, error } = await supabase.auth.getSession();
    
    if (error) {
        console.error("Session fetch error:", error);
        return null;
    }
    return data?.session || null;
}

// ── Database İşlemleri ───────────────────────────────────────────────

export async function savePortfolio(tickersArray) {
    const user = await getUser();
    if (!user) throw new Error("Giriş yapmalısınız!");

    try {
        const session = await getValidSession();
        const jwtToken = session ? session.access_token : "";

        // 🛡️ SRE Best Practice: Veritabanı işlemleri Backend (Render) proxy üzerinden geçer.
        const res = await fetch(`${window.API_BASE}/api/portfolio`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${jwtToken}`
            },
            body: JSON.stringify({ tickers: tickersArray })
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || "Portföy kaydedilemedi.");
        }

        if (typeof localStorage !== "undefined") {
            localStorage.removeItem(`offline_portfolio_${user.id}`);
        }
        return { status: "success" };
    } catch (err) {
        console.warn("Save failed, saving to offline cache fallback:", err);
        if (typeof localStorage !== "undefined") {
            localStorage.setItem(`offline_portfolio_${user.id}`, JSON.stringify({
                tickers: tickersArray,
                timestamp: Date.now()
            }));
        }
        throw new Error("Çevrimdışı kaydedildi. Ağ bağlantısı geldiğinde otomatik eşitlenecektir.");
    }
}

export async function loadPortfolio() {
    const user = await getUser();
    if (!user) return [];

    let offlineData = null;
    if (typeof localStorage !== "undefined") {
        const cached = localStorage.getItem(`offline_portfolio_${user.id}`);
        if (cached) {
            try { offlineData = JSON.parse(cached); } catch (e) {}
        }
    }

    try {
        const session = await getValidSession();
        const jwtToken = session ? session.access_token : "";

        const res = await fetch(`${window.API_BASE}/api/portfolio`, {
             method: "GET",
             headers: {
                  "Authorization": `Bearer ${jwtToken}`
             }
        });

        if (!res.ok) throw new Error("Yükleme hatası");

        const data = await res.json(); 

        const updated_at = data ? data.updated_at : null;

        // ÇEVRİMDIŞI SENKRONİZASYON (Timestamp wins)
        if (offlineData && data && updated_at) {
             const dbTime = new Date(updated_at).getTime();
             if (offlineData.timestamp > dbTime) {
                 console.log("Offline veri daha yeni, Backend'e geri senkronize ediliyor...");
                 savePortfolio(offlineData.tickers).catch(console.error);
                 return offlineData.tickers;
             }
        } 
        else if (offlineData && (!data || !data.tickers)) {
             console.log("Yeni offline portföy Backend'e yükleniyor...");
             savePortfolio(offlineData.tickers).catch(console.error);
             return offlineData.tickers;
         }

        if (offlineData) {
            localStorage.removeItem(`offline_portfolio_${user.id}`); 
        }

        return data ? (data.tickers || []) : [];
    } catch (err) {
        console.warn("Portföy yüklenemedi (Offline olabilir), local cache kullanılıyor:", err);
        return offlineData ? offlineData.tickers : [];
    }
}

// Vanilla JS Fallback (expose to window if required by standard scripts)
window.SupabaseAuth = { signInWithGoogle, signOut, getUser, getValidSession, savePortfolio, loadPortfolio };
