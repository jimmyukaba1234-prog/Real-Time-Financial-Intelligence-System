import os
from dotenv import load_dotenv

load_dotenv()

# Google Drive Configuration
GDRIVE_CREDENTIALS = os.getenv('GDRIVE_CREDENTIALS_PATH')
GDRIVE_FOLDER_ID = os.getenv('GDRIVE_FOLDER_ID')

# Email Configuration
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
HR_EMAILS = os.getenv('HR_EMAILS', '').split(',')

# Database Configuration
DB_PATH = 'financial_data.db'
RAW_DATA_PATH = 'data/raw/'
CLEAN_DATA_PATH = 'data/clean/'

# Scraping Configuration
SCRAPE_INTERVAL = 7  # days
FINANCIAL_SOURCES = {
    'yahoo_finance': 'https://finance.yahoo.com/',
    'marketwatch': 'https://www.marketwatch.com/'
}