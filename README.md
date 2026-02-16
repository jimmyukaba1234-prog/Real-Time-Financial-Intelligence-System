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

## What's Next (Roadmap)
- Machine Learning predictions 
  - Store results in predictions table
- Streamlit dashboard:
  - Live ticker overview
  - Intraday charts
  - News feed
  - Metrics & predictions visualization
- Deployment: Streamlit Community Cloud 
- Enhancements:
  - Email alerts 
  - More sources 
