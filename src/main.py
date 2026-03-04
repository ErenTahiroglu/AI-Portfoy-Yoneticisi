"""
🧩 Puzzle Parça: API Katmanı (Sadece HTTP)
============================================
FastAPI endpoint tanımları, request/response modelleri ve middleware.
İş mantığı analysis_engine.py'de yaşar.

Kullanım:
    uvicorn main:app --host 127.0.0.1 --port 8000
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional
from io import BytesIO
import os

# ── Modül importları ──────────────────────────────────────────────────────
from file_processor import extract_tickers_from_text, process_uploaded_file
from analysis_engine import AnalysisEngine

# ── FastAPI uygulaması ────────────────────────────────────────────────────
app = FastAPI(title="AI İslami Portföy Yöneticisi", version="2.0")

# ── Analiz motoru (singleton) ─────────────────────────────────────────────
engine = AnalysisEngine()

# ── Statik dosya servisi (Frontend) ───────────────────────────────────────
base_dir = os.path.dirname(os.path.abspath(__file__))
frontend_path = os.path.join(base_dir, "frontend")

if os.path.exists(frontend_path):
    app.mount("/ui", StaticFiles(directory=frontend_path, html=True), name="ui")

# ── Cache-Control middleware (tarayıcı eski dosyaları kullanmasın) ─────────
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/ui"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheMiddleware)

# ── CORS middleware ───────────────────────────────────────────────────────
# İleride web sitesi haline getirildiğinde allow_origins kısıtlanmalı:
#   allow_origins=["https://yourdomain.com", "http://localhost:8000"]
# Şimdilik tüm origin'lere açık bırakılıyor (geliştirme + gelecek entegrasyon).
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
    check_islamic: bool = True
    check_financials: bool = True

class TextAnalysisRequest(BaseModel):
    text: str
    use_ai: bool = False
    api_key: Optional[str] = None
    av_api_key: Optional[str] = None
    model: str = "gemini-2.5-flash"
    check_islamic: bool = True
    check_financials: bool = True


# ══════════════════════════════════════════════════════════════════════════
# API ENDPOINT'LERİ
# ══════════════════════════════════════════════════════════════════════════

@app.get("/")
def read_root():
    return RedirectResponse(url="/ui")

@app.post("/api/analyze")
async def analyze_portfolio(request: AnalysisRequest):
    """Ticker listesiyle portföy analizi."""
    if not request.tickers:
        raise HTTPException(status_code=400, detail="No tickers provided")
    if request.use_ai and not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required for AI analysis")
    
    return engine.analyze(
        tickers=request.tickers,
        use_ai=request.use_ai,
        api_key=request.api_key,
        av_api_key=request.av_api_key,
        model=request.model,
        check_islamic=request.check_islamic,
        check_financials=request.check_financials,
    )

@app.post("/api/analyze/text")
async def analyze_from_text(request: TextAnalysisRequest):
    """Metin kutusundan ticker çıkarıp analiz eder."""
    tickers = extract_tickers_from_text(request.text)
    if not tickers:
        raise HTTPException(status_code=400, detail="No stock symbols found in the provided text")
    
    return engine.analyze(
        tickers=tickers,
        use_ai=request.use_ai,
        api_key=request.api_key,
        av_api_key=request.av_api_key,
        model=request.model,
        check_islamic=request.check_islamic,
        check_financials=request.check_financials,
    )

@app.post("/api/analyze/file")
async def analyze_from_file(
    file: UploadFile = File(...),
    use_ai: bool = Form(False),
    api_key: Optional[str] = Form(None),
    av_api_key: Optional[str] = Form(None),
    model: str = Form("gemini-2.5-flash"),
    check_islamic: bool = Form(True),
    check_financials: bool = Form(True)
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
        
        if not tickers:
            raise HTTPException(status_code=400, detail="No stock symbols found in the uploaded file")
        
        return engine.analyze(
            tickers=tickers,
            use_ai=use_ai,
            api_key=api_key,
            av_api_key=av_api_key,
            model=model,
            check_islamic=check_islamic,
            check_financials=check_financials,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
