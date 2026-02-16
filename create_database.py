#!/usr/bin/env python3
"""Create a fresh database with sample data"""
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

print("🔧 Creating fresh database...")

# Remove old database if exists
if os.path.exists('financial_data.db'):
    os.remove('financial_data.db')
    print("🗑️  Removed old database")

# Create new database
conn = sqlite3.connect('financial_data.db')
cursor = conn.cursor()

# Create stock_prices table
cursor.execute('''
CREATE TABLE IF NOT EXISTS stock_prices (
    Date TEXT,
    Open REAL,
    High REAL,
    Low REAL,
    Close REAL,
    Volume INTEGER,
    Daily_Return REAL,
    Cumulative_Return REAL,
    SMA_20 REAL,
    SMA_50 REAL,
    RSI REAL,
    Ticker TEXT,
    Processing_Date TEXT,
    PRIMARY KEY (Date, Ticker)
)
''')

# Create predictions table
cursor.execute('''
CREATE TABLE IF NOT EXISTS predictions (
    Prediction_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Ticker TEXT,
    Prediction_Date TEXT,
    Predicted_Close REAL,
    Confidence_Interval_Lower REAL,
    Confidence_Interval_Upper REAL,
    Model_Used TEXT,
    Created_At TEXT
)
''')

print("✅ Database tables created")

# Generate sample data for popular stocks
tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META']
start_date = datetime.now() - timedelta(days=90)

for ticker in tickers:
    print(f"📊 Generating data for {ticker}...")
    
    # Generate business days
    dates = pd.date_range(start=start_date, end=datetime.now(), freq='B')
    n_days = len(dates)
    
    # Realistic base prices
    base_prices = {
        'AAPL': 180, 'GOOGL': 140, 'MSFT': 380,
        'AMZN': 170, 'TSLA': 240, 'META': 490
    }
    base = base_prices.get(ticker, 100)
    
    # Generate realistic price movements
    np.random.seed(hash(ticker) % 10000)  # Consistent random
    
    # Random walk with drift
    returns = np.random.normal(0.0005, 0.02, n_days)
    prices = base * np.exp(np.cumsum(returns))
    
    # Create DataFrame
    df = pd.DataFrame({
        'Date': dates.strftime('%Y-%m-%d'),
        'Open': prices * (1 - np.random.uniform(0, 0.01, n_days)),
        'High': prices * (1 + np.random.uniform(0, 0.02, n_days)),
        'Low': prices * (1 - np.random.uniform(0, 0.02, n_days)),
        'Close': prices,
        'Volume': np.random.randint(1000000, 50000000, n_days),
        'Ticker': ticker,
        'Processing_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    # Calculate returns
    df['Daily_Return'] = df['Close'].pct_change()
    df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod() - 1
    
    # Calculate technical indicators
    df['SMA_20'] = df['Close'].rolling(window=20, min_periods=1).mean()
    df['SMA_50'] = df['Close'].rolling(window=50, min_periods=1).mean()
    
    # Calculate RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Fill NaN values
    df = df.fillna(method='bfill').fillna(method='ffill').fillna(0)
    
    # Insert into database
    df.to_sql('stock_prices', conn, if_exists='append', index=False)
    print(f"  ✅ Added {len(df)} records for {ticker}")

conn.commit()

# Verify data
print("\n📊 Verifying database...")
ticker_count = pd.read_sql_query("SELECT COUNT(DISTINCT Ticker) as count FROM stock_prices", conn)
row_count = pd.read_sql_query("SELECT COUNT(*) as count FROM stock_prices", conn)
print(f"✅ Database contains:")
print(f"  • {ticker_count['count'].iloc[0]} tickers")
print(f"  • {row_count['count'].iloc[0]} total records")

# Show sample data
sample = pd.read_sql_query("SELECT * FROM stock_prices LIMIT 3", conn)
print(f"\n📋 Sample data:")
print(sample[['Date', 'Ticker', 'Close', 'Daily_Return']])

conn.close()

print("\n🎉 Database creation complete!")
print("You can now run: streamlit run app.py")