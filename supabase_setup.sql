-- 🛡️ AI Portföy Yöneticisi: Eksik Tablo Kurulum Betiği
-- Bu betiği Supabase -> SQL Editor kısmına yapıştırıp çalıştırın.

-- 1. User Settings Tablosu (Onboarding ve Bildirim Ayarları)
CREATE TABLE IF NOT EXISTS public.user_settings (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    onboarding_profile JSONB DEFAULT '{}'::jsonb,
    is_onboarded BOOLEAN DEFAULT false,
    telegram_chat_id TEXT,
    risk_tolerance TEXT DEFAULT 'Orta',
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Paper Trades Tablosu (Sanal İşlem Kayıtları)
CREATE TABLE IF NOT EXISTS public.paper_trades (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    type TEXT, -- BUY, SELL, REBALANCE
    target_weight DOUBLE PRECISION,
    timestamp TIMESTAMPTZ DEFAULT now()
);

-- 3. Portfolio Snapshots Tablosu (Geçmiş Performans Grafiği Verileri)
CREATE TABLE IF NOT EXISTS public.portfolio_snapshots (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ DEFAULT now(),
    assets JSONB DEFAULT '[]'::jsonb,
    total_value DOUBLE PRECISION DEFAULT 0
);

-- 🔐 RLS (Row Level Security) Politikaları
-- Kullanıcıların sadece kendi verilerini görmesini sağlar.

ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.paper_trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolio_snapshots ENABLE ROW LEVEL SECURITY;

-- User Settings Politikaları
CREATE POLICY "Users can view own settings" ON public.user_settings FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own settings" ON public.user_settings FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own settings" ON public.user_settings FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Paper Trades Politikaları
CREATE POLICY "Users can view own trades" ON public.paper_trades FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own trades" ON public.paper_trades FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Portfolio Snapshots Politikaları
CREATE POLICY "Users can view own snapshots" ON public.portfolio_snapshots FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own snapshots" ON public.portfolio_snapshots FOR INSERT WITH CHECK (auth.uid() = user_id);

-- 🚀 Başarılı! Tablolar oluşturuldu.
