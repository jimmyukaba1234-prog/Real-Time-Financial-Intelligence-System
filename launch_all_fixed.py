# launch_all.py
import subprocess
import threading
import time
import webbrowser
import os
import sys

def initialize_database():
    """Initialize database before starting dashboards"""
    print("🔧 Checking database...")
    
    DB_PATH = 'financial_data.db'
    
    # Check if database exists and has data
    if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 0:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM stock_prices")
            count = cursor.fetchone()[0]
            conn.close()
            if count > 0:
                print(f"✅ Database ready with {count} records")
                return True
        except:
            pass
    
    # Database needs initialization
    print("📊 Initializing database with sample data...")
    
    # Import initialization
    try:
        # Create sample data
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        import sqlite3
        
        # Create connection
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create table
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
        
        # Create sample data for 3 stocks
        tickers = ['AAPL', 'GOOGL', 'MSFT']
        start_date = datetime.now() - timedelta(days=60)
        
        for ticker in tickers:
            dates = []
            current_date = start_date
            while current_date <= datetime.now():
                if current_date.weekday() < 5:
                    dates.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
            
            # Generate realistic data
            np.random.seed(hash(ticker) % 10000)
            n_days = len(dates)
            
            base_prices = {'AAPL': 180, 'GOOGL': 140, 'MSFT': 380}
            base = base_prices.get(ticker, 100)
            
            prices = []
            current = base
            for i in range(n_days):
                change = np.random.normal(0.001, 0.015)
                current = current * (1 + change)
                prices.append(current)
            
            df = pd.DataFrame({
                'Date': dates,
                'Open': [p * 0.99 for p in prices],
                'High': [p * 1.02 for p in prices],
                'Low': [p * 0.98 for p in prices],
                'Close': prices,
                'Volume': np.random.randint(1000000, 50000000, n_days),
                'Ticker': ticker,
                'Processing_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            # Calculate indicators
            df['Daily_Return'] = df['Close'].pct_change()
            df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod() - 1
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            df = df.fillna(method='bfill').fillna(method='ffill')
            df.to_sql('stock_prices', conn, if_exists='append', index=False)
            print(f"  ✅ Added {ticker}")
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized with {len(tickers)} tickers")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

def run_streamlit():
    """Run Streamlit dashboard"""
    print("🚀 Starting Streamlit...")
    import sys

    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true"])
    #subprocess.run(["streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true"])

def run_dash():
    """Run Dash dashboard"""
    print("🚀 Starting Dash...")
    subprocess.run(["python", "dashboard.py"])

def open_browsers():
    """Open both dashboards in browser"""
    time.sleep(5)  # Wait longer for servers to start
    webbrowser.open("http://localhost:8501")  # Streamlit
    time.sleep(2)
    webbrowser.open("http://localhost:8050")  # Dash

if __name__ == "__main__":
    print("🚀 Launching Financial Dashboards...")
    print("📊 Streamlit (Simple): http://localhost:8501")
    print("📈 Dash (Advanced): http://localhost:8050")
    
    # Initialize database first
    if not initialize_database():
        print("❌ Failed to initialize database. Exiting.")
        sys.exit(1)
    
    print("⏳ Starting servers...")
    
    # Start both servers with delay
    t1 = threading.Thread(target=run_dash)  # Dash first (takes longer to fail)
    t2 = threading.Thread(target=run_streamlit)  # Then Streamlit
    
    t1.start()
    time.sleep(3)  # Give Dash time to start
    t2.start()
    
    # Open browsers after both start
    time.sleep(5)
    open_browsers()
    
    print("✅ Both dashboards should be running!")
    print("Press Ctrl+C to stop all servers")
    
    try:
        t1.join()
        t2.join()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")