#!/usr/bin/env python3
"""Prompt Compiler 1-Command Universal Launcher.
Works on Windows, macOS, and Linux.
"""

import sys
import subprocess
import time
import urllib.request
import os

def check_dependencies():
    print("[1/3] Checking dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"])
    except Exception as e:
        print(f"[WARN] Dependency check note: {e}")

def check_backend_running():
    print("[2/3] Checking backend engine...")
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=1) as resp:
            if resp.status == 200:
                print("✓ Backend engine already running on http://127.0.0.1:8000")
                return True
    except Exception:
        pass

    print("Launching background API server...")
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "prompt_optimizer.web.app:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)
    return True

def launch_desktop():
    print("[3/3] Launching Floating Spotlight Box [Win + O]...")
    print("=" * 60)
    print(" ⚡ PROMPT COMPILER IS LIVE!")
    print(" • Press [Win + O] or [Alt + O] anytime to pop up!")
    print(" • Web Dashboard: http://localhost:8000")
    print(" • Spotlight Web: http://localhost:8000/spotlight.html")
    print("=" * 60)
    try:
        import prompt_optimizer.quick_box.desktop_app as app
        app.launch()
    except Exception as e:
        print(f"GUI notice: {e}")
        print("Web server is running at http://localhost:8000/spotlight.html")

if __name__ == "__main__":
    check_dependencies()
    check_backend_running()
    launch_desktop()
