import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

// Supabase URL ve Anon Key
const SUPABASE_URL = "YOUR_SUPABASE_URL";
const SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY";

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
    if (!supabase) return null;
    const { data } = await supabase.auth.getUser();
    return data?.user || null;
}

// ── Database İşlemleri ───────────────────────────────────────────────

export async function savePortfolio(tickersArray) {
    if (!supabase) throw new Error("Supabase aktif değil.");
    const user = await getUser();
    if (!user) throw new Error("Giriş yapmalısınız!");

    // user_id unique olduğu için upsert yapabiliriz
    const { data, error } = await supabase
        .from('portfolios')
        .upsert({
            user_id: user.id,
            tickers: tickersArray,
            updated_at: new Date().toISOString()
        }, { onConflict: 'user_id' });

    if (error) {
        console.error("Save Error:", error);
        throw error;
    }
    return data;
}

export async function loadPortfolio() {
    if (!supabase) return [];
    const user = await getUser();
    if (!user) return [];

    const { data, error } = await supabase
        .from('portfolios')
        .select('tickers')
        .eq('user_id', user.id)
        .maybeSingle();

    if (error) {
        console.error("Load Error:", error);
        throw error;
    }
    return data ? data.tickers : [];
}

// Vanilla JS Fallback (expose to window if required by standard scripts)
window.SupabaseAuth = { signInWithGoogle, signOut, getUser, savePortfolio, loadPortfolio };
