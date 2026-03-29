-- Supabase / Alembic T0-T7 Divergence Tablosu & pg_cron Schema

CREATE TABLE IF NOT EXISTS shadow_divergence_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker VARCHAR(20) NOT NULL,
    old_decision VARCHAR(50) NOT NULL, -- BUY, SELL, HOLD
    new_decision VARCHAR(50) NOT NULL, -- BUY, SELL, HOLD
    
    old_rationale TEXT,
    new_rationale TEXT,
    
    -- Fiyatlama & Paper Trading (T0..T7)
    t0_price DECIMAL(10,2) NOT NULL,
    t1_price DECIMAL(10,2),
    t3_price DECIMAL(10,2),
    t7_price DECIMAL(10,2),
    
    -- Ayrışma sonrasında sistemde yaşanan başarı durumları
    -- Kararı alınan senaryo kimin lehine sonuçlandı? (Old/New/Tie)
    winner_t1 VARCHAR(10), 
    winner_t3 VARCHAR(10),
    winner_t7 VARCHAR(10),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- pg_cron eklentisi kullanılarak standalone python PnL_Tracker.py dosyasını tetiklemek
-- için Edge Function/Webhook veya REST API cron'u Supabase Dashboard'dan ayarlanır.
