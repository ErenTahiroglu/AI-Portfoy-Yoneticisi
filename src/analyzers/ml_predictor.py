"""
🤖 ML Fiyat Tahmin Modülü — P5 Öncelik Matrisi
================================================
Prophet (Meta) tabanlı zaman serisi tahmin stratejisi.
Tek başına çalışan GET /api/predict/{ticker} endpoint'i için.

• Varsayılan KAPALI — ML_PREDICTION_ENABLED=true env var ile açılır.
• Prophet ~200MB — ana analiz akışından izole tutuldu.
• 60 günlük tarihsel fiyat → Prophet fit → 7 günlük forecast.

Önemli: Bu strateji ana analysis_engine registry'sine eklenmez.
Bağımsız /api/predict endpoint'i tarafından çağrılır.
"""
import logging
import os

logger = logging.getLogger(__name__)

ML_ENABLED: bool = os.getenv("ML_PREDICTION_ENABLED", "false").lower() == "true"


def predict_price(ticker: str) -> dict:
    """
    Ticker için 7 günlük ML fiyat tahmini üretir.

    Returns:
        {
            "ticker": "AAPL",
            "direction": "UP" | "DOWN" | "SIDEWAYS",
            "confidence": 0.73,
            "current_price": 182.5,
            "target_7d": 191.2,
            "change_pct": 4.77,
            "plot_data": [{"ds": "2026-03-25", "yhat": 191.2, "yhat_lower": 185.0, "yhat_upper": 197.4}],
            "model": "Prophet",
            "error": null
        }
    """
    if not ML_ENABLED:
        return {
            "ticker": ticker,
            "error": "ML tahmini devre dışı. ML_PREDICTION_ENABLED=true ile aktifleştirin.",
            "enabled": False
        }

    try:
        # Lazy import — yalnızca ML etkinleştirildiğinde yüklenir
        import pandas as pd
        from prophet import Prophet  # type: ignore[import]
        import yfinance as yf         # type: ignore[import]

        logger.info(f"📊 ML tahmin başlatılıyor: {ticker}")

        # ── 1. Tarihsel Veri ──────────────────────────────────────────────
        stock = yf.Ticker(ticker)
        hist = stock.history(period="90d", interval="1d")

        if hist.empty or len(hist) < 20:
            return {"ticker": ticker, "error": "Yetersiz tarihsel veri (min 20 gün)."}

        # Prophet formatına çevir: ds, y
        df = pd.DataFrame({
            "ds": hist.index.tz_localize(None),
            "y": hist["Close"].values,
        })

        current_price = float(df["y"].iloc[-1])

        # ── 2. Prophet Model ──────────────────────────────────────────────
        model = Prophet(
            changepoint_prior_scale=0.15,
            seasonality_mode="multiplicative",
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
        )
        model.fit(df)

        # 7 günlük gelecek tahmin
        future = model.make_future_dataframe(periods=7, freq="D")
        forecast = model.predict(future)

        # Sadece gelecek 7 günü al
        future_fc = forecast[forecast["ds"] > df["ds"].max()].head(7)

        target_price = float(future_fc["yhat"].iloc[-1])
        lower_bound = float(future_fc["yhat_lower"].iloc[-1])
        upper_bound = float(future_fc["yhat_upper"].iloc[-1])
        change_pct = ((target_price - current_price) / current_price) * 100

        # ── 3. Güven Skoru ────────────────────────────────────────────────
        # Tahmin aralığının genişliğine göre güven hesapla
        interval_width = (upper_bound - lower_bound) / current_price
        confidence = max(0.3, min(0.95, 1.0 - interval_width * 2))

        # ── 4. Yön Belirleme ─────────────────────────────────────────────
        if change_pct > 1.5:
            direction = "UP"
        elif change_pct < -1.5:
            direction = "DOWN"
        else:
            direction = "SIDEWAYS"

        # ── 5. Çıktı ─────────────────────────────────────────────────────
        plot_data = [
            {
                "ds": str(row["ds"].date()),
                "yhat": round(float(row["yhat"]), 2),
                "yhat_lower": round(float(row["yhat_lower"]), 2),
                "yhat_upper": round(float(row["yhat_upper"]), 2),
            }
            for _, row in future_fc.iterrows()
        ]

        return {
            "ticker": ticker,
            "direction": direction,
            "confidence": round(confidence, 3),
            "current_price": round(current_price, 2),
            "target_7d": round(target_price, 2),
            "lower_7d": round(lower_bound, 2),
            "upper_7d": round(upper_bound, 2),
            "change_pct": round(change_pct, 2),
            "plot_data": plot_data,
            "model": "Prophet",
            "error": None,
            "enabled": True,
        }

    except ImportError as e:
        return {
            "ticker": ticker,
            "error": f"Gerekli paket eksik: {e}. pip install prophet yfinance",
            "enabled": True,
        }
    except Exception as e:
        logger.error(f"ML tahmin hatası ({ticker}): {e}")
        return {"ticker": ticker, "error": str(e), "enabled": True}
