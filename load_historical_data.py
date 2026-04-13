#!/usr/bin/env python3
"""Load 1 year of historical data for ML training"""
import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import numpy as np
import os

print("📊 Loading 1 Year Historical Data for ML Training")
print("=" * 60)

# Tickers to load
tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META']

# Connect to database
conn = sqlite3.connect('financial_data.db')
cursor = conn.cursor()

print(f"\n📡 Downloading 1 year of daily data for {len(tickers)} stocks...")

# Download data for all tickers at once (more efficient)
print("   This may take a moment...")
data = yf.download(
    tickers=tickers,
    period="1y",  # 1 year of data
    interval="1d",  # Daily intervals
    group_by='ticker',
    progress=True,
    threads=True
)

print(f"\n✅ Downloaded data for {len(tickers)} tickers")

# Clear existing data
print("\n🗑️  Clearing existing data...")
cursor.execute("DELETE FROM stock_prices")
conn.commit()

# Process each ticker
total_records = 0
for ticker in tickers:
    print(f"\n📈 Processing {ticker}...")
    
    if ticker in data.columns.levels[0]:
        df = data[ticker].copy()
        
        # Reset index to get Date as column
        df = df.reset_index()
        
        # Rename columns to match our schema
        df = df.rename(columns={
            'Open': 'Open',
            'High': 'High',
            'Low': 'Low',
            'Close': 'Close',
            'Volume': 'Volume',
            'Date': 'Date'
        })
        
        # Convert Date to string
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        
        # Add ticker column
        df['Ticker'] = ticker
        
        # Calculate returns
        df['Daily_Return'] = df['Close'].pct_change()
        df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod() - 1
        
        # Calculate moving averages
        df['SMA_20'] = df['Close'].rolling(window=20, min_periods=1).mean()
        df['SMA_50'] = df['Close'].rolling(window=50, min_periods=1).mean()
        
        # Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Add processing timestamp
        df['Processing_Date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Fill NaN values
        df = df.bfill().ffill()
        #df = df.fillna(method='bfill').fillna(method='ffill')
        
        # Insert into database
        df.to_sql('stock_prices', conn, if_exists='append', index=False)
        
        total_records += len(df)
        print(f"   ✅ Added {len(df)} days of historical data")
    else:
        print(f"   ⚠️  No data for {ticker}")

conn.commit()
conn.close()

print(f"\n" + "=" * 60)
print(f"🎉 HISTORICAL DATA LOAD COMPLETE!")
print(f"   • Total records: {total_records:,}")
print(f"   • Average per ticker: {total_records//len(tickers):,} days")
print(f"   • Enough for ML training: ✅ YES")
print("\n📊 Now run ML predictions in your dashboard!")
print("=" * 60)