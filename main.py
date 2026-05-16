"""
main.py - Hybrid Shield Entry Point
=====================================
Launches the FastAPI web server and opens the dashboard in your browser.
"""

import webbrowser
import threading
import uvicorn

def open_browser():
    """Opens the dashboard in the default browser after a short delay."""
    import time
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════╗")
    print("║   HYBRID SHIELD — Secure Encryption System      ║")
    print("║   Opening dashboard at http://127.0.0.1:8000     ║")
    print("║   Press Ctrl+C to stop the server                ║")
    print("╚══════════════════════════════════════════════════╝")
    
    # Open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start the FastAPI server
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
