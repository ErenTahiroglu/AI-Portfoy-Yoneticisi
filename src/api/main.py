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

import logging

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
frontend_path = os.path.join(os.path.dirname(base_dir), "frontend")

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

logger = logging.getLogger(__name__)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Portföy Analiz API aktif"}

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
    initial_balance: float = 10000.0
    monthly_contribution: float = 0.0
    rebalancing_freq: str = "none"

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

from src.data.constants import POPULAR_TICKERS


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

def attach_weights_and_compute_extras(engine_result: dict, weights_map: dict, initial_balance: float = 10000.0, monthly_contribution: float = 0.0, rebalancing_freq: str = "none"):
    results_list = engine_result.get("results", [])
    for r in results_list:
        r["weight"] = weights_map.get(r["ticker"], 1.0)
    engine_result["extras"] = compute_portfolio_extras(results_list, initial_balance, monthly_contribution, rebalancing_freq)
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
    return attach_weights_and_compute_extras(
        result, 
        weights_map, 
        request.initial_balance, 
        request.monthly_contribution, 
        request.rebalancing_freq
    )

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
    return attach_weights_and_compute_extras(
        result, 
        weights_map, 
        request.initial_balance, 
        request.monthly_contribution, 
        request.rebalancing_freq
    )

@app.post("/api/analyze/file")
async def analyze_from_file(
    file: UploadFile = File(...),
    use_ai: bool = Form(False),
    api_key: Optional[str] = Form(None),
    av_api_key: Optional[str] = Form(None),
    model: str = Form("gemini-2.5-flash"),
    check_islamic: bool = Form(False),
    check_financials: bool = Form(True),
    lang: str = Form("tr"),
    initial_balance: float = Form(10000.0),
    monthly_contribution: float = Form(0.0),
    rebalancing_freq: str = Form("none")
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
        return attach_weights_and_compute_extras(
            result, 
            weights_map, 
            initial_balance, 
            monthly_contribution, 
            rebalancing_freq
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


# ══════════════════════════════════════════════════════════════════════════
# TICKER SUGGESTION ENDPOINT
# ══════════════════════════════════════════════════════════════════════════

# ── Yardımcı Fonksiyonlar ────────────────────────────────────────────────
def tr_lower(text: str) -> str:
    """Türkçe karakter duyarlı küçük harfe çevirme."""
    return text.replace('İ', 'i').replace('I', 'ı').lower()

def tr_upper(text: str) -> str:
    """Türkçe karakter duyarlı büyük harfe çevirme."""
    return text.replace('i', 'İ').replace('ı', 'I').upper()

@app.get("/api/suggest")
async def suggest_tickers(q: str = ""):
    """Ticker autocomplete önerileri döndürür."""
    q = q.strip()
    if not q:
        return {"suggestions": []}
    
    q_norm = tr_lower(q)
    matches = []
    
    # 1. Ticker üzerinden arama (Sembol)
    for ticker, name in POPULAR_TICKERS.items():
        ticker_norm = tr_lower(ticker)
        if ticker_norm.startswith(q_norm) or q_norm in ticker_norm:
            matches.append({"ticker": ticker, "name": name})
            if len(matches) >= 15: break

    # 2. İsim üzerinden arama (Eğer liste dolmadıysa)
    if len(matches) < 10:
        for ticker, name in POPULAR_TICKERS.items():
            if any(m["ticker"] == ticker for m in matches): continue
            name_norm = tr_lower(name)
            if q_norm in name_norm:
                matches.append({"ticker": ticker, "name": name})
                if len(matches) >= 15: break
    
    return {"suggestions": matches[:15]}


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

class ChatRequest(BaseModel):
    messages: List[dict]
    portfolio_context: dict
    api_key: str
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

@app.post("/api/chat")
async def chat_api(request: ChatRequest):
    """Floating Copilot Chatbot Endpoint."""
    if not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required for AI Copilot")
    try:
        from src.core.ai_agent import generate_chat_response
        reply = generate_chat_response(request.messages, request.portfolio_context, request.api_key, request.model, request.lang)
        return {"reply": reply}
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
