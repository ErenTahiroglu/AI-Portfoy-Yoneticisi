"""Tests for file_processor.py — Dosya işleme modülü."""

import pytest
from utils.file_processor import extract_tickers_from_text, create_pdf, create_docx


class TestExtractTickers:
    """Ticker çıkarma testleri."""

    def test_basic_comma_separated(self):
        tickers = extract_tickers_from_text("AAPL, MSFT, TSLA")
        assert "AAPL" in tickers
        assert "MSFT" in tickers
        assert "TSLA" in tickers

    def test_mixed_separators(self):
        tickers = extract_tickers_from_text("AAPL MSFT;TSLA,THYAO")
        assert len(tickers) >= 4

    def test_bist_tickers(self):
        tickers = extract_tickers_from_text("THYAO AKBNK GARAN")
        assert "THYAO" in tickers

    def test_with_dot_suffix(self):
        tickers = extract_tickers_from_text("THYAO.IS AKBNK.IS")
        assert any("IS" in t for t in tickers)

    def test_empty_input(self):
        assert extract_tickers_from_text("") == []

    def test_numbers_only_excluded(self):
        tickers = extract_tickers_from_text("12345 67890")
        assert len(tickers) == 0


class TestCreatePDF:
    """PDF oluşturma testleri."""

    def test_creates_bytes(self):
        result = create_pdf("# Test Raporu\n- Madde 1\n- Madde 2")
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:4] == b"%PDF"

    def test_handles_turkish_chars(self):
        result = create_pdf("Türkçe karakterler: ğüşöçı İĞÜŞÖÇ")
        assert isinstance(result, bytes)


class TestCreateDOCX:
    """DOCX oluşturma testleri."""

    def test_creates_bytes(self):
        result = create_docx("# Test Raporu\n## Alt Başlık\n- Madde")
        assert isinstance(result, bytes)
        assert len(result) > 0
        # DOCX is a ZIP file (PK header)
        assert result[:2] == b"PK"
