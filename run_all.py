# run_all.py
"""
Script to start both the FastAPI backend and the Streamlit dashboard.
- Starts the API server in a background process
- Starts the Streamlit dashboard in the foreground
"""
import subprocess
import sys
import os
import time

# Ensure working directory is project root
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Paths
API_PATH = os.path.join("api", "api_server.py")
DASH_PATH = os.path.join("frontend", "streamlit_dashboard.py")

# Check if API and dashboard files exist
if not os.path.exists(API_PATH):
    raise FileNotFoundError(f"API server not found at {API_PATH}")
if not os.path.exists(DASH_PATH):
    raise FileNotFoundError(f"Streamlit dashboard not found at {DASH_PATH}")

# Start API server (background) in the correct working directory
api_proc = subprocess.Popen([
    sys.executable, "-m", "uvicorn", "api.api_server:app", "--host", "0.0.0.0", "--port", "8000"
], cwd=os.getcwd())
print("[INFO] API server started on http://localhost:8000 (PID: %d)" % api_proc.pid)

# Wait a bit to ensure API is up
time.sleep(2)

try:
    # Start Streamlit dashboard (foreground)
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", os.path.abspath(DASH_PATH)
    ])
finally:
    print("[INFO] Shutting down API server...")
    api_proc.terminate()
    api_proc.wait()
    print("[INFO] All processes stopped.")
