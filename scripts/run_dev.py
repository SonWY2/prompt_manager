#!/usr/bin/env python
import sys
import os
import subprocess
import time
from pathlib import Path

# Get the project root directory (one level up from this script)
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"

def main():
    """Starts the backend and frontend servers."""
    # Python backend (FastAPI) listens here
    api_port = "3000"
    vite_port = "3030"

    # --- Setup Environment ---
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    # Vite dev proxy target for /api → backend
    env["VITE_API_URL"] = f"http://localhost:{api_port}"
    env["VITE_PORT"] = vite_port

    # --- Start Backend (Uvicorn via wrapper) ---
    backend_cmd = [
        sys.executable,
        str(ROOT_DIR / "scripts" / "run_backend.py")
    ]
    print(f"[run_dev.py] Starting backend via wrapper: {' '.join(backend_cmd)}")
    backend_proc = subprocess.Popen(backend_cmd, cwd=ROOT_DIR, env=env)

    # --- Start Frontend (Vite) ---
    # Find npm
    npm_cmd_base = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_cmd = [npm_cmd_base, "run", "dev"]
    print(f"[run_dev.py] Starting frontend: {' '.join(frontend_cmd)}")
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=ROOT_DIR, env=env, shell=True)

    print("\nBackend and Frontend servers are starting.")
    print(f"Frontend running at: http://localhost:{vite_port}")
    print(f"Backend running at:  http://localhost:{api_port}")
    print("\nPress CTRL+C to stop both servers.")

    try:
        # Wait for processes to complete
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\n[run_dev.py] Shutting down servers...")
    finally:
        backend_proc.terminate()
        frontend_proc.terminate()
        backend_proc.wait()
        frontend_proc.wait()
        print("[run_dev.py] Servers stopped.")

if __name__ == "__main__":
    main()
