import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from config import DB_PATH

class DatabaseHandler:
    def __init__(self):
        self.db_path = DB_PATH
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create stock prices table
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
        
        # Create metrics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_metrics (
            Metric_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Ticker TEXT,
            Metric_Date TEXT,
            Metric_Name TEXT,
            Metric_Value REAL,
            Created_At TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame"""
        conn = sqlite3.connect(self.db_path)
        
        if params:
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    
    def get_stock_data(self, ticker: str, start_date: str = None, end_date: str = None):
        """Get stock data for specific ticker and date range"""
        query = "SELECT * FROM stock_prices WHERE Ticker = ?"
        params = [ticker]
        
        if start_date:
            query += " AND Date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND Date <= ?"
            params.append(end_date)
        
        query += " ORDER BY Date DESC"
        
        return self.execute_query(query, tuple(params))
    
    def get_latest_prices(self):
        """Get latest prices for all tickers"""
        query = '''
        SELECT sp1.* 
        FROM stock_prices sp1
        INNER JOIN (
            SELECT Ticker, MAX(Date) as LatestDate
            FROM stock_prices
            GROUP BY Ticker
        ) sp2 ON sp1.Ticker = sp2.Ticker AND sp1.Date = sp2.LatestDate
        ORDER BY sp1.Ticker
        '''
        
        return self.execute_query(query)
    
    def calculate_metrics(self, ticker: str):
        """Calculate financial metrics for a ticker"""
        query = '''
        SELECT 
            Ticker,
            AVG(Daily_Return) as Avg_Daily_Return,
            STDDEV(Daily_Return) as Daily_Volatility,
            MAX(High) as Period_High,
            MIN(Low) as Period_Low,
            AVG(Volume) as Avg_Volume,
            COUNT(*) as Data_Points
        FROM stock_prices
        WHERE Ticker = ?
        GROUP BY Ticker
        '''
        
        return self.execute_query(query, (ticker,))
    
    def save_prediction(self, prediction_data: dict):
        """Save prediction to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO predictions 
        (Ticker, Prediction_Date, Predicted_Close, 
         Confidence_Interval_Lower, Confidence_Interval_Upper, 
         Model_Used, Created_At)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            prediction_data['ticker'],
            prediction_data['prediction_date'],
            prediction_data['predicted_close'],
            prediction_data.get('ci_lower'),
            prediction_data.get('ci_upper'),
            prediction_data.get('model_used', 'Random Forest'),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()