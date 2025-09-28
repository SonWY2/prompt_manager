import os
import sys
import subprocess
from pathlib import Path

"""
Launch the Python backend (FastAPI/uvicorn) for SQLite-based Prompt Manager.
"""

if __name__ == '__main__':
    root_dir = Path(__file__).resolve().parent.parent
    backend_dir = root_dir / 'src' / 'backend'
    backend_main_py = backend_dir / 'main.py'

    if not backend_main_py.exists():
        print(f"[run_backend.py] ERROR: Backend entry not found: {backend_main_py}")
        sys.exit(1)

    # Choose proper python command on Windows vs others
    python_cmd = 'python.exe' if sys.platform == 'win32' else 'python'

    env = os.environ.copy()
    # SQLite 시스템은 기본적으로 8000 포트 사용
    server_port = env.get('SERVER_PORT', '8000')

    print(f"[run_backend.py] Starting SQLite-based Python backend on port {server_port}")
    print(f"[run_backend.py] Backend directory: {backend_dir}")
    print(f"[run_backend.py] Main file: {backend_main_py}")
    
    try:
        # src/backend 디렉토리에서 직접 실행하여 database.py 모듈 접근 가능하게 함
        proc = subprocess.Popen([
            python_cmd,
            "-m",
            "uvicorn",
            "main:app",  # src.backend.main이 아닌 main 직접 참조
            "--host", "0.0.0.0",
            "--port", server_port,
            "--reload"  # 개발 모드에서 자동 재시작
        ], cwd=backend_dir, env=env)  # backend 디렉토리에서 실행
        proc.wait()
        sys.exit(proc.returncode or 0)
    except FileNotFoundError:
        print("[run_backend.py] ERROR: Python/Uvicorn is not installed or not on PATH.")
        sys.exit(1)
