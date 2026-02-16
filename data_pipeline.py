import pandas as pd
import numpy as np
from datetime import datetime
import sqlite3
from typing import Dict, List
import os
from config import RAW_DATA_PATH, CLEAN_DATA_PATH, DB_PATH

class DataPipeline:
    def __init__(self):
        self.raw_path = RAW_DATA_PATH
        self.clean_path = CLEAN_DATA_PATH
        self.db_path = DB_PATH
        
        # Create directories if they don't exist
        os.makedirs(self.raw_path, exist_ok=True)
        os.makedirs(self.clean_path, exist_ok=True)
    
    def extract_from_gdrive(self, gdrive_handler):
        """Extract data from Google Drive"""
        files = gdrive_handler.list_files()
        
        for file in files:
            if file['name'].endswith('.csv'):
                dest_path = os.path.join(self.raw_path, file['name'])
                gdrive_handler.download_file(file['id'], dest_path)
                print(f"Downloaded: {file['name']}")
    
    def transform_data(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """Clean and transform financial data"""
        
        # Make a copy
        df_clean = df.copy()
        
        # Handle missing values
        if 'Close' in df_clean.columns:
            df_clean['Close'] = df_clean['Close'].fillna(method='ffill')
        
        # Calculate returns
        if 'Close' in df_clean.columns:
            df_clean['Daily_Return'] = df_clean['Close'].pct_change()
            df_clean['Cumulative_Return'] = (1 + df_clean['Daily_Return']).cumprod() - 1
        
        # Add technical indicators
        if 'Close' in df_clean.columns:
            df_clean['SMA_20'] = df_clean['Close'].rolling(window=20).mean()
            df_clean['SMA_50'] = df_clean['Close'].rolling(window=50).mean()
            
            # RSI
            delta = df_clean['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df_clean['RSI'] = 100 - (100 / (1 + rs))
        
        # Add metadata
        df_clean['Ticker'] = ticker
        df_clean['Processing_Date'] = datetime.now()
        
        # Reset index for date handling
        if 'Date' in df_clean.columns:
            df_clean['Date'] = pd.to_datetime(df_clean['Date'])
        elif df_clean.index.name == 'Date':
            df_clean = df_clean.reset_index()
            df_clean['Date'] = pd.to_datetime(df_clean['Date'])
        
        # Remove any remaining NaN
        df_clean = df_clean.dropna()
        
        return df_clean
    
    def load_to_database(self, df: pd.DataFrame, table_name: str):
        """Load data to SQLite database"""
        conn = sqlite3.connect(self.db_path)
        
        df.to_sql(table_name, conn, if_exists='append', index=False)
        
        conn.close()
    
    def process_all_files(self):
        """Process all raw data files"""
        processed_files = []
        
        for file in os.listdir(self.raw_path):
            if file.endswith('.csv') and 'historical' in file:
                try:
                    # Extract ticker from filename
                    ticker = file.split('_')[0]
                    
                    # Read CSV
                    file_path = os.path.join(self.raw_path, file)
                    df = pd.read_csv(file_path)
                    
                    # Transform
                    df_clean = self.transform_data(df, ticker)
                    
                    # Save cleaned data
                    clean_filename = f"clean_{file}"
                    clean_path = os.path.join(self.clean_path, clean_filename)
                    df_clean.to_csv(clean_path, index=False)
                    
                    # Load to database
                    self.load_to_database(df_clean, 'stock_prices')
                    
                    processed_files.append(file)
                    
                    print(f"Processed: {file}")
                    
                except Exception as e:
                    print(f"Error processing {file}: {e}")
        
        return processed_files
    
    def run_pipeline(self, gdrive_handler):
        """Run complete ETL pipeline"""
        print("Starting ETL pipeline...")
        
        # Extract from Google Drive
        print("Step 1: Extracting from Google Drive...")
        self.extract_from_gdrive(gdrive_handler)
        
        # Transform and Load
        print("Step 2: Transforming data...")
        processed = self.process_all_files()
        
        # Upload cleaned data back to Google Drive
        print("Step 3: Uploading cleaned data to Google Drive...")
        for file in os.listdir(self.clean_path):
            if file.endswith('.csv'):
                file_path = os.path.join(self.clean_path, file)
                gdrive_handler.upload_file(file_path, file, 'text/csv')
        
        print(f"ETL pipeline completed. Processed {len(processed)} files.")
        return processed