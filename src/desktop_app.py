import threading
import time
import webbrowser
import sys
import os
import socket
import traceback

# Add the 'src' directory to Python's import path so main.py and other modules can be found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from main import app as fastapi_app


def find_free_port(start=8000, end=8020):
    """Try ports from start to end and return the first available one."""
    for port in range(start, end):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    return None


def run_server(port):
    """Run the FastAPI server locally on the given port."""
    try:
        uvicorn.run(fastapi_app, host="127.0.0.1", port=port, log_level="info")
    except Exception as e:
        print(f"CRITICAL ERROR IN UVICORN SERVER THREAD: {e}")
        traceback.print_exc()


if __name__ == '__main__':
    print("Starting AI Islamic Portfolio Manager API Background Daemon...")

    # Find a free port (try 8000-8019)
    port = find_free_port()
    if port is None:
        print("[HATA] 8000-8019 arasi tum portlar mesgul! Baska programlari kapatip tekrar deneyin.")
        input("Cikmak icin Enter'a basin...")
        sys.exit(1)

    if port != 8000:
        print(f"[BILGI] Port 8000 mesgul, port {port} kullaniliyor.")

    # Start the FastAPI server daemon thread
    api_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    api_thread.start()

    import urllib.request
    import urllib.error

    # Wait until the server is responsive (up to 30 seconds)
    print("Waiting for server to start...")
    for _ in range(30):
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/", method="GET")
            with urllib.request.urlopen(req, timeout=1) as response:
                if response.status == 200:
                    break
        except Exception:
            time.sleep(1)

    url = f"http://127.0.0.1:{port}/ui"
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
