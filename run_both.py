import subprocess
import threading
import time

def run_streamlit():
    subprocess.run(["streamlit", "run", "app.py"])

def run_dash():
    subprocess.run(["python", "dashboard.py"])

if __name__ == "__main__":
    print("Starting both dashboards...")
    print("Streamlit: http://localhost:8501")
    print("Dash: http://localhost:8050")
    
    t1 = threading.Thread(target=run_streamlit)
    t2 = threading.Thread(target=run_dash)
    
    t1.start()
    time.sleep(2)  # Give Streamlit time to start
    t2.start()
    
    t1.join()
    t2.join()