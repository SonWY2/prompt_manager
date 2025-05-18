# Prompt Manager

LLM 프롬프트를 관리하고 시험할 수 있는 웹 애플리케이션입니다. 이 도구는 LLM 프롬프트의 개발, 버전 관리, 테스트를 위한 통합 환경을 제공합니다.

![Prompt Manager 스크린샷](screenshot.png)

## 주요 기능

- **3단 레이아웃**: 태스크 네비게이터, 프롬프트 에디터, 결과 뷰어를 한눈에 확인
- **태스크 관리**: 관련 프롬프트를 그룹화하고 폴더 구조로 정리
- **버전 관리**: 프롬프트의 여러 버전을 생성하고 시각적 타임라인으로 확인
- **템플릿 변수**: `{{변수명}}` 형식의 템플릿 변수로 동적 프롬프트 작성
- **LLM 통합**: 프롬프트를 LLM API로 전송하고 결과를 즉시 확인
- **결과 비교**: 여러 버전의 프롬프트 결과를 나란히 비교
- **성능 메트릭**: 응답 시간, 토큰 사용량 등 통계 확인
- **다크 모드**: 라이트/다크 모드 토글 지원

## 기술 스택

### 프론트엔드
- **React**: UI 구성을 위한 자바스크립트 라이브러리
- **Tailwind CSS**: 스타일링을 위한 유틸리티 CSS 프레임워크
- **Zustand**: 상태 관리 라이브러리

### 백엔드
- **Node.js**: 서버 환경
- **Express**: 웹 프레임워크
- **JSON 파일 스토리지**: 데이터 저장을 위한 간단한 파일 기반 스토리지 시스템

## 프로젝트 구조

```
prompt_manager/
├── data/                      # 데이터 스토리지
│   └── prompt-data.json       # 프롬프트 데이터 JSON 파일
├── src/
│   ├── backend/               # 백엔드 코드
│   │   └── server.js          # Express 서버 
│   └── frontend/              # 프론트엔드 코드
│       ├── components/        # React 컴포넌트
│       │   ├── common/        # 공통 UI 컴포넌트
│       │   ├── layout/        # 레이아웃 관련 컴포넌트
│       │   ├── prompt/        # 프롬프트 관련 컴포넌트
│       │   ├── result/        # 결과 관련 컴포넌트
│       │   └── task/          # 태스크 관련 컴포넌트
│       ├── App.jsx            # 메인 React 앱 컴포넌트
│       ├── App.css            # 스타일시트
│       └── store.jsx          # Zustand 상태 관리
└── package.json               # 프로젝트 의존성 및 스크립트
```

## 설치 및 실행

### 전제 조건
- Node.js (v14 이상)
- npm 또는 yarn

### 설치 단계

1. 레포지토리 클론
   ```bash
   git clone <repository-url>
   cd prompt-manager
   ```

2. 의존성 설치
   ```bash
   npm install
   ```

3. 개발 서버 실행
   ```bash
   # 프론트엔드와 백엔드 동시 실행
   npm run dev:all

   # 또는 개별적으로 실행
   npm run dev        # 프론트엔드 개발 서버
   npm run backend    # 백엔드 서버
   ```

4. 웹 브라우저에서 `http://localhost:5173` 접속 (프론트엔드)
   - 백엔드는 기본적으로 `http://localhost:3000`에서 실행됩니다.

### 프로덕션 빌드

1. 프론트엔드 빌드
   ```bash
   npm run build
   ```

2. 프로덕션 서버 실행
   ```bash
   npm start
   ```

3. 웹 브라우저에서 `http://localhost:3000` 접속

## 사용 가이드

### 태스크 관리
1. 왼쪽 패널에서 "태스크 추가" 버튼을 클릭하여 새 태스크 생성
2. 태스크를 선택하여 관련 프롬프트와 버전 확인
3. "최근" 탭에서 최근 작업한 태스크 확인

### 프롬프트 작성 및 버전 관리
1. 중앙 패널의 에디터에서 프롬프트 작성
2. `{{변수명}}` 형식으로 템플릿 변수 사용
3. "새 버전 생성" 버튼을 클릭하여 현재 프롬프트의 새 버전 생성
4. 버전 타임라인에서 이전 버전으로 돌아가기

### 변수 관리 및 실행
1. 프롬프트 에디터 하단의 변수 관리 섹션에서 변수값 입력
2. "미리보기" 버튼을 클릭하여 렌더링된 프롬프트 확인
3. "실행" 버튼을 클릭하여 LLM API 호출

### 결과 확인 및 비교
1. 오른쪽 패널에서 LLM 응답 확인
2. "이력" 탭에서 이전 실행 결과 확인
3. "비교" 탭에서 두 버전의 프롬프트와 결과 비교
4. "메트릭" 탭에서 성능 통계 확인

## API 엔드포인트

### 태스크 관리
- `GET /api/tasks` - 모든 태스크 목록 가져오기
- `POST /api/tasks` - 새 태스크 생성

### 버전 관리
- `GET /api/tasks/:taskId/versions` - 특정 태스크의 모든 버전 가져오기
- `POST /api/tasks/:taskId/versions` - 새 버전 추가
- `PUT /api/tasks/:taskId/versions/:versionId` - 버전 업데이트

### 템플릿 변수 관리
- `GET /api/templates/:taskId/variables` - 특정 태스크의 템플릿 변수 가져오기
- `POST /api/templates/:taskId/variables` - 템플릿 변수 저장

### 변수 프리셋 관리
- `GET /api/variable-presets/:taskId` - 변수 프리셋 가져오기
- `POST /api/variable-presets/:taskId` - 변수 프리셋 저장

### LLM 통합
- `POST /api/llm/call` - LLM API 호출

### 버전 비교
- `GET /api/compare` - 두 버전 비교

## 향후 개선 사항

- **LLM 프로바이더 다양화**: OpenAI, Anthropic, Google 등 다양한 LLM API 지원
- **프롬프트 성능 분석**: A/B 테스트 및 상세 분석 기능
- **데이터베이스 마이그레이션**: MongoDB 또는 PostgreSQL로 데이터 저장소 전환
- **사용자 인증**: 멀티 유저 환경 지원 및 권한 관리
- **협업 기능**: 실시간 공동 편집 및 코멘트 기능
- **프롬프트 템플릿 라이브러리**: 자주 사용하는 패턴 저장 및 공유

## 라이센스

[MIT 라이센스](LICENSE)
