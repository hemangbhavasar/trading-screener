import os
import secrets
import warnings

# Load local .env file automatically if present
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import numpy as np
import pandas as pd
import uvicorn
import yfinance as yf

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*inplace.*")

app = FastAPI(title="NSE F&O Trend & Choppy Market Screener")
security = HTTPBasic()

# Read credentials from Environment (.env locally or Render Environment Variables)
AUTH_USER = os.getenv("DASHBOARD_USER")
AUTH_PASS = os.getenv("DASHBOARD_PASS")

if not AUTH_USER or not AUTH_PASS:
    print("\n" + "=" * 65)
    print("CONFIG NOTICE: DASHBOARD_USER and DASHBOARD_PASS are not set.")
    print("Add them into your local .env file:")
    print("  DASHBOARD_USER=hemang")
    print("  DASHBOARD_PASS=411057")
    print("Or configure them in your Render Dashboard under Environment.")
    print("=" * 65 + "\n")
    raise RuntimeError("Missing DASHBOARD_USER or DASHBOARD_PASS environment variables.")

def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Constant-time comparison protects against timing attacks"""
    is_user_ok = secrets.compare_digest(credentials.username.encode("utf8"), AUTH_USER.encode("utf8"))
    is_pass_ok = secrets.compare_digest(credentials.password.encode("utf8"), AUTH_PASS.encode("utf8"))
    if not (is_user_ok and is_pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INDEX_MAP = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
    "INDIA VIX": "^INDIAVIX"
}

FO_STOCKS = [
    # Banking
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "sector": "BANKING"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "sector": "BANKING"},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "sector": "BANKING"},
    {"symbol": "AXISBANK.NS", "name": "Axis Bank", "sector": "BANKING"},
    {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank", "sector": "BANKING"},
    {"symbol": "INDUSINDBK.NS", "name": "IndusInd Bank", "sector": "BANKING"},
    {"symbol": "FEDERALBNK.NS", "name": "Federal Bank", "sector": "BANKING"},
    {"symbol": "BANDHANBNK.NS", "name": "Bandhan Bank", "sector": "BANKING"},
    {"symbol": "AUBANK.NS", "name": "AU Small Finance Bank", "sector": "BANKING"},
    {"symbol": "IDFCFIRSTB.NS", "name": "IDFC First Bank", "sector": "BANKING"},
    {"symbol": "PNB.NS", "name": "Punjab National Bank", "sector": "BANKING"},
    {"symbol": "BANKBARODA.NS", "name": "Bank of Baroda", "sector": "BANKING"},
    {"symbol": "CANBK.NS", "name": "Canara Bank", "sector": "BANKING"},
    # Finance
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance", "sector": "FINANCE"},
    {"symbol": "BAJAJFINSV.NS", "name": "Bajaj Finserv", "sector": "FINANCE"},
    {"symbol": "CHOLAFIN.NS", "name": "Cholamandalam Inv", "sector": "FINANCE"},
    {"symbol": "SHRIRAMFIN.NS", "name": "Shriram Finance", "sector": "FINANCE"},
    {"symbol": "MUTHOOTFIN.NS", "name": "Muthoot Finance", "sector": "FINANCE"},
    {"symbol": "HDFCLIFE.NS", "name": "HDFC Life", "sector": "FINANCE"},
    {"symbol": "SBILIFE.NS", "name": "SBI Life", "sector": "FINANCE"},
    {"symbol": "ICICIPRULI.NS", "name": "ICICI Prudential Life", "sector": "FINANCE"},
    {"symbol": "ICICIGI.NS", "name": "ICICI Lombard", "sector": "FINANCE"},
    {"symbol": "PFC.NS", "name": "Power Finance Corp", "sector": "FINANCE"},
    {"symbol": "RECLTD.NS", "name": "REC Limited", "sector": "FINANCE"},
    # IT Services
    {"symbol": "TCS.NS", "name": "TCS", "sector": "IT"},
    {"symbol": "INFY.NS", "name": "Infosys", "sector": "IT"},
    {"symbol": "HCLTECH.NS", "name": "HCL Technologies", "sector": "IT"},
    {"symbol": "WIPRO.NS", "name": "Wipro", "sector": "IT"},
    {"symbol": "TECHM.NS", "name": "Tech Mahindra", "sector": "IT"},
    {"symbol": "PERSISTENT.NS", "name": "Persistent Systems", "sector": "IT"},
    {"symbol": "COFORGE.NS", "name": "Coforge", "sector": "IT"},
    {"symbol": "MPHASIS.NS", "name": "Mphasis", "sector": "IT"},
    {"symbol": "LTTS.NS", "name": "L&T Tech Services", "sector": "IT"},
    # Energy
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "sector": "ENERGY"},
    {"symbol": "ONGC.NS", "name": "ONGC", "sector": "ENERGY"},
    {"symbol": "BPCL.NS", "name": "BPCL", "sector": "ENERGY"},
    {"symbol": "IOC.NS", "name": "Indian Oil Corp", "sector": "ENERGY"},
    {"symbol": "NTPC.NS", "name": "NTPC", "sector": "ENERGY"},
    {"symbol": "POWERGRID.NS", "name": "Power Grid", "sector": "ENERGY"},
    {"symbol": "TATAPOWER.NS", "name": "Tata Power", "sector": "ENERGY"},
    {"symbol": "ADANIENT.NS", "name": "Adani Enterprises", "sector": "ENERGY"},
    {"symbol": "ADANIPORTS.NS", "name": "Adani Ports", "sector": "INFRA"},
    {"symbol": "GAIL.NS", "name": "GAIL India", "sector": "ENERGY"},
    {"symbol": "COALINDIA.NS", "name": "Coal India", "sector": "ENERGY"},
    # Auto
    {"symbol": "M&M.NS", "name": "Mahindra & Mahindra", "sector": "AUTO"},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki", "sector": "AUTO"},
    {"symbol": "BAJAJ-AUTO.NS", "name": "Bajaj Auto", "sector": "AUTO"},
    {"symbol": "EICHERMOT.NS", "name": "Eicher Motors", "sector": "AUTO"},
    {"symbol": "HEROMOTOCO.NS", "name": "Hero MotoCorp", "sector": "AUTO"},
    {"symbol": "TVSMOTOR.NS", "name": "TVS Motor", "sector": "AUTO"},
    {"symbol": "BHARATFORG.NS", "name": "Bharat Forge", "sector": "AUTO"},
    {"symbol": "MRF.NS", "name": "MRF Tyres", "sector": "AUTO"},
    {"symbol": "BALKRISIND.NS", "name": "Balkrishna Ind", "sector": "AUTO"},
    # Metals
    {"symbol": "TATASTEEL.NS", "name": "Tata Steel", "sector": "METALS"},
    {"symbol": "JSWSTEEL.NS", "name": "JSW Steel", "sector": "METALS"},
    {"symbol": "HINDALCO.NS", "name": "Hindalco", "sector": "METALS"},
    {"symbol": "VEDL.NS", "name": "Vedanta", "sector": "METALS"},
    {"symbol": "JINDALSTEL.NS", "name": "Jindal Steel", "sector": "METALS"},
    {"symbol": "NATIONALUM.NS", "name": "National Aluminium", "sector": "METALS"},
    {"symbol": "NMDC.NS", "name": "NMDC", "sector": "METALS"},
    {"symbol": "SAIL.NS", "name": "SAIL", "sector": "METALS"},
    # FMCG & Consumption
    {"symbol": "ITC.NS", "name": "ITC", "sector": "FMCG"},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever", "sector": "FMCG"},
    {"symbol": "NESTLEIND.NS", "name": "Nestle India", "sector": "FMCG"},
    {"symbol": "BRITANNIA.NS", "name": "Britannia", "sector": "FMCG"},
    {"symbol": "TATACONSUM.NS", "name": "Tata Consumer", "sector": "FMCG"},
    {"symbol": "DABUR.NS", "name": "Dabur India", "sector": "FMCG"},
    {"symbol": "GODREJCP.NS", "name": "Godrej Consumer", "sector": "FMCG"},
    {"symbol": "MARICO.NS", "name": "Marico", "sector": "FMCG"},
    {"symbol": "COLPAL.NS", "name": "Colgate", "sector": "FMCG"},
    {"symbol": "ASIANPAINT.NS", "name": "Asian Paints", "sector": "CONSUMPTION"},
    {"symbol": "BERGEPAINT.NS", "name": "Berger Paints", "sector": "CONSUMPTION"},
    {"symbol": "TITAN.NS", "name": "Titan", "sector": "CONSUMPTION"},
    {"symbol": "TRENT.NS", "name": "Trent", "sector": "CONSUMPTION"},
    # Healthcare
    {"symbol": "SUNPHARMA.NS", "name": "Sun Pharma", "sector": "HEALTHCARE"},
    {"symbol": "DRREDDY.NS", "name": "Dr. Reddy's", "sector": "HEALTHCARE"},
    {"symbol": "CIPLA.NS", "name": "Cipla", "sector": "HEALTHCARE"},
    {"symbol": "APOLLOHOSP.NS", "name": "Apollo Hospitals", "sector": "HEALTHCARE"},
    {"symbol": "DIVISLAB.NS", "name": "Divi's Labs", "sector": "HEALTHCARE"},
    {"symbol": "LUPIN.NS", "name": "Lupin", "sector": "HEALTHCARE"},
    {"symbol": "AUROPHARMA.NS", "name": "Aurobindo Pharma", "sector": "HEALTHCARE"},
    {"symbol": "BIOCON.NS", "name": "Biocon", "sector": "HEALTHCARE"},
    {"symbol": "TORNTPHARM.NS", "name": "Torrent Pharma", "sector": "HEALTHCARE"},
    # Capital Goods
    {"symbol": "LT.NS", "name": "Larsen & Toubro", "sector": "CAPITAL GOODS"},
    {"symbol": "SIEMENS.NS", "name": "Siemens", "sector": "CAPITAL GOODS"},
    {"symbol": "ABB.NS", "name": "ABB India", "sector": "CAPITAL GOODS"},
    {"symbol": "BEL.NS", "name": "Bharat Electronics", "sector": "CAPITAL GOODS"},
    {"symbol": "HAL.NS", "name": "Hindustan Aeronautics", "sector": "CAPITAL GOODS"},
    {"symbol": "BHEL.NS", "name": "BHEL", "sector": "CAPITAL GOODS"},
    {"symbol": "POLYCAB.NS", "name": "Polycab", "sector": "CAPITAL GOODS"},
    {"symbol": "HAVELLS.NS", "name": "Havells", "sector": "CAPITAL GOODS"},
    {"symbol": "CUMMINSIND.NS", "name": "Cummins India", "sector": "CAPITAL GOODS"},
    # Cement & Realty
    {"symbol": "ULTRACEMCO.NS", "name": "UltraTech Cement", "sector": "CEMENT"},
    {"symbol": "GRASIM.NS", "name": "Grasim Industries", "sector": "CEMENT"},
    {"symbol": "AMBUJACEM.NS", "name": "Ambuja Cements", "sector": "CEMENT"},
    {"symbol": "ACC.NS", "name": "ACC Limited", "sector": "CEMENT"},
    {"symbol": "DLF.NS", "name": "DLF", "sector": "REALTY"},
    {"symbol": "GODREJPROP.NS", "name": "Godrej Properties", "sector": "REALTY"},
    {"symbol": "OBEROIRLTY.NS", "name": "Oberoi Realty", "sector": "REALTY"},
    # Telecom & Chemicals
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel", "sector": "TELECOM"},
    {"symbol": "IDEA.NS", "name": "Vodafone Idea", "sector": "TELECOM"},
    {"symbol": "PIDILITIND.NS", "name": "Pidilite", "sector": "CHEMICALS"},
    {"symbol": "SRF.NS", "name": "SRF Limited", "sector": "CHEMICALS"},
    {"symbol": "NAVINFLUOR.NS", "name": "Navin Fluorine", "sector": "CHEMICALS"},
    {"symbol": "DEEPAKNTR.NS", "name": "Deepak Nitrite", "sector": "CHEMICALS"}
]

CACHE = {"last_updated": None, "indices": [], "stocks": []}

def calculate_pure_trend(df: pd.DataFrame) -> dict:
    if df is None or len(df) < 5:
        return {"status": "downtrend", "score": -1}
    close = df['Close']
    length = len(df)
    ema200_len = 200 if length >= 200 else length - 1
    ema50_len = 50 if length >= 50 else min(20, length - 1)
    
    # Pure native Pandas EMA (no external dependency)
    ema200 = close.ewm(span=ema200_len, adjust=False).mean()
    ema50 = close.ewm(span=ema50_len, adjust=False).mean()
    
    c = float(close.iloc[-1])
    e200 = float(ema200.iloc[-1]) if not pd.isna(ema200.iloc[-1]) else c
    e50 = float(ema50.iloc[-1]) if not pd.isna(ema50.iloc[-1]) else c
    is_bull = (c >= e200) or (e50 >= e200)
    return {
        "status": "uptrend" if is_bull else "downtrend",
        "score": 1 if is_bull else -1,
        "c": round(c, 2),
        "e200": round(e200, 2)
    }

def calculate_pure_choppy(close_series: pd.Series) -> dict:
    if close_series is None or len(close_series) < 17:
        return {"score": 0, "status": "chop-red", "label": "CHOPPY"}
    closes = close_series.values
    hist_list = []
    for offset in range(1, 11):
        idx = len(closes) - offset
        if idx < 6:
            hist_list.append(0)
            continue
        c1, c2, c3, c4, c5, c6 = closes[idx], closes[idx-1], closes[idx-2], closes[idx-3], closes[idx-4], closes[idx-5]
        is_bull = (
            (c1 > c2 and c2 > c3 and c3 > c4 and c4 > c5 and c5 > c6) or
            (c1 > c2 and c2 > c3 and c3 > c4) or
            (c2 > c3 and c3 > c4 and c4 > c5 and c5 > c6) or
            (c1 > c2 and c3 > c4 and c4 > c5 and c5 > c6) or
            (c1 > c2 and c2 > c3 and c4 > c5 and c5 > c6) or
            (c1 > c2 and c2 > c3 and c3 > c4 and c5 > c6) or
            (c1 > c2 and c2 > c3 and c3 > c4 and c4 > c5)
        )
        is_bear = (
            (c1 < c2 and c2 < c3 and c3 < c4 and c4 < c5 and c5 < c6) or
            (c1 < c2 and c2 < c3 and c3 < c4) or
            (c2 < c3 and c3 < c4 and c4 < c5 and c5 < c6) or
            (c1 < c2 and c3 < c4 and c4 < c5 and c5 < c6) or
            (c1 < c2 and c2 < c3 and c4 < c5 and c5 < c6) or
            (c1 < c2 and c2 < c3 and c3 < c4 and c5 < c6) or
            (c1 < c2 and c2 < c3 and c3 < c4 and c4 < c5)
        )
        hist_list.append(10 if (is_bull or is_bear) else 0)
    score = int(sum(hist_list))
    if score >= 50:
        return {"score": score, "status": "chop-green", "label": "GOOD"}
    elif score >= 30:
        return {"score": score, "status": "chop-orange", "label": "POTENTIAL"}
    return {"score": score, "status": "chop-red", "label": "CHOPPY"}

def resample_bars(df_source: pd.DataFrame, rule: str) -> pd.DataFrame:
    try:
        resampled = df_source.resample(rule).agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        })
        return resampled.dropna()
    except Exception:
        return pd.DataFrame()

def extract_stock_df(multi_df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    try:
        if isinstance(multi_df.columns, pd.MultiIndex):
            if symbol in multi_df.columns.levels[0]:
                df = multi_df[symbol].copy()
            elif symbol in multi_df.columns.levels[1]:
                df = multi_df.xs(symbol, axis=1, level=1).copy()
            else:
                return pd.DataFrame()
        else:
            df = multi_df.copy()
        return df.dropna(how='all')
    except Exception:
        return pd.DataFrame()

# Serve UI at root URL with password protection
@app.get("/", response_class=HTMLResponse)
def serve_dashboard(username: str = Depends(authenticate_user)):
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        return HTMLResponse(f"<h3>Error loading index.html: {e}</h3>", status_code=500)

# Scan endpoint (Internal to authenticated session)
@app.get("/api/scan")
def scan_all():
    global CACHE
    now = datetime.now()
    if CACHE["last_updated"] and (now - CACHE["last_updated"]).total_seconds() < 10:
        return {
            "timestamp": CACHE["last_updated"].isoformat(),
            "indices": CACHE["indices"],
            "stocks": CACHE["stocks"]
        }

    symbol_list = [s["symbol"] for s in FO_STOCKS]

    indices_data = []
    try:
        raw_idx = yf.download(list(INDEX_MAP.values()), period="5d", interval="1d", progress=False)
        for label, sym in INDEX_MAP.items():
            df_sym = extract_stock_df(raw_idx, sym)
            if not df_sym.empty and len(df_sym) >= 2:
                curr = float(df_sym['Close'].iloc[-1])
                prev = float(df_sym['Close'].iloc[-2])
                chg = curr - prev
                pct = (chg / prev) * 100
                indices_data.append({
                    "name": label,
                    "value": round(curr, 2),
                    "change": round(chg, 2),
                    "pct": round(pct, 2)
                })
            else:
                indices_data.append({"name": label, "value": 0.0, "change": 0.0, "pct": 0.0})
    except Exception:
        pass

    raw_5m = yf.download(symbol_list, period="5d", interval="5m", progress=False)
    raw_1h = yf.download(symbol_list, period="60d", interval="60m", progress=False)
    raw_daily = yf.download(symbol_list, period="1y", interval="1d", progress=False)

    processed = []
    for item in FO_STOCKS:
        sym = item["symbol"]
        res = {
            "symbol": sym.replace(".NS", ""),
            "name": item["name"],
            "sector": item["sector"],
            "ltp": 0.0,
            "change": 0.0,
            "trends": {},
            "choppy": {},
            "candles": [],
            "bull_count": 0,
            "bear_count": 0,
            "trend_signal": "NEUTRAL",
            "avg_chop": 0,
            "chop_signal": "CHOPPY"
        }
        df_5m = extract_stock_df(raw_5m, sym)
        df_1h_src = extract_stock_df(raw_1h, sym)
        df_daily_src = extract_stock_df(raw_daily, sym)

        if not df_daily_src.empty and len(df_daily_src) >= 2:
            curr_c = float(df_daily_src['Close'].iloc[-1])
            prev_c = float(df_daily_src['Close'].iloc[-2])
            res["ltp"] = round(curr_c, 2)
            res["change"] = round(((curr_c - prev_c) / prev_c) * 100, 2)
            recent = df_daily_src.tail(30)
            res["candles"] = [
                {
                    "o": round(float(r['Open']), 1),
                    "h": round(float(r['High']), 1),
                    "l": round(float(r['Low']), 1),
                    "c": round(float(r['Close']), 1)
                }
                for _, r in recent.iterrows()
            ]

        df_15m = resample_bars(df_5m, '15min') if not df_5m.empty else pd.DataFrame()
        df_30m = resample_bars(df_5m, '30min') if not df_5m.empty else pd.DataFrame()
        df_1h = resample_bars(df_5m, '60min') if not df_5m.empty else pd.DataFrame()
        df_4h = resample_bars(df_1h_src, '4h') if not df_1h_src.empty else pd.DataFrame()
        df_1w = resample_bars(df_daily_src, '1W') if not df_daily_src.empty else pd.DataFrame()

        timeframe_dfs = {
            "5m": df_5m,
            "15m": df_15m,
            "30m": df_30m,
            "1h": df_1h,
            "4h": df_4h,
            "1D": df_daily_src,
            "1W": df_1w
        }

        bulls = 0
        bears = 0
        chop_vals = []

        for tf_name, frame in timeframe_dfs.items():
            t_res = calculate_pure_trend(frame)
            res["trends"][tf_name] = t_res
            if t_res["status"] == "uptrend":
                bulls += 1
            else:
                bears += 1

            c_res = calculate_pure_choppy(frame['Close'] if not frame.empty else None)
            res["choppy"][tf_name] = c_res
            chop_vals.append(c_res["score"])

        res["bull_count"] = bulls
        res["bear_count"] = bears
        res["avg_chop"] = round(sum(chop_vals) / len(chop_vals)) if chop_vals else 0

        if bulls >= 6:
            res["trend_signal"] = "STRONG BULL"
        elif bears >= 6:
            res["trend_signal"] = "STRONG BEAR"
        elif bulls >= 4 and res["trends"].get("5m", {}).get("status") == "downtrend":
            res["trend_signal"] = "DIP BUY WATCH"
        else:
            res["trend_signal"] = "MIXED"

        if res["avg_chop"] >= 50:
            res["chop_signal"] = "ACTIVE TREND"
        elif res["avg_chop"] >= 30:
            res["chop_signal"] = "POTENTIAL CHOP"
        else:
            res["chop_signal"] = "HEAVY CHOP"

        processed.append(res)

    processed.sort(key=lambda x: x["bull_count"], reverse=True)
    CACHE["last_updated"] = datetime.now()
    CACHE["indices"] = indices_data
    CACHE["stocks"] = processed

    return {
        "timestamp": CACHE["last_updated"].isoformat(),
        "indices": indices_data,
        "stocks": processed
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)