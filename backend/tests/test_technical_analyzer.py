import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from backend.analyzers.technical_analyzer import run_technical_indicators


def generate_synthetic_ohlc(ticker="AAPL", days=100) -> pd.DataFrame:
    """Belirtilen gün sayısında sentetik MultiIndex OHLC DataFrame üretir."""
    dates = pd.date_range(end=pd.Timestamp.today(), periods=days)
    
    np.random.seed(42)
    closes = np.linspace(100, 150, days) + np.random.normal(0, 2, days)
    
    df = pd.DataFrame({
        'open': closes - 1,
        'high': closes + 2,
        'low': closes - 2,
        'close': closes,
        'volume': np.random.randint(1000, 5000, days)
    }, index=dates)
    
    # yahooquery Ticker.history() returns a MultiIndex (symbol, date)
    df['symbol'] = ticker
    df.set_index(['symbol', df.index], inplace=True)
    return df


@patch('yahooquery.Ticker')
def test_run_technical_indicators_success(mock_ticker_class):
    """
    Başarılı Senaryo: 100 günlük sentetik OHLC verisi sağlandığında RSI, MACD, 
    EMA metriklerinin ve gauge_score'un doğru hesaplanıp result_entry sözlüğüne 
    yazıldığını doğrula.
    """
    mock_t = MagicMock()
    mock_ticker_class.return_value = mock_t
    
    fetcher_ticker = "AAPL"
    
    # run_technical_indicators içinde hisse senedi ve benchmark için iki ayrı Ticker instance
    # aynı mock_t objesini döndürecek. side_effect kullanarak history çağrılarına sırasıyla
    # hisse ve benchmark verilerini döndürüyoruz.
    hist_hisse = generate_synthetic_ohlc(fetcher_ticker, 100)
    hist_bm = generate_synthetic_ohlc("SPY", 100)
    
    mock_t.history.side_effect = [hist_hisse, hist_bm]
    
    result_entry = {}
    run_technical_indicators(fetcher_ticker, result_entry)
    
    assert "technicals" in result_entry, "technicals sözlüğü result_entry içine eklenmeli"
    
    techs = result_entry["technicals"]
    assert "rsi_14" in techs, "RSI değeri hesaplanmalı"
    assert "macd" in techs, "MACD değeri hesaplanmalı"
    assert "ema_20" in techs, "EMA 20 değeri hesaplanmalı"
    assert "gauge_score" in techs, "Gauge Score değeri hesaplanmalı"
    
    assert isinstance(techs["rsi_14"], float), "RSI değeri float olmalı"
    assert isinstance(techs["gauge_score"], int), "Gauge Score değeri int olmalı"


@patch('yahooquery.Ticker')
def test_run_technical_indicators_empty_df_raises_exception(mock_ticker_class):
    """
    Başarısız Senaryo 1: API boş bir DataFrame döndürdüğünde fonksiyonun 
    sessizce çıkmak yerine açıkça bir Exception fırlattığını test et.
    """
    mock_t = MagicMock()
    mock_ticker_class.return_value = mock_t
    
    # Boş DataFrame
    mock_t.history.return_value = pd.DataFrame()
    
    result_entry = {}
    
    with pytest.raises(Exception):
        run_technical_indicators("AAPL", result_entry)


@patch('yahooquery.Ticker')
def test_run_technical_indicators_less_than_30_days_raises_exception(mock_ticker_class):
    """
    Başarısız Senaryo 2: 30 günden az veri geldiğinde fonksiyonun Exception fırlattığını test et.
    """
    mock_t = MagicMock()
    mock_ticker_class.return_value = mock_t
    
    # 29 günlük veri
    hist_hisse = generate_synthetic_ohlc("AAPL", 29)
    mock_t.history.return_value = hist_hisse
    
    result_entry = {}
    
    with pytest.raises(Exception):
        run_technical_indicators("AAPL", result_entry)


@patch('yahooquery.Ticker')
def test_run_technical_indicators_missing_close_column_raises_key_error(mock_ticker_class):
    """
    Başarısız Senaryo 3: Veri setinde 'Close' fiyat kolonu eksik olduğunda 
    KeyError/ValueError fırlattığını test et.
    """
    mock_t = MagicMock()
    mock_ticker_class.return_value = mock_t
    
    hist_hisse = generate_synthetic_ohlc("AAPL", 100)
    # create OHLC data without close price to raise an error
    hist_hisse = hist_hisse.drop(columns=['close'])
    
    mock_t.history.return_value = hist_hisse
    
    result_entry = {}
    
    with pytest.raises((KeyError, ValueError)):
        run_technical_indicators("AAPL", result_entry)
