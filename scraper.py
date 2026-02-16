import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import schedule
import time
from typing import List, Dict
import json
import os
from config import FINANCIAL_SOURCES

class FinancialScraper:
    def __init__(self):
        self.tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META']
    
    def scrape_yahoo_finance(self, tickers: List[str] = None, period: str = "1y", interval: str = "1d") -> Dict:
        """Scrape financial data from Yahoo Finance"""
        if tickers is None:
            tickers = self.tickers
        
        data = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                
                # Get historical data
                hist = stock.history(period=period, interval=interval)
                
                # Get financials
                financials = stock.financials
                balance_sheet = stock.balance_sheet
                cashflow = stock.cashflow
                
                # Get info (includes live data)
                info = stock.info
                
                # Get live quote
                live_quote = self.get_live_quote(ticker)
                
                data[ticker] = {
                    'historical': hist,
                    'financials': financials,
                    'balance_sheet': balance_sheet,
                    'cashflow': cashflow,
                    'info': info,
                    'live_quote': live_quote,
                    'timestamp': datetime.now()
                }
                
                print(f"Scraped data for {ticker}")
                
            except Exception as e:
                print(f"Error scraping {ticker}: {e}")
        
        return data
    
    def get_live_quote(self, ticker: str) -> Dict:
        """Get live market quote for a ticker"""
        try:
            stock = yf.Ticker(ticker)
            
            # Get live quote using info
            info = stock.info
            
            live_data = {
                'current_price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                'previous_close': info.get('previousClose', 0),
                'open': info.get('open', 0),
                'day_high': info.get('dayHigh', 0),
                'day_low': info.get('dayLow', 0),
                'volume': info.get('volume', 0),
                'avg_volume': info.get('averageVolume', 0),
                'market_cap': info.get('marketCap', 0),
                'bid': info.get('bid', 0),
                'ask': info.get('ask', 0),
                'bid_size': info.get('bidSize', 0),
                'ask_size': info.get('askSize', 0),
                'last_update': datetime.now().isoformat(),
                'change': info.get('regularMarketChange', 0),
                'change_percent': info.get('regularMarketChangePercent', 0),
                'currency': info.get('currency', 'USD')
            }
            
            return live_data
            
        except Exception as e:
            print(f"Error getting live quote for {ticker}: {e}")
            return {}
    
    def get_intraday_data(self, ticker: str, period: str = "1d", interval: str = "5m") -> pd.DataFrame:
        """Get intraday/live data with minute intervals"""
        try:
            stock = yf.Ticker(ticker)
            
            # For intraday data, use shorter periods
            # Valid intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m
            # Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
            intraday = stock.history(period=period, interval=interval)
            
            if not intraday.empty:
                print(f"✅ Got intraday data for {ticker}: {len(intraday)} intervals")
                return intraday
            else:
                print(f"⚠️ No intraday data for {ticker}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error getting intraday data for {ticker}: {e}")
            return pd.DataFrame()
    
    def get_realtime_tickers_data(self, tickers: List[str] = None) -> Dict:
        """Get real-time data for multiple tickers at once"""
        if tickers is None:
            tickers = self.tickers
        
        realtime_data = {}
        
        try:
            # Download batch data (more efficient)
            print(f"📡 Getting real-time data for {len(tickers)} tickers...")
            
            # Use yf.download for multiple tickers at once
            data = yf.download(
                tickers=tickers,
                period="1d",
                interval="1m",  # 1-minute intervals for real-time
                group_by='ticker',
                progress=False
            )
            
            for ticker in tickers:
                if ticker in data.columns.levels[0]:
                    ticker_data = data[ticker].copy()
                    
                    # Get the latest (most recent) data point
                    if not ticker_data.empty:
                        latest = ticker_data.iloc[-1]
                        
                        realtime_data[ticker] = {
                            'timestamp': datetime.now().isoformat(),
                            'open': latest.get('Open', 0),
                            'high': latest.get('High', 0),
                            'low': latest.get('Low', 0),
                            'close': latest.get('Close', 0),
                            'volume': latest.get('Volume', 0),
                            'last_updated': ticker_data.index[-1].strftime('%Y-%m-%d %H:%M:%S')
                        }
                    else:
                        realtime_data[ticker] = {'error': 'No data available'}
                else:
                    realtime_data[ticker] = {'error': 'Ticker not found in data'}
            
            print(f"✅ Real-time data retrieved for {len(realtime_data)} tickers")
            
        except Exception as e:
            print(f"❌ Error getting real-time data: {e}")
            # Fallback to individual quotes
            for ticker in tickers:
                realtime_data[ticker] = self.get_live_quote(ticker)
        
        return realtime_data
    
    def scrape_marketwatch(self):
        """Scrape market news and insights"""
        url = "https://www.marketwatch.com/latest-news"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.content, 'html.parser')
        
        articles = []
        for article in soup.find_all('div', class_='article__content', limit=10):
            title = article.find('h3', class_='article__headline')
            summary = article.find('p', class_='article__summary')
            
            if title and summary:
                articles.append({
                    'title': title.text.strip(),
                    'summary': summary.text.strip(),
                    'timestamp': datetime.now()
                })
        
        return articles
    
    def save_to_files(self, data: Dict, path: str):
        """Save scraped data to CSV and JSON files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save each ticker's data
        for ticker, ticker_data in data.items():
            # Save historical data
            if 'historical' in ticker_data and not ticker_data['historical'].empty:
                hist_path = f"{path}/{ticker}_historical_{timestamp}.csv"
                ticker_data['historical'].to_csv(hist_path)
            
            # Save financials
            if 'financials' in ticker_data and not ticker_data['financials'].empty:
                fin_path = f"{path}/{ticker}_financials_{timestamp}.csv"
                ticker_data['financials'].to_csv(fin_path)
            
            # Save live quote data
            if 'live_quote' in ticker_data and ticker_data['live_quote']:
                live_path = f"{path}/{ticker}_live_{timestamp}.json"
                with open(live_path, 'w') as f:
                    json.dump(ticker_data['live_quote'], f, indent=2)
        
        # Save metadata
        metadata = {
            'scrape_timestamp': timestamp,
            'tickers_scraped': list(data.keys()),
            'source': 'yahoo_finance'
        }
        
        with open(f"{path}/metadata_{timestamp}.json", 'w') as f:
            json.dump(metadata, f)
        
        return metadata
    
    def weekly_scrape_job(self):
        """Scheduled weekly scraping job"""
        print(f"Starting weekly scrape at {datetime.now()}")
        
        # Scrape data
        data = self.scrape_yahoo_finance()
        
        # Save locally
        from config import RAW_DATA_PATH
        import os
        os.makedirs(RAW_DATA_PATH, exist_ok=True)
        
        metadata = self.save_to_files(data, RAW_DATA_PATH)
        
        # Upload to Google Drive
        from gdrive_handler import GoogleDriveHandler
        gdrive = GoogleDriveHandler()
        
        # Upload all CSV files
        for file in os.listdir(RAW_DATA_PATH):
            if file.endswith('.csv') or file.endswith('.json'):
                file_path = os.path.join(RAW_DATA_PATH, file)
                mime_type = 'text/csv' if file.endswith('.csv') else 'application/json'
                gdrive.upload_file(file_path, file, mime_type)
        
        print(f"Weekly scrape completed at {datetime.now()}")
        return metadata
    
    def get_live_dashboard_data(self):
        """Get data specifically for live dashboard display"""
        print("🔄 Getting live dashboard data...")
        
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'market_status': self.get_market_status(),
            'tickers': {},
            'news': self.scrape_marketwatch()[:5]  # Get top 5 news
        }
        
        # Get real-time data for all tickers
        realtime_data = self.get_realtime_tickers_data()
        
        for ticker in self.tickers:
            if ticker in realtime_data:
                dashboard_data['tickers'][ticker] = {
                    'realtime': realtime_data[ticker],
                    'quote': self.get_live_quote(ticker),
                    'intraday': self.get_intraday_data(ticker, period="1d", interval="15m").tail(20).to_dict('records')
                }
        
        return dashboard_data
    
    def get_market_status(self):
        """Check if US market is open"""
        now = datetime.now()
        
        # US Market hours: 9:30 AM - 4:00 PM EST
        # Convert to EST (simplified)
        est_hour = now.hour - 5  # Rough EST conversion
        
        # Check if weekday
        if now.weekday() >= 5:  # Saturday (5) or Sunday (6)
            return {
                'is_open': False,
                'status': 'CLOSED (Weekend)',
                'next_open': 'Monday 9:30 AM EST',
                'current_time': now.strftime('%Y-%m-%d %H:%M:%S')
            }
        
        # Check market hours
        if 9.5 <= est_hour < 16:
            return {
                'is_open': True,
                'status': 'OPEN',
                'hours': '9:30 AM - 4:00 PM EST',
                'current_time': now.strftime('%Y-%m-%d %H:%M:%S EST')
            }
        else:
            return {
                'is_open': False,
                'status': 'CLOSED',
                'next_open': 'Tomorrow 9:30 AM EST',
                'current_time': now.strftime('%Y-%m-%d %H:%M:%S EST')
            }