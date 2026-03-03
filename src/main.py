from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import uvicorn
from io import BytesIO

# Import modules
from data_fetcher import get_financials
from file_processor import extract_tickers_from_text, process_uploaded_file
from ai_agent import generate_report

app = FastAPI(title="Islamic Portfolio Manager API")

import sys

# Determine the correct base directory whether running as script or pyinstaller exe
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running in a PyInstaller bundle, the data is unpacked / moved to _MEIPASS
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
else:
    # Running in normal Python environment
    base_dir = os.path.dirname(os.path.abspath(__file__))

frontend_path = os.path.join(base_dir, "frontend")

# Serve the frontend directory for the UI
if os.path.exists(frontend_path):
    app.mount("/ui", StaticFiles(directory=frontend_path, html=True), name="ui")

# Force browsers to always revalidate cached files (fixes stale JS/CSS issues)
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

# Redirect root to UI
@app.get("/")
def read_root():
    return RedirectResponse(url="/ui")

# Add CORS middleware to allow requests from our separate frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

def detect_market_and_ticker(ticker: str):
    """Auto-detects whether the ticker is US, BIST (TR) or TEFAS (TR)."""
    if ticker.endswith(".IS"):
        return "TR", ticker, False
    
    import yfinance as yf
    try:
        if yf.Ticker(ticker).fast_info.get('lastPrice', 0) > 0:
            return "US", ticker, False
    except:
        pass
        
    try:
        if yf.Ticker(f"{ticker}.IS").fast_info.get('lastPrice', 0) > 0:
            return "TR", f"{ticker}.IS", False
    except:
        pass
        
    # TEFAS fallback: short codes (2-5 chars) that weren't found on Yahoo
    if len(ticker) <= 5:
        return "TR", ticker, True
        
    return "US", ticker, False

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Islamic Portfolio Manager API is running"}

