# launch_all.py
import subprocess
import threading
import time
import webbrowser
import os
import sys

def kill_port(port):
    """Kill process on specified port"""
    try:
        if os.name == 'posix':  # macOS/Linux
            os.system(f'lsof -ti:{port} | xargs kill -9 2>/dev/null')
        else:  # Windows
            os.system(f'netstat -ano | findstr :{port} | findstr LISTENING')
        time.sleep(1)
    except:
        pass

def run_streamlit():
    """Run Streamlit dashboard on port 8502"""
    kill_port(8501)  # Clean up port 8501 first
    kill_port(8502)  # Clean up port 8502
    print("🚀 Starting Streamlit on port 8502...")
    subprocess.run(["streamlit", "run", "app.py", "--server.port=8502", "--server.headless=true"])

def run_dash():
    """Run Dash dashboard"""
    kill_port(8050)  # Clean up port 8050
    print("🚀 Starting Dash on port 8050...")
    subprocess.run(["python", "dashboard.py"])

def open_browsers():
    """Open both dashboards in browser"""
    time.sleep(5)  # Wait for servers to start
    webbrowser.open("http://localhost:8502")  # Streamlit on 8502
    time.sleep(2)
    webbrowser.open("http://localhost:8050")  # Dash

if __name__ == "__main__":
    print("🚀 Launching Financial Dashboards...")
    print("📊 Streamlit (Simple): http://localhost:8502")
    print("📈 Dash (Advanced): http://localhost:8050")
    
    # Clean up ports first
    kill_port(8501)
    kill_port(8502)
    kill_port(8050)
    
    print("⏳ Starting servers...")
    
    # Start both servers
    t1 = threading.Thread(target=run_dash)
    t2 = threading.Thread(target=run_streamlit)
    
    t1.start()
    time.sleep(2)
    t2.start()
    
    # Open browsers
    time.sleep(5)
    open_browsers()
    
    print("✅ Both dashboards are running!")
    print("Press Ctrl+C to stop all servers")
    
    try:
        t1.join()
        t2.join()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        kill_port(8502)
        kill_port(8050)