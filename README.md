# Financial-Data-Etl
Automated pipeline for scraping, processing, storing, and analyzing stock market data from major tech companies (Magnificent 7-inspired tickers: AAPL, GOOGL, MSFT, AMZN, TSLA, META).  Built in Python with a focus on modularity, scheduling, cloud backup (Google Drive), and future ML/dashboard integration.

## Current Features (v0.1 – Data Acquisition & ETL)

- **Data Scraping** (FinancialScraper class)
  - Historical prices, financial statements, balance sheets, cash flows via `yfinance`
  - Live quotes and intraday (1m/5m/15m) data
  - Batch real-time 1-minute data for multiple tickers
  - Market news headlines from MarketWatch (web scraping with BeautifulSoup)
  - Market open/closed status checker

- **Scheduled Jobs**
  - Weekly full scrape + save (configurable interval)
  - Saves raw data as timestamped CSVs/JSONs

- **ETL Pipeline** (DataPipeline class)
  - Extract: Downloads raw files from Google Drive
  - Transform: Cleans data, fills NaNs, calculates daily/cumulative returns, SMA(20/50), RSI(14)
  - Load: Appends to SQLite database (financial_data.db)
  - Saves cleaned CSVs and uploads back to Drive

- **Storage & Backup**
  - Google Drive integration (GoogleDriveHandler) with OAuth2 + token refresh
  - Uploads both raw and cleaned files to a dedicated folder

- **Database Layer** (DatabaseHandler)
  - SQLite tables: stock_prices, predictions, financial_metrics
  - Query helpers: latest prices, historical ranges, aggregated metrics (volatility, avg volume, etc.)
  - Prediction storage (ready for future ML outputs)

- **Setup & Dev Tools**
  - database.py: Script to reset DB + populate with realistic synthetic data (90 days per ticker)

## Tech Stack
- Python 3.10+
- Libraries: yfinance, pandas, numpy, requests, beautifulsoup4, schedule, sqlite3, google-api-python-client
- Storage: Local SQLite + Google Drive (for raw/cleaned backups)
- Authentication: OAuth2 (Installed App Flow) with token caching


##. Machine Learning Layer
- RandomForestRegressor with time-series features (lags, rolling stats, RSI, MACD)
- Future price prediction (configurable horizon)
- Trading signals: **STRONG BUY / BUY / HOLD / SELL / STRONG SELL**
- Model persistence with joblib

## 5. Visualization Layer (Complete)

**Streamlit Web App** (`app.py`)
- Clean, modern, and user-friendly interface
- Live market quotes
- Interactive charts and technical indicators
- ML predictions with confidence intervals
- One-click report generation

![Streamlit Web App](screenshots/streamlit_dashboard.png)

**Advanced Analytics Dashboard** (`dashboard.py`)
- Built with Plotly Dash for deeper analysis
- Multi-tab interface (Charts, Data, Metrics, Correlation)
- Auto-refreshing live quotes
- Professional visualizations and correlation analysis

![Dash Advanced Dashboard](screenshots/dash_dashboard.png)
