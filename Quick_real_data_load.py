# Quick real data load
import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

print('📥 Downloading real stock data...')

# List of popular stocks
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM']

# Download 1 year of daily data
data = yf.download(tickers, period='1y', interval='1d', group_by='ticker')

# Connect to database
conn = sqlite3.connect('financial_data.db')
cursor = conn.cursor()

# Clear existing data
cursor.execute('DELETE FROM stock_prices')
conn.commit()

# Process each ticker
for ticker in tickers:
    if ticker in data.columns.levels[0]:
        df = data[ticker].copy()
        df['Ticker'] = ticker
        df['Date'] = df.index.strftime('%Y-%m-%d')
        
        # Reset index
        df = df.reset_index(drop=True)
        
        # Rename columns
        df = df.rename(columns={
            'Open': 'Open',
            'High': 'High',
            'Low': 'Low', 
            'Close': 'Close',
            'Volume': 'Volume',
            'Adj Close': 'Adj_Close'
        })
        
        # Calculate returns
        df['Daily_Return'] = df['Close'].pct_change()
        df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod() - 1
        
        # Calculate SMA
        df['SMA_20'] = df['Close'].rolling(20).mean()
        df['SMA_50'] = df['Close'].rolling(50).mean()
        
        # Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        df['Processing_Date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Fill NaN
        df = df.fillna(method='bfill').fillna(method='ffill')
        
        # Insert into database
        cols_to_keep = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume',
                       'Daily_Return', 'Cumulative_Return', 'SMA_20', 
                       'SMA_50', 'RSI', 'Ticker', 'Processing_Date']
        
        df[cols_to_keep].to_sql('stock_prices', conn, if_exists='append', index=False)
        
        print(f'✅ {ticker}: {len(df)} days loaded')

conn.commit()
conn.close()

print(f'🎉 Loaded {len(tickers)} stocks with real market data!')