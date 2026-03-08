"""
🧩 Puzzle Parça: API Katmanı — v3.0
============================================
FastAPI endpoint tanımları, request/response modelleri ve middleware.
İş mantığı analysis_engine.py'de yaşar.

v3.0 Yenilikler:
  • Export endpoint'leri (Excel, PDF, DOCX)
  • Ticker suggestion / autocomplete endpoint'i

Kullanım:
    uvicorn main:app --host 127.0.0.1 --port 8000
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel
from typing import List, Optional
from io import BytesIO
import os

# ── Modül importları ──────────────────────────────────────────────────────
# ── Modül importları ──────────────────────────────────────────────────────
from src.utils.file_processor import extract_tickers_from_text, process_uploaded_file
from src.core.analysis_engine import AnalysisEngine, compute_portfolio_extras

# ── FastAPI uygulaması ────────────────────────────────────────────────────
app = FastAPI(title="Portföy Analiz Platformu", version="3.0")

# ── Analiz motoru (singleton) ─────────────────────────────────────────────
engine = AnalysisEngine()

# ── Statik dosya servisi (Frontend) ───────────────────────────────────────
base_dir = os.path.dirname(os.path.abspath(__file__))
frontend_path = os.path.join(base_dir, "frontend")

if os.path.exists(frontend_path):
    app.mount("/ui", StaticFiles(directory=frontend_path, html=True), name="ui")

# ── Cache-Control middleware (tarayıcı eski dosyaları kullanmasın) ─────────
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/ui"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheMiddleware)

# ── CORS middleware ───────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══════════════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELLERİ
# ══════════════════════════════════════════════════════════════════════════

class AnalysisRequest(BaseModel):
    tickers: List[str]
    use_ai: bool = False
    api_key: Optional[str] = None
    av_api_key: Optional[str] = None
    model: str = "gemini-2.5-flash"
    check_islamic: bool = False
    check_financials: bool = True
    lang: str = "tr"

class TextAnalysisRequest(BaseModel):
    text: str
    use_ai: bool = False
    api_key: Optional[str] = None
    av_api_key: Optional[str] = None
    model: str = "gemini-2.5-flash"
    check_islamic: bool = False
    check_financials: bool = True
    lang: str = "tr"

class ExportRequest(BaseModel):
    results: list
    format: str = "excel"  # excel | pdf | docx


# ══════════════════════════════════════════════════════════════════════════
# TICKER SUGGESTION DATA
# ══════════════════════════════════════════════════════════════════════════

_POPULAR_TICKERS = {
    # ABD Popüler
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp.", "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.", "TSLA": "Tesla Inc.", "META": "Meta Platforms",
    "NVDA": "NVIDIA Corp.", "JPM": "JPMorgan Chase", "V": "Visa Inc.",
    "JNJ": "Johnson & Johnson", "WMT": "Walmart Inc.", "PG": "Procter & Gamble",
    "MA": "Mastercard Inc.", "UNH": "UnitedHealth Group", "HD": "Home Depot",
    "DIS": "Walt Disney Co.", "BAC": "Bank of America", "KO": "Coca-Cola Co.",
    "PEP": "PepsiCo Inc.", "NFLX": "Netflix Inc.", "INTC": "Intel Corp.",
    "AMD": "Advanced Micro Devices", "CRM": "Salesforce Inc.", "AVGO": "Broadcom Inc.",
    "COST": "Costco Wholesale", "ABBV": "AbbVie Inc.", "MRK": "Merck & Co.",
    "TMO": "Thermo Fisher", "ACN": "Accenture plc", "LLY": "Eli Lilly & Co.",
    # BIST Popüler
    "THYAO": "Türk Hava Yolları", "ASELS": "Aselsan", "GARAN": "Garanti Bankası",
    "AKBNK": "Akbank", "YKBNK": "Yapı Kredi Bankası", "EREGL": "Ereğli Demir Çelik",
    "BIMAS": "BİM Mağazaları", "SAHOL": "Sabancı Holding", "KCHOL": "Koç Holding",
    "SISE": "Şişecam", "TUPRS": "Tüpraş", "FROTO": "Ford Otosan",
    "TOASO": "Tofaş", "TCELL": "Turkcell", "PGSUS": "Pegasus",
    "TAVHL": "TAV Havalimanları", "EKGYO": "Emlak Konut GYO", "KOZAL": "Koza Altın",
    "SASA": "SASA Polyester", "TTKOM": "Türk Telekom", "ARCLK": "Arçelik",
    "MGROS": "Migros", "PETKM": "PETKİM", "SOKM": "Şok Marketler",
    "VESTL": "Vestel Elektronik", "HALKB": "Halkbank", "VAKBN": "VakıfBank",
    "GUBRF": "Gübre Fabrikaları", "KOZAA": "Koza Anadolu Metal",
    # TEFAS Popüler
    "TP2": "TEB Portföy İkinci Fon Sepeti Fonu", "AKB": "Ak Portföy Birinci Değişken Fon",
    "ZP8": "Ziraat Portföy Birinci Katılım Fonu", "IPB": "İş Portföy Birinci Değişken Fon",
    "YAY": "Yapı Kredi Yabancı Teknoloji Hisse Senedi Fonu", "TI2": "TEB Portföy İş İştirakleri Fonu",
    "MAC": "Marmara Capital Hisse Senedi Fonu", "AFA": "Ak Portföy Amerika Yabancı Hisse Fonu",
}


# ══════════════════════════════════════════════════════════════════════════
# API ENDPOINT'LERİ
# ══════════════════════════════════════════════════════════════════════════

@app.get("/")
def read_root():
    return RedirectResponse(url="/ui")

def process_tickers_with_weights(raw_tickers: List[str]):
    parsed = []
    weights_map = {}
    for rt in raw_tickers:
        parts = rt.split(":")
        ticker = parts[0].strip().upper()
        if not ticker: continue
        weight = 1.0
        if len(parts) > 1:
            try:
                weight = float(parts[1])
            except ValueError:
                pass
        parsed.append(ticker)
        weights_map[ticker] = weight
    return parsed, weights_map

def attach_weights_and_compute_extras(engine_result: dict, weights_map: dict):
    results_list = engine_result.get("results", [])
    for r in results_list:
        r["weight"] = weights_map.get(r["ticker"], 1.0)
    engine_result["extras"] = compute_portfolio_extras(results_list)
    return engine_result

@app.post("/api/analyze")
async def analyze_portfolio(request: AnalysisRequest):
    """Ticker listesiyle portföy analizi."""
    if not request.tickers:
        raise HTTPException(status_code=400, detail="No tickers provided")
    if request.use_ai and not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required for AI analysis")
    
    parsed_tickers, weights_map = process_tickers_with_weights(request.tickers)
    if not parsed_tickers:
        raise HTTPException(status_code=400, detail="No valid tickers provided")
        
    result = engine.analyze(
        tickers=parsed_tickers,
        use_ai=request.use_ai,
        api_key=request.api_key,
        av_api_key=request.av_api_key,
        model=request.model,
        check_islamic=request.check_islamic,
        check_financials=request.check_financials,
    )
    return attach_weights_and_compute_extras(result, weights_map)

@app.post("/api/analyze/text")
async def analyze_from_text(request: TextAnalysisRequest):
    """Metin kutusundan ticker çıkarıp analiz eder."""
    tickers = extract_tickers_from_text(request.text)
    if not tickers:
        raise HTTPException(status_code=400, detail="No stock symbols found in the provided text")
    
    parsed_tickers, weights_map = process_tickers_with_weights(tickers)
    if not parsed_tickers:
        raise HTTPException(status_code=400, detail="No stock symbols found in the provided text")
    
    result = engine.analyze(
        tickers=parsed_tickers,
        use_ai=request.use_ai,
        api_key=request.api_key,
        av_api_key=request.av_api_key,
        model=request.model,
        check_islamic=request.check_islamic,
        check_financials=request.check_financials,
    )
    return attach_weights_and_compute_extras(result, weights_map)

@app.post("/api/analyze/file")
async def analyze_from_file(
    file: UploadFile = File(...),
    use_ai: bool = Form(False),
    api_key: Optional[str] = Form(None),
    av_api_key: Optional[str] = Form(None),
    model: str = Form("gemini-2.5-flash"),
    check_islamic: bool = Form(False),
    check_financials: bool = Form(True),
    lang: str = Form("tr")
):
    """Dosyadan ticker çıkarıp analiz eder."""
    try:
        contents = await file.read()
        
        class MockFile:
            def __init__(self, name, data):
                self.name = name
                self.data = data
            def read(self):
                return self.data
        
        buffer = BytesIO(contents)
        buffer.name = file.filename
        mock_file = MockFile(file.filename, contents)
        
        if file.filename.endswith(('.csv', '.xlsx', '.xls')):
            tickers = process_uploaded_file(buffer)
        else:
            tickers = process_uploaded_file(mock_file)
        
        parsed_tickers, weights_map = process_tickers_with_weights(tickers)
        if not parsed_tickers:
            raise HTTPException(status_code=400, detail="No stock symbols found in the uploaded file")
        
        result = engine.analyze(
            tickers=parsed_tickers,
            use_ai=use_ai,
            api_key=api_key,
            av_api_key=av_api_key,
            model=model,
            check_islamic=check_islamic,
            check_financials=check_financials,
            lang=lang,
        )
        return attach_weights_and_compute_extras(result, weights_map)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


# ══════════════════════════════════════════════════════════════════════════
# TICKER SUGGESTION ENDPOINT
# ══════════════════════════════════════════════════════════════════════════

@app.get("/api/suggest")
async def suggest_tickers(q: str = ""):
    """Ticker autocomplete önerileri döndürür."""
    if not q or len(q) < 1:
        return {"suggestions": []}
    
    q_upper = q.upper().strip()
    matches = []
    
    for ticker, name in _POPULAR_TICKERS.items():
        if q_upper in ticker or q.lower() in name.lower():
            matches.append({"ticker": ticker, "name": name})
            if len(matches) >= 10:
                break
    
    return {"suggestions": matches}


# ══════════════════════════════════════════════════════════════════════════
# AI WIZARD & NEWS ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════

class WizardRequest(BaseModel):
    prompt: str
    api_key: str
    model: str = "gemini-2.5-flash"
    lang: str = "tr"

class NewsRequest(BaseModel):
    tickers: List[str]
    api_key: Optional[str] = None
    model: str = "gemini-2.5-flash"
    lang: str = "tr"

@app.post("/api/wizard")
async def wizard_api(request: WizardRequest):
    """Metinsel komuttan portföy üretir."""
    if not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required for AI Wizard")
    try:
        from src.core.ai_agent import generate_wizard_portfolio
        portfolio = generate_wizard_portfolio(request.prompt, request.api_key, request.model, request.lang)
        return {"portfolio": portfolio}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/news")
async def news_api(request: NewsRequest):
    """Ticker listesi için önemli haberleri çeker ve AI ile filtreler."""
    if not request.tickers: return {"news": []}
    try:
        from src.data.news_fetcher import fetch_and_filter_news
        data = fetch_and_filter_news(request.tickers, request.api_key, request.model, request.lang)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ══════════════════════════════════════════════════════════════════════════
# EXPORT ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════

@app.post("/api/export/excel")
async def export_excel(request: ExportRequest):
    """Analiz sonuçlarını Excel dosyası olarak döndürür."""
    import pandas as pd
    from src.utils.file_processor import to_excel
    
    rows = _results_to_rows(request.results)
    df = pd.DataFrame(rows)
    excel_bytes = to_excel(df)
    
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=portfolio_analysis.xlsx"}
    )

@app.post("/api/export/pdf")
async def export_pdf(request: ExportRequest):
    """Analiz sonuçlarını PDF dosyası olarak döndürür."""
    from src.utils.file_processor import create_pdf
    
    report_text = _results_to_report_text(request.results)
    pdf_bytes = create_pdf(report_text)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=portfolio_analysis.pdf"}
    )

@app.post("/api/export/docx")
async def export_docx(request: ExportRequest):
    """Analiz sonuçlarını DOCX dosyası olarak döndürür."""
    from src.utils.file_processor import create_docx
    
    report_text = _results_to_report_text(request.results)
    docx_bytes = create_docx(report_text)
    
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=portfolio_analysis.docx"}
    )


def _results_to_rows(results: list) -> list:
    """Analiz sonuçlarını tablo satırlarına çevirir."""
    rows = []
    for res in results:
        row = {
            "Hisse/Fon": res.get("ticker", ""),
            "Pazar": res.get("market", ""),
        }
        if res.get("status"):
            row["Durum"] = res["status"]
            row["Arındırma Oranı (%)"] = res.get("purification_ratio", "-")
            row["Borçluluk Oranı (%)"] = res.get("debt_ratio", "-")
        
        fin = res.get("financials", {})
        if fin:
            row["5Y Reel Getiri (%)"] = fin.get("s5", "-")
            row["3Y Reel Getiri (%)"] = fin.get("s3", "-")
        
        val = res.get("valuation", {})
        if val:
            row["P/E"] = val.get("pe", "-")
            row["P/B"] = val.get("pb", "-")
            row["Beta"] = val.get("beta", "-")
        
        rows.append(row)
    return rows


def _results_to_report_text(results: list) -> str:
    """Analiz sonuçlarını rapor metnine çevirir."""
    lines = ["# Portföy Analiz Raporu\n"]
    
    for res in results:
        ticker = res.get("ticker", "?")
        lines.append(f"\n## {ticker}")
        lines.append(f"- Pazar: {res.get('market', '?')}")
        
        if res.get("status"):
            lines.append(f"- Durum: {res['status']}")
            if res.get("purification_ratio") is not None:
                lines.append(f"- Arındırma Oranı: %{res['purification_ratio']}")
            if res.get("debt_ratio") is not None:
                lines.append(f"- Borçluluk Oranı: %{res['debt_ratio']}")
        
        fin = res.get("financials", {})
        if fin:
            if fin.get("s5") is not None:
                lines.append(f"- 5Y Reel Getiri: %{fin['s5']:.2f}")
            if fin.get("s3") is not None:
                lines.append(f"- 3Y Reel Getiri: %{fin['s3']:.2f}")
        
        val = res.get("valuation", {})
        if val:
            lines.append(f"- P/E: {val.get('pe', '-')}")
            lines.append(f"- P/B: {val.get('pb', '-')}")
            lines.append(f"- Beta: {val.get('beta', '-')}")
        
        if res.get("ai_comment"):
            lines.append(f"\n### AI Yorumu\n{res['ai_comment']}")
    
    return "\n".join(lines)
