# Prompt Manager - PyQt GUI

LLM 프롬프트를 관리하고 테스트할 수 있는 네이티브 데스크톱 애플리케이션입니다. PyQt6 기반의 직관적인 GUI로 프롬프트 개발, 버전 관리, LLM 테스트를 한 곳에서 수행할 수 있습니다.

![Prompt Manager GUI](public/screenshot.png)

## 주요 기능

### 1. 📋 태스크 관리
- **태스크 생성/삭제**: 프롬프트를 태스크 단위로 그룹화하여 관리
- **즐겨찾기**: 자주 사용하는 태스크를 즐겨찾기로 고정
- **검색 기능**: 태스크명으로 빠르게 검색
- **태스크 이름 변경**: 태스크 선택 후 이름 수정 가능

### 2. ✏️ 프롬프트 편집
- **실시간 편집**: 프롬프트 내용을 즉시 편집하고 저장
- **템플릿 변수**: `{{변수명}}` 형식으로 동적 프롬프트 작성
- **System Prompt**: 시스템 프롬프트 별도 설정
- **버전 관리**: 프롬프트의 여러 버전 생성 및 관리
- **버전 설명**: 각 버전에 설명 추가 가능

### 3. 🔧 변수 관리
- **변수 자동 추출**: 프롬프트에서 `{{변수}}` 자동 인식
- **변수값 입력**: UI에서 직접 변수값 설정
- **실시간 미리보기**: 변수가 적용된 최종 프롬프트 확인

### 4. 🤖 LLM 통합
- **다중 엔드포인트**: 여러 LLM API 엔드포인트 등록 및 관리
- **엔드포인트 설정**:
  - 이름, 설명
  - Base URL (API 엔드포인트)
  - API Key
  - 기본 모델명
  - Context 크기
- **엔드포인트 테스트**: 연결 테스트 및 모델 목록 확인
- **Temperature 조절**: 0.0 ~ 2.0 범위에서 창의성 조절
- **실시간 호출**: 프롬프트를 LLM에 전송하고 결과 즉시 확인

### 5. 📊 결과 확인
- **응답 내용 표시**: LLM의 전체 응답 확인
- **결과 이력**: 이전 실행 결과 목록 확인
- **메타 정보**: 사용된 모델, Temperature, 타임스탬프 표시
- **프롬프트 재확인**: 실행 당시 사용된 정확한 프롬프트 확인

### 6. 🔄 버전 비교
- **나란히 비교**: 두 버전의 프롬프트 내용 비교
- **차이점 강조**: 변경된 부분 시각적으로 표시
- **결과 비교**: 각 버전의 LLM 응답 비교

### 7. 🎨 사용자 인터페이스
- **3단 레이아웃**: 
  - 왼쪽: 태스크 네비게이터
  - 중앙: 프롬프트 에디터
  - 오른쪽: 변수/결과 탭
- **분할 패널**: 패널 크기 자유롭게 조절
- **탭 구성**: 변수 편집기와 LLM 결과를 탭으로 전환
- **창 위치 저장**: 종료 시 창 크기/위치 자동 저장

## 기술 스택

- **PyQt6**: 크로스 플랫폼 GUI 프레임워크
- **SQLite**: 로컬 데이터베이스 (프롬프트, 버전, 결과 저장)
- **Python 3.8+**: 백엔드 로직
- **requests**: LLM API 통신

## 프로젝트 구조

```
prompt_manager/
├── run_gui.py                 # GUI 실행 스크립트
├── requirements-gui.txt       # PyQt GUI 의존성
├── src/
│   ├── backend/              # 데이터베이스 라이브러리
│   │   ├── database.py       # SQLite DB 로직
│   │   └── data/
│   │       └── prompt_manager.db  # SQLite 데이터베이스
│   └── gui/                  # PyQt GUI
│       ├── main_window.py    # 메인 윈도우
│       ├── utils/
│       │   ├── db_client.py  # DB 클라이언트
│       │   └── theme_manager.py  # 테마 관리
│       └── widgets/          # GUI 위젯
│           ├── task_navigator.py      # 태스크 목록
│           ├── prompt_editor.py       # 프롬프트 편집기
│           ├── variable_editor.py     # 변수 편집기
│           ├── result_viewer.py       # 결과 뷰어
│           ├── llm_settings.py        # LLM 설정
│           └── version_comparison_dialog.py  # 버전 비교
└── scripts/
    ├── run_gui.bat           # Windows 실행 스크립트
    └── run_gui.sh            # Linux/Mac 실행 스크립트
```

## 설치 및 실행

### 전제 조건
- Python 3.8 이상
- pip

### 설치

1. 레포지토리 클론
   ```bash
   git clone <repository-url>
   cd prompt_manager
   ```

2. 의존성 설치
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-gui.txt
   ```

### 실행

```bash
# Python으로 직접 실행
python run_gui.py

# Windows
scripts\run_gui.bat

