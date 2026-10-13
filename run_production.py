#!/usr/bin/env python3
"""
MediLogix - Production Runner
A foolproof script to setup, verify, and run MediLogix in production or development mode.

Usage:
    python run_production.py [run|setup|test|status]
    (Running without arguments presents an interactive menu)
"""
import os
import sys
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

WIN = sys.platform.startswith("win")
VPY = ROOT / "venv" / ("Scripts/python.exe" if WIN else "bin/python")
SCHEMA_FILE = ROOT / "medilogix_db.sql"


def print_banner():
    print("=" * 60)
    print("           MEDILOGIX - PRODUCTION RUNNER")
    print("=" * 60)


def ensure_environment():
    """Ensure Python 3.10+, venv, and dependencies exist."""
    if sys.version_info < (3, 10):
        print(f"[ERROR] Python 3.10+ is required. Found: {sys.version}")
        sys.exit(1)

    # Check venv
    if not VPY.exists():
        print("[INFO] Virtual environment (venv) not found. Creating...")
        import venv
        venv.create(ROOT / "venv", with_pip=True)
        print("[INFO] Installing dependencies...")
        subprocess.check_call([str(VPY), "-m", "pip", "install", "-q", "-r", str(ROOT / "requirements.txt")])
        print("[OK] Virtual environment created and dependencies installed.")
    else:
        print(f"[OK] Virtual environment found: {VPY}")


def run_tests():
    print("\n[INFO] Running test suite...")
    res = subprocess.run([str(VPY), "-m", "pytest", "-v"])
    sys.exit(res.returncode)


def run_setup():
    print("\n[INFO] Applying database schema...")
    subprocess.run([str(VPY), str(ROOT / "apply_schema.py")])


def run_production(open_browser=True):
    print("\n[INFO] Starting MediLogix Application...")
    cmd = [str(VPY), str(ROOT / "run.py")]
    
    if open_browser:
        import webbrowser
        import threading
        def open_url():
            time.sleep(1.5)
            webbrowser.open("http://127.0.0.1:5000")
        threading.Thread(target=open_url, daemon=True).start()

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[INFO] MediLogix stopped.")


def check_status():
    print("\n[INFO] System Status Check:")
    print(f"  - Root Directory: {ROOT}")
    print(f"  - Python Executable: {VPY} (exists: {VPY.exists()})")
    print(f"  - Schema File: {SCHEMA_FILE} (exists: {SCHEMA_FILE.exists()})")
    
    # Check MySQL connection if possible
    try:
        subprocess.run([str(VPY), "-c", "import pymysql, os; pymysql.connect(host=os.environ.get('MYSQL_HOST','localhost'), user=os.environ.get('MYSQL_USER','root'), password=os.environ.get('MYSQL_PASSWORD',''), database=os.environ.get('MYSQL_DB','medilogix_db'))"], check=True)
        print("  - Database Connection: [OK]")
    except Exception as e:
        print(f"  - Database Connection: [ERROR/WARNING] ({e})")


def main():
    print_banner()
    ensure_environment()

    action = sys.argv[1].lower() if len(sys.argv) > 1 else ""

    if not action:
        print("\nSelect Mode:")
        print("  1. Run Application (Start Flask server)")
        print("  2. Setup Database Schema (Apply medilogix_db.sql)")
        print("  3. Run Unit Tests (pytest)")
        print("  4. Check Status")
        print("  5. Exit")
        choice = input("\nEnter choice [1-5] (default 1): ").strip() or "1"
        if choice == "1":
            run_production(open_browser=True)
        elif choice == "2":
            run_setup()
        elif choice == "3":
            run_tests()
        elif choice == "4":
            check_status()
        else:
            print("Exiting.")
    else:
        if action == "run":
            run_production(open_browser="--no-open" not in sys.argv)
        elif action == "setup":
            run_setup()
        elif action == "test":
            run_tests()
        elif action == "status":
            check_status()
        else:
            print(f"Unknown action: {action}")
            print("Usage: python run_production.py [run|setup|test|status]")


if __name__ == "__main__":
    main()
