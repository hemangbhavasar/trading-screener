# NSE F&O Trend & Choppy Market Screener

A real-time web-based screener for NSE F&O stocks that analyzes multi-timeframe trends using EMA-based indicators and identifies choppy market conditions. Built with FastAPI, yfinance, and a responsive web dashboard with Basic Authentication.

## Features

### Trend Finder Matrix
- **Multi-timeframe analysis** across 5m, 15m, 30m, 1h, 4h, 1D, and 1W
- **200 EMA-based trend detection** using native pandas EMA calculations
- **Smart confluence signals**: ALL 7 GREEN, ALL 7 RED, STRONG BULL/BEAR, DIP BUY WATCH
- **Bias indicators** showing overall market sentiment
- **Sector-wise grouping** for easier analysis

### Choppy Market Matrix
- **TradingRush-style choppy detection** using 10-bar lookback pattern analysis
- **Scoring system** (0-100) where higher scores indicate better trending conditions
- **Color-coded signals**: GOOD (≥50), POTENTIAL (30-40), CHOPPY (≤20)
- **Helps identify** when markets are trending vs ranging/choppy

### Dashboard Features
- **Live index tracking** for NIFTY 50, BANK NIFTY, FINNIFTY, and INDIA VIX
- **Auto-refresh** with customizable intervals (seconds/minutes)
- **Advanced filtering** by sector, trend signals, and choppy conditions
- **Search functionality** by stock symbol or name
- **Detailed stock view** with 30-day candlestick chart and timeframe breakdown
- **Password-protected** dashboard with HTTP Basic Authentication
- **In-memory caching** (10-second cache for API responses)

## Tech Stack

- **Backend**: FastAPI 0.110+, Uvicorn
- **Data**: yfinance 0.2.36 for NSE market data
- **Analysis**: pandas 2.2+, numpy 1.26+
- **Frontend**: Vanilla HTML/CSS/JavaScript with Chart.js-style canvas rendering
- **Auth**: HTTP Basic Auth with constant-time comparison
- **Config**: python-dotenv for environment variables

## F&O Stock Universe

The screener covers 100+ NSE F&O stocks across sectors including:
- **Banking** (HDFC Bank, ICICI Bank, SBI, Axis Bank, etc.)
- **Finance** (Bajaj Finance, Bajaj Finserv, HDFC Life, etc.)
- **IT** (TCS, Infosys, HCL Tech, Wipro, etc.)
- **Energy** (Reliance, ONGC, BPCL, NTPC, etc.)
- **Auto** (Maruti, M&M, Bajaj Auto, Hero MotoCorp, etc.)
- **Metals** (Tata Steel, JSW Steel, Hindalco, etc.)
- **FMCG & Consumption** (ITC, HUL, Nestle, Asian Paints, etc.)
- **Healthcare** (Sun Pharma, Dr. Reddy's, Cipla, etc.)
- **Capital Goods** (L&T, Siemens, ABB, HAL, etc.)
- **Cement & Realty** (UltraTech, DLF, Godrej Properties, etc.)
- **Telecom & Chemicals** (Bharti Airtel, Pidilite, SRF, etc.)

## Installation

### Prerequisites
- Python 3.11+ (as specified in `.python-version`)
- pip package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Trading
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   DASHBOARD_USER=your_username
   DASHBOARD_PASS=your_password
   PORT=8000
   ```
   
   *Note: If not set, the app will raise a RuntimeError with configuration instructions.*

4. **Run the application**
   ```bash
   python app.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```

5. **Access the dashboard**
   
   Open your browser and navigate to `http://localhost:8000`. You'll be prompted for Basic Auth credentials.

## Usage

### Trend Finder
- View stocks sorted by trend confluence across all timeframes
- Filter by: ALL GREEN, ALL RED, STRONG BULL (6+/7), STRONG BEAR (6+/7), DIP BUY WATCH, MIXED
- Click any stock row to see detailed breakdown with 200 EMA values per timeframe and 30-day price action

### Choppy Market
- Switch to "CHOPPY MARKET MATRIX" tab
- Scores range 0-100 based on price structure patterns
- Filter by: ALL GOOD (≥50), ALL CHOP (≤20), GOOD AVG, POTENTIAL, CHOP AVG
- Higher scores indicate cleaner trending conditions suitable for trend-following strategies

### Controls
- **AUTO/MANUAL refresh**: Toggle between automatic updates and manual scanning
- **Refresh interval**: Set custom interval in seconds or minutes (min 5s)
- **Sector filter**: Focus on specific sectors
- **Sort options**: Sort by green/red count, choppy score, price change, or symbol
- **Search**: Find specific stocks quickly

## API Endpoints

- `GET /` - Protected dashboard UI (requires Basic Auth)
- `GET /api/scan` - Returns scan results with indices and all stock analysis (cached for 10 seconds)

## Technical Details

### Trend Calculation
Uses native pandas EMA: `close.ewm(span=period, adjust=False).mean()`. A stock is in uptrend if current close ≥ EMA200 or EMA50 ≥ EMA200.

### Choppy Detection
Analyzes last 10 bars with pattern recognition looking for consecutive higher/lower closes across various combinations. Scores 10 points per "trending" pattern detected, with thresholds:
- ≥50: GOOD (clean trend)
- 30-40: POTENTIAL (transitioning)
- ≤20: CHOPPY (ranging/whipsaw)

### Data Resampling
- 5m data resampled to 15m, 30m, 1h using OHLCV aggregation
- 1h data resampled to 4h
- Daily data resampled to weekly (1W)

### Performance
- 10-second in-memory cache prevents excessive API calls
- Concurrent data fetching for indices and all stocks
- Efficient pandas operations for real-time analysis

## Security

- HTTP Basic Authentication with `secrets.compare_digest()` for constant-time comparison (prevents timing attacks)
- CORS enabled for all origins (suitable for internal/development use)
- Credentials loaded from environment variables, never hardcoded
- Warnings suppressed for cleaner logs

## Deployment

This app is designed to run on platforms like Render, Railway, or any Python hosting service. Make sure to set `DASHBOARD_USER`, `DASHBOARD_PASS`, and `PORT` environment variables in your deployment platform.

## Disclaimer

This tool is for educational and informational purposes only. It is not financial advice. Trading in F&O markets carries substantial risk. Always do your own research and consult with a qualified financial advisor before making any trading decisions.

## License

[Add your license information here]