# Linux/Mac
./scripts/run_gui.sh
```

## 사용 가이드

### 1️⃣ 태스크 생성 및 관리

1. **새 태스크 만들기**
   - 왼쪽 패널 상단의 `➕ New Task` 버튼 클릭
   - 태스크 이름 입력
   
2. **태스크 선택**
   - 태스크 목록에서 원하는 태스크 클릭
   - 중앙 에디터에 프롬프트 표시됨

3. **태스크 삭제**
   - 태스크 우클릭 → `Delete` 선택
   - 또는 태스크 선택 후 `Delete` 키

4. **즐겨찾기 설정**
   - 태스크 우클릭 → `Toggle Favorite`
   - ⭐ 아이콘으로 표시됨

### 2️⃣ 프롬프트 작성 및 편집

1. **프롬프트 입력**
   - 중앙 에디터의 "User Prompt" 영역에 프롬프트 작성
   - `{{변수명}}` 형식으로 변수 사용
   - 예: `Translate "{{text}}" to {{language}}`

2. **System Prompt 설정**
   - "System Prompt" 영역에 시스템 지시사항 입력
   - 예: `You are a professional translator`

3. **자동 저장**
   - 편집 내용은 자동으로 데이터베이스에 저장됨

### 3️⃣ 버전 관리

1. **새 버전 생성**
   - `New Version` 버튼 클릭
   - 버전 이름과 설명 입력
   - 현재 프롬프트가 새 버전으로 저장됨

2. **버전 선택**
   - 버전 타임라인에서 원하는 버전 클릭
   - 해당 버전의 프롬프트가 에디터에 로드됨

3. **버전 삭제**
   - 버전 우클릭 → `Delete Version`

4. **버전 비교**
   - 두 버전 선택 후 `Compare` 버튼 클릭
   - 차이점이 색상으로 표시됨

### 4️⃣ 변수 설정 및 실행

1. **변수 확인**
   - 오른쪽 "📝 Variables" 탭 클릭
   - 프롬프트의 `{{변수}}`가 자동으로 나열됨

2. **변수값 입력**
   - 각 변수에 값 입력
   - 예: `text = "Hello"`, `language = "Korean"`

3. **미리보기**
   - 하단에 렌더링된 최종 프롬프트 확인

4. **LLM 실행**
   - `▶ Run` 버튼 클릭
   - Temperature 슬라이더로 창의성 조절 (0.0~2.0)
   - 활성 엔드포인트로 자동 전송

### 5️⃣ LLM 엔드포인트 설정

1. **엔드포인트 추가**
   - 상단 탭에서 `⚙️ LLM Provider` 선택
   - `➕ Add Endpoint` 버튼 클릭
   - 필수 정보 입력:
     ```
     Name: My OpenAI
     Base URL: https://api.openai.com/v1
     API Key: sk-...
     Default Model: gpt-4
     ```

2. **연결 테스트**
   - `Test Connection` 버튼으로 연결 확인
   - 사용 가능한 모델 목록 표시됨

3. **활성 엔드포인트 설정**
   - 엔드포인트 목록에서 라디오 버튼 선택
   - 프롬프트 실행 시 이 엔드포인트 사용

4. **엔드포인트 수정/삭제**
   - 목록에서 엔드포인트 선택
   - `Edit` 또는 `Delete` 버튼 클릭

### 6️⃣ 결과 확인

1. **실행 결과 보기**
   - 오른쪽 "🤖 LLM Result" 탭 자동 전환
   - LLM 응답 내용 표시

2. **결과 이력**
   - 하단 "History" 섹션에서 이전 실행 기록 확인
   - 클릭하여 해당 결과 다시 보기

3. **메타 정보 확인**
   - 사용된 모델명
   - Temperature 값
   - 실행 시각
   - 사용된 프롬프트 원본

## 단축키

| 단축키 | 기능 |
|--------|------|
| `Ctrl+N` | 새 태스크 생성 |
| `Ctrl+S` | 현재 프롬프트 저장 (자동 저장됨) |
| `Ctrl+Q` | 애플리케이션 종료 |
| `Delete` | 선택된 태스크/버전 삭제 |
| `F5` | 프롬프트 실행 |

## 데이터 저장 위치

모든 데이터는 SQLite 데이터베이스에 저장됩니다:
```
src/backend/data/prompt_manager.db
```

이 파일을 백업하면 모든 태스크, 프롬프트, 버전, 결과, LLM 설정이 보존됩니다.

## 문제 해결

### PyQt6 설치 오류
```bash
pip install --upgrade pip
pip install PyQt6
```

### LLM 연결 실패
1. API Key가 올바른지 확인
2. Base URL이 정확한지 확인 (끝에 `/v1` 포함 여부)
3. 인터넷 연결 확인
4. API 사용 한도 확인

### 데이터베이스 오류
데이터베이스 파일 손상 시:
```bash
# 백업이 있다면
cp backup/prompt_manager.db src/backend/data/

# 새로 시작
rm src/backend/data/prompt_manager.db
python run_gui.py  # 자동으로 새 DB 생성
```

## 향후 계획

- [ ] 다크 모드 지원
- [ ] 프롬프트 템플릿 라이브러리
- [ ] 프롬프트 성능 분석 (A/B 테스트)
- [ ] 다국어 지원
- [ ] 프롬프트 export/import (JSON, Markdown)
- [ ] 클라우드 동기화
- [ ] 협업 기능 (프롬프트 공유)

## 라이센스

MIT License

## 기여

버그 리포트나 기능 제안은 GitHub Issues를 통해 제출해주세요.
