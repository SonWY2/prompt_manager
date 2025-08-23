import os
import sys
import subprocess
from pathlib import Path

"""
Launch the Node.js backend (Express) used by this project.

Previously this script attempted to run a FastAPI/uvicorn app, but the
current backend lives at `src/backend/server.js`. This wrapper keeps the
`scripts/run_dev.py` interface stable while starting the correct server.
"""

if __name__ == '__main__':
    root_dir = Path(__file__).resolve().parent.parent
    server_js = root_dir / 'src' / 'backend' / 'server.js'

    if not server_js.exists():
        print(f"[run_backend.py] ERROR: Backend entry not found: {server_js}")
        sys.exit(1)

    # Choose proper node command on Windows vs others
    node_cmd = 'node.exe' if sys.platform == 'win32' else 'node'

    env = os.environ.copy()
    # Respect SERVER_PORT if already set; default to 3000 in server.js
    server_port = env.get('SERVER_PORT', '3000')

    print(f"[run_backend.py] Starting Node backend on port {server_port} → {server_js}")
    try:
        # Inherit stdio so logs stream to this console
        proc = subprocess.Popen([node_cmd, str(server_js)], cwd=root_dir, env=env)
        proc.wait()
        sys.exit(proc.returncode or 0)
    except FileNotFoundError:
        print("[run_backend.py] ERROR: Node.js is not installed or not on PATH (node command not found).")
        sys.exit(1)
