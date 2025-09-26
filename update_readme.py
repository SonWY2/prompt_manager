import pathlib, re
path = pathlib.Path('README.md')
text = path.read_text(encoding='utf-8')
old_backend = '### 백엔드\n- **Node.js**: 서버 환경\n- **Express**: 웹 프레임워크\n- **JSON 파일 스토리지**: 데이터 저장을 위한 간단한 파일 기반 스토리지 시스템\n'
new_backend = '### 백엔드\n- **Python (FastAPI)**: 경량 REST API 서버\n- **Uvicorn**: ASGI 서버 러너\n- **JSON 파일 스토리지**: 데이터 저장을 위한 간단한 파일 기반 스토리지 시스템\n'
if old_backend not in text:
    raise SystemExit('Backend section not found')
text = text.replace(old_backend, new_backend)
old_structure = """```
prompt_manager/\n├── data/                      # 데이터 스토리지\n│   └── prompt-data.json       # 프롬프트 데이터 JSON 파일\n├── src/\n│   ├── backend/               # 백엔드 코드\n│   │   └── server.js          # Express 서버 \n│   └── frontend/              # 프론트엔드 코드\n│       ├── components/        # React 컴포넌트\n│       │   ├── common/        # 공통 UI 컴포넌트\n│       │   ├── layout/        # 레이아웃 관련 컴포넌트\n│       │   ├── prompt/        # 프롬프트 관련 컴포넌트\n│       │   ├── result/        # 결과 관련 컴포넌트\n│       │   └── task/          # 태스크 관련 컴포넌트\n│       ├── App.jsx            # 메인 React 앱 컴포넌트\n│       ├── App.css            # 스타일시트\n│       └── store.jsx          # Zustand 상태 관리\n└── package.json               # 프로젝트 의존성 및 스크립트\n```"""
new_structure = """```
prompt_manager/\n├── data/                      # 데이터 스토리지\n│   └── prompt-data.json       # 프롬프트 데이터 JSON 파일\n├── scripts/                   # 개발 편의 스크립트\n│   ├── run_backend.py         # FastAPI 백엔드 실행 래퍼\n│   └── run_dev.py             # 백엔드/프론트 동시 실행\n├── src/\n│   ├── backend/               # 백엔드 코드\n│   │   └── main.py            # FastAPI 엔트리 포인트\n│   └── frontend/              # 프론트엔드 코드\n│       ├── components/        # React 컴포넌트\n│       │   ├── common/        # 공통 UI 컴포넌트\n│       │   ├── layout/        # 레이아웃 관련 컴포넌트\n│       │   ├── prompt/        # 프롬프트 관련 컴포넌트\n│       │   ├── result/        # 결과 관련 컴포넌트\n│       │   └── task/          # 태스크 관련 컴포넌트\n│       ├── App.jsx            # 메인 React 앱 컴포넌트\n│       ├── App.css            # 스타일시트\n│       └── store.jsx          # Zustand 상태 관리\n├── package.json               # 프론트엔드 의존성 및 스크립트\n└── requirements.txt           # 백엔드 Python 의존성\n```"""
if old_structure not in text:
    raise SystemExit('Structure block not found')
text = text.replace(old_structure, new_structure)
pattern = re.compile(r'### 전제 조건.*?### 프로덕션 빌드', re.S)
new_setup = """### 전제 조건\n- Python 3.10 이상\n- Node.js (v18 이상) 및 npm\n\n### 설치 단계\n\n1. 레포지토리 클론\n   ```bash\n   git clone <repository-url>\n   cd prompt-manager\n   ```\n\n2. (선택) 파이썬 가상환경 생성\n   ```bash\n   python -m venv .venv\n   .venv\\Scripts\\activate  # Windows\n   # 또는\n   source .venv/bin/activate   # macOS/Linux\n   ```\n\n3. 백엔드 의존성 설치\n   ```bash\n   pip install -r requirements.txt\n   ```\n\n4. 프론트엔드 의존성 설치\n   ```bash\n   npm install\n   ```\n\n### 개발 서버 실행\n\n- 백엔드 (FastAPI):\n  ```bash\n  python -m uvicorn src.backend.main:app --host 127.0.0.1 --port 3000 --reload\n  ```\n\n- 프론트엔드 (Vite):\n  ```bash\n  npm run dev\n  ```\n\n- 두 서비스를 동시에 실행\n  - Windows: `scripts\\run_dev.bat`\n  - 크로스 플랫폼: `python scripts/run_dev.py`\n\n브라우저에서 `http://localhost:3030` (기본값)으로 접속하며, 프론트엔드는 `/api` 요청을 백엔드로 프록시합니다.\n\n### 프로덕션 빌드\n"""
if not pattern.search(text):
    raise SystemExit('Setup section not found')
text = pattern.sub(new_setup, text)
path.write_text(text, encoding='utf-8')
