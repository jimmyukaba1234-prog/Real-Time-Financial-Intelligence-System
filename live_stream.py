#!/usr/bin/env python3
"""Continuous live data stream"""
import time
from datetime import datetime
from scraper import FinancialScraper
import json
import os

class LiveDataStream:
    def __init__(self, update_interval=30):  # seconds
        self.scraper = FinancialScraper()
        self.update_interval = update_interval
        os.makedirs('data/stream', exist_ok=True)
    
    def start_stream(self):
        """Start continuous data stream"""
        print("🌊 Starting live data stream...")
        print(f"📡 Streaming {len(self.scraper.tickers)} tickers")
        print(f"⏱️  Update interval: {self.update_interval} seconds")
        print("-" * 50)
        
        try:
            while True:
                timestamp = datetime.now()
                print(f"\n🕐 {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Get market status
                status = self.scraper.get_market_status()
                print(f"🏛️  Market: {status['status']}")
                
                # Get live data
                data = self.scraper.get_realtime_tickers_data()
                
                # Display updates
                for ticker, ticker_data in data.items():
                    if 'error' not in ticker_data:
                        price = ticker_data.get('close', 0)
                        volume = ticker_data.get('volume', 0)
                        print(f"   {ticker}: ${price:.2f} | 📊 {volume:,}")
                
                # Save to file
                self.save_snapshot(data, timestamp)
                
                # Wait for next update
                time.sleep(self.update_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Live stream stopped by user")
    
    def save_snapshot(self, data, timestamp):
        """Save data snapshot"""
        snapshot = {
            'timestamp': timestamp.isoformat(),
            'data': data
        }
        
        filename = f"data/stream/snapshot_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(snapshot, f, indent=2)
        
        # Keep only last 100 files
        self.cleanup_old_files('data/stream', 100)
    
    def cleanup_old_files(self, directory, keep_count=100):
        """Keep only recent files"""
        files = [os.path.join(directory, f) for f in os.listdir(directory) 
                if f.startswith('snapshot_') and f.endswith('.json')]
        files.sort(key=os.path.getmtime)
        
        if len(files) > keep_count:
            for file_to_delete in files[:-keep_count]:
                os.remove(file_to_delete)

if __name__ == "__main__":
    stream = LiveDataStream(update_interval=30)  # Update every 30 seconds
    stream.start_stream()