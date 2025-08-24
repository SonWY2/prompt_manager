import os
import sys
import subprocess
from pathlib import Path

"""
Launch the Python backend (FastAPI/uvicorn) used by this project.
"""

if __name__ == '__main__':
    root_dir = Path(__file__).resolve().parent.parent
    backend_main_py = root_dir / 'src' / 'backend' / 'main.py'

    if not backend_main_py.exists():
        print(f"[run_backend.py] ERROR: Backend entry not found: {backend_main_py}")
        sys.exit(1)

    # Choose proper python command on Windows vs others
    python_cmd = 'python.exe' if sys.platform == 'win32' else 'python'

    env = os.environ.copy()
    # Respect SERVER_PORT if already set; default to 3000
    server_port = env.get('SERVER_PORT', '3000')

    print(f"[run_backend.py] Starting Python backend on port {server_port} → {backend_main_py}")
    try:
        # Inherit stdio so logs stream to this console
        proc = subprocess.Popen([
            python_cmd,
            "-m",
            "uvicorn",
            "src.backend.main:app",
            "--host", "0.0.0.0",
            "--port", server_port
        ], cwd=root_dir, env=env)
        proc.wait()
        sys.exit(proc.returncode or 0)
    except FileNotFoundError:
        print("[run_backend.py] ERROR: Python/Uvicorn is not installed or not on PATH.")
        sys.exit(1)
