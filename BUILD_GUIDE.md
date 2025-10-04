# Prompt Manager - EXE 빌드 가이드

## 개요
이 가이드는 Prompt Manager GUI를 독립 실행 가능한 .exe 파일로 빌드하는 방법을 설명합니다.

## 시스템 요구사항
- Python 3.8 이상
- Windows 10/11
- 최소 2GB 여유 디스크 공간

## 빌드 단계

### 1. 의존성 설치
빌드에 필요한 패키지를 설치합니다:

```bash
pip install -r requirements-build.txt
```

또는 개별 설치:
```bash
pip install PyQt6>=6.5.0
pip install requests>=2.31.0
pip install pyinstaller>=5.13.0
pip install pyyaml
```

### 2. 빌드 실행

#### 방법 A: 배치 스크립트 사용 (권장)
```bash
scripts\build_exe.bat
```

이 스크립트는 자동으로:
1. Python 설치 확인
2. PyInstaller 확인/설치
3. 이전 빌드 정리
4. 새 실행 파일 빌드
5. 빌드 검증

#### 방법 B: 수동 빌드
```bash
pyinstaller --clean prompt_manager.spec
```

### 3. 빌드 결과물

빌드가 완료되면 다음 위치에 실행 파일이 생성됩니다:
```
dist/PromptManager.exe
```

파일 크기: 약 80-120MB

## 배포

생성된 `PromptManager.exe` 파일을 다른 PC에 복사하여 실행할 수 있습니다.

### 실행 시 데이터 저장 위치
프로그램은 다음 위치에 데이터를 저장합니다:
```
%APPDATA%\PromptManager\
```

실제 경로 예시:
```
C:\Users\[사용자명]\AppData\Roaming\PromptManager\
```

## 빌드 설정 커스터마이징

빌드 설정을 수정하려면 `prompt_manager.spec` 파일을 편집하세요.

### 주요 설정:
- **name**: 실행 파일 이름
- **icon**: 아이콘 파일 경로
- **console**: True로 설정하면 콘솔 창 표시
- **excludes**: 빌드에서 제외할 모듈

## 문제 해결

### 빌드 실패 시
1. 모든 의존성이 설치되었는지 확인
2. build 폴더와 dist 폴더 삭제 후 재시도
3. PyInstaller 버전 확인 (5.13.0 이상)

### 실행 파일이 실행되지 않을 때
1. Windows Defender나 백신 소프트웨어 확인
2. --debug 옵션으로 빌드하여 상세 로그 확인:
   ```bash
   pyinstaller --debug=all prompt_manager.spec
   ```

### 파일 크기가 너무 클 때
1. UPX 압축 활성화 (spec 파일에서 `upx=True`)
2. 불필요한 모듈 제외 (spec 파일의 excludes 리스트 수정)

## 빌드 환경 정보

### 포함된 컴포넌트:
- PyQt6 (GUI 프레임워크)
- SQLite (데이터베이스, Python 내장)
- requests (HTTP 통신)
- YAML 설정 파일
- 프롬프트 개선 템플릿

### 제외된 컴포넌트:
- FastAPI 백엔드 서버 (직접 SQLite 사용)
- 웹 프론트엔드
- Node.js 의존성

## 라이센스
빌드된 실행 파일은 원본 프로젝트의 라이센스를 따릅니다.
