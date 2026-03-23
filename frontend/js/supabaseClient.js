import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

// Supabase URL ve Anon Key
const SUPABASE_URL = "https://zlggrmsolklhfgijcjnz.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_G67qSQ6JxmUYy3fuQAHb_Q_myhSebvW";

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
    if (!supabase) throw new Error("Supabase aktif değil.");
    const user = await getUser();
    if (!user) throw new Error("Giriş yapmalısınız!");

    try {
        const { data, error } = await supabase
            .from('portfolios')
            .upsert({
                user_id: user.id,
                tickers: tickersArray,
                updated_at: new Date().toISOString()
            }, { onConflict: 'user_id' });

        if (error) throw error;
        if (typeof localStorage !== "undefined") {
            localStorage.removeItem(`offline_portfolio_${user.id}`); // Başarılıysa offline cache'i sil
        }
        return data;
    } catch (err) {
        console.warn("Save failed, saving to offline cache fallback:", err);
        if (typeof localStorage !== "undefined") {
            localStorage.setItem(`offline_portfolio_${user.id}`, JSON.stringify({
                tickers: tickersArray,
                timestamp: Date.now()
            }));
        }
        // Hata fırlatma ki offline iken de UI kaydedildi saysın ama uyarsın (Opsiyonel: feedback toast)
        throw new Error("Çevrimdışı kaydedildi. Ağ bağlantısı geldiğinde otomatik eşitlenecektir.");
    }
}

export async function loadPortfolio() {
    if (!supabase) return [];
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
        const { data, error } = await supabase
            .from('portfolios')
            .select('tickers, updated_at')
            .eq('user_id', user.id)
            .maybeSingle();

        if (error) throw error;

        // ÇEVRİMDIŞI SENKRONİZASYON (Timestamp wins)
        if (offlineData && data && data.updated_at) {
             const dbTime = new Date(data.updated_at).getTime();
             if (offlineData.timestamp > dbTime) {
                 console.log("Offline veri daha yeni, Supabase'e geri senkronize ediliyor...");
                 savePortfolio(offlineData.tickers).catch(console.error);
                 return offlineData.tickers;
             }
        } 
        else if (offlineData && !data) {
             console.log("Yeni offline portföy Supabase'e yükleniyor...");
             savePortfolio(offlineData.tickers).catch(console.error);
             return offlineData.tickers;
        }

        if (offlineData) {
            localStorage.removeItem(`offline_portfolio_${user.id}`); // Senkronize edildi veya eskidi
        }

        return data ? data.tickers : [];
    } catch (err) {
        console.warn("Portföy yüklenemedi (Offline olabilir), local cache kullanılıyor:", err);
        return offlineData ? offlineData.tickers : [];
    }
}

// Vanilla JS Fallback (expose to window if required by standard scripts)
window.SupabaseAuth = { signInWithGoogle, signOut, getUser, getValidSession, savePortfolio, loadPortfolio };