@app.post("/api/analyze")
async def analyze_portfolio(request: AnalysisRequest):
    if not request.tickers:
        raise HTTPException(status_code=400, detail="No tickers provided")
        
    if request.use_ai and not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required for AI analysis")

    results = []
    
    # Initialize the financial analyzers selectively
    us_analyzer = None
    tr_analyzer = None
    init_errors = []
    if request.check_financials:
        try:
            from portfolio_analyzer import HisseAnaliz
            us_analyzer = HisseAnaliz(av_key=request.av_api_key)
        except Exception as e:
            init_errors.append(f"US Analyzer hatası: {str(e)}")
        try:
            from bist_analyzer import HisseAnaliz as BistHisseAnaliz
            tr_analyzer = BistHisseAnaliz()
        except Exception as e:
            init_errors.append(f"TR Analyzer hatası: {str(e)}")
    
    for ticker in request.tickers:
        ticker = ticker.upper().strip()
        if not ticker:
            continue
            
        market, fetcher_ticker, is_tefas = detect_market_and_ticker(ticker)
        result_entry = {"ticker": ticker, "market": market}
        
        # 1. Islamic / Halal Compliance Check (independent)
        data = None
        if request.check_islamic:
            if is_tefas:
                # Check if the TEFAS fund is a "Katılım" (Participation/Islamic) type fund
                is_katilim = False
                fund_note = ""
                try:
                    import yfinance as yf
                    fund_info = yf.Ticker(fetcher_ticker + ".IS").info
                    fund_name = fund_info.get('longName', '') or fund_info.get('shortName', '') or ''
                except Exception:
                    fund_name = ''
                
                katilim_keywords = ['katılım', 'katilim', 'participation', 'sukuk', 'islamic']
                if any(kw in fund_name.lower() for kw in katilim_keywords):
                    is_katilim = True
                    fund_note = f"✅ Katılım Fonu ({fund_name})"
                else:
                    fund_note = f"⚠️ Bu fon resmi olarak 'Katılım' türünde değildir. Bazı fonlar katılım ilkelerini uygulasa da resmi sınıflandırması farklı olabilir."
                    if fund_name:
                        fund_note = f"Fon: {fund_name} — " + fund_note
                # Get the fund's first trading date
                fund_start_date = None
                fund_age_text = ""
                try:
                    import yfinance as yf
                    from datetime import datetime, timedelta
                    hist = yf.Ticker(fetcher_ticker + ".IS").history(period="max")
                    if hist is not None and not hist.empty:
                        first_date = hist.index[0]
                        fund_start_date = first_date.strftime("%d.%m.%Y")
                        days_active = (datetime.now() - first_date.to_pydatetime().replace(tzinfo=None)).days
                        years = days_active // 365
                        months = (days_active % 365) // 30
                        if years > 0:
                            fund_age_text = f"{years} yıl {months} aydır aktif"
                        else:
                            fund_age_text = f"{months} aydır aktif"
                except Exception:
                    pass
                
                status = "Katılım Fonu (Uygun)" if is_katilim else "Katılım Fonu Değil"
                data = {
                    "status": status,
                    "is_etf": True,
                    "holdings_str": "",
                    "purification_ratio": 0,
                    "debt_ratio": 0,
                    "fund_note": fund_note,
                    "fund_start_date": fund_start_date,
                    "fund_age": fund_age_text
                }
            else:
                data, error = get_financials(fetcher_ticker)
                if error or data is None:
                    result_entry["islamic_error"] = error or "İslami veri bulunamadı"
                    data = None
                    
            if data is not None:
                if is_tefas:
                    # For TEFAS funds: only show status and fund_note, no ratios
                    result_entry["status"] = data.get('status', 'Bilinmiyor')
                    result_entry["is_etf"] = True
                    result_entry["is_tefas"] = True
                    result_entry["fund_note"] = data.get('fund_note', '')
                    result_entry["fund_start_date"] = data.get('fund_start_date')
                    result_entry["fund_age"] = data.get('fund_age', '')
                else:
                    result_entry["purification_ratio"] = round(data.get('purification_ratio', 0), 2)
                    result_entry["debt_ratio"] = round(data.get('debt_ratio', 0), 2)
                    result_entry["interest"] = data.get('interest', 0)
                    result_entry["status"] = data.get('status', 'Bilinmiyor')
                    result_entry["is_etf"] = data.get("is_etf", False)
            
        # 2. Financial Return & Historical Check (independent)
        fin_data = None
        if request.check_financials:
            analyzer = tr_analyzer if market == "TR" else us_analyzer
            if analyzer:
                try:
                    fin_data = analyzer.analiz_et(ticker)
                    if fin_data:
                        result_entry["financials"] = fin_data
                    else:
                        result_entry["fin_error"] = "Hisse için detaylı finansal veri kurulamadı."
                except Exception as e:
                    if str(e) == "ALPHA_VANTAGE_RATE_LIMIT":
                        result_entry["fin_error"] = "⚠️ **Alpha Vantage Kotası Doldu**<br>Ücretsiz API limitiniz (günlük) dolmuştur. Diğer kaynaklardan (Yahoo/Stooq) da veri çekilemedi. Analiz için yarına kadar bekleyin."
                    else:
                        result_entry["fin_error"] = f"Finans modülü hatası: {str(e)}"
            elif init_errors:
                result_entry["fin_error"] = " | ".join(init_errors)
                
        # 3. AI Comment Generator (uses whatever data is available)
        if request.use_ai:
            try:
                islamic_dict = data if data is not None else {}
                ai_comment = generate_report(
                    ticker=ticker,
                    data=islamic_dict,
                    api_key=request.api_key,
                    model_name=request.model,
                    check_islamic=request.check_islamic,
                    check_financials=request.check_financials,
                    fin_data=fin_data,
                    market=market
                )
                result_entry["ai_comment"] = ai_comment
            except Exception as e:
                result_entry["ai_comment"] = f"API Error: {str(e)}"

        results.append(result_entry)

    return {"results": results}

@app.post("/api/analyze/text")
async def analyze_from_text(request: TextAnalysisRequest):
    tickers = extract_tickers_from_text(request.text)
    if not tickers:
        raise HTTPException(status_code=400, detail="No stock symbols found in the provided text")
        
    analysis_req = AnalysisRequest.model_validate({
        "tickers": tickers,
        "use_ai": request.use_ai,
        "api_key": request.api_key,
        "av_api_key": request.av_api_key,
        "model": request.model,
        "check_islamic": request.check_islamic,
        "check_financials": request.check_financials
    })
    return await analyze_portfolio(analysis_req)

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
    try:
        # Read file contents into an in-memory buffer to simulate what process_uploaded_file expects
        contents = await file.read()
        
        # Create a mock file object with .name attribute matching original file
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
            # Read file bytes into bytesIO for pandas
            tickers = process_uploaded_file(buffer)
        else:
            tickers = process_uploaded_file(mock_file)

        if not tickers:
            raise HTTPException(status_code=400, detail="No stock symbols found in the uploaded file")
            
        analysis_req = AnalysisRequest.model_validate({
            "tickers": tickers,
            "use_ai": use_ai,
            "api_key": api_key,
            "av_api_key": av_api_key,
            "model": model,
            "check_islamic": check_islamic,
            "check_financials": check_financials
        })
        return await analyze_portfolio(analysis_req)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# Remove or comment out the following lines before running with uvicorn directly
# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
