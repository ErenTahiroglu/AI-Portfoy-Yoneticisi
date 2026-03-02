import threading
import time
import webbrowser
import sys
import os

# Add the 'src' directory to Python's import path so main.py and other modules can be found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from main import app as fastapi_app

import traceback

def run_server():
    """Run the FastAPI server locally."""
    try:
        # Pass the app as an import string or import instance. Uvicorn supports both.
        uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="error")
    except Exception as e:
        print(f"CRITICAL ERROR IN UVICORN SERVER THREAD: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    print("Starting AI Islamic Portfolio Manager API Background Daemon...")
    
    # Start the FastAPI server daemon thread
    api_thread = threading.Thread(target=run_server, daemon=True)
    api_thread.start()
    
    import urllib.request
    import urllib.error
    
    # Wait until the server is responsive (up to 30 seconds)
    print("Waiting for server to start...")
    for _ in range(30):
        try:
            # We hit the root endpoint that returns {"status": "ok"}
            req = urllib.request.Request("http://127.0.0.1:8000/", method="GET")
            with urllib.request.urlopen(req, timeout=1) as response:
                if response.status == 200:
                    break
        except Exception:
            time.sleep(1)
    
    url = "http://127.0.0.1:8000/ui"
    print(f"Opening browser at: {url}")
    
    # Open the UI in the user's default browser!
    webbrowser.open(url)
    
    # Keep the console / process alive as long as necessary
    print("Press CTRL+C or close this window to stop the server.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        sys.exit(0)
