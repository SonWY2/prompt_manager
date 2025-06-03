
# 🚀 프론트엔드/백엔드 연결 실행 가이드

## 📋 현재 설정 요약
- **프론트엔드**: http://localhost:3030 (Vite 개발 서버)
- **백엔드**: http://localhost:3000 (Express 서버)
- **프록시**: /api/* 요청을 localhost:3000으로 전달

## 🔧 실행 단계

### 1단계: 서버 실행
```bash
cd D:\workspace\prompt_manager
npm run dev:all
```

### 2단계: 성공 확인 포인트

#### ✅ 백엔드 서버 로그 확인
```
서버 실행 중: http://localhost:3000
허용된 프론트엔드 원본: ["http://localhost:3030", "http://127.0.0.1:3030", ...]
데이터 저장 경로: D:\workspace\prompt_manager\data\prompt-data.json
```

#### ✅ 프론트엔드 개발 서버 로그 확인
```
🔧 개발 모드: Vite 프록시 사용 (/api/* → http://localhost:3000/api/*)
Local:   http://localhost:3030/
ready in XXXms
```

#### ✅ 브라우저에서 확인 (http://localhost:3030)
- 헤더에 🟢 "서버 연결됨" 표시
- 새 태스크 생성 시 에러 없음
- 네트워크 탭에서 `/api/tasks` 요청이 200 OK

## 🐛 문제 해결

### 포트 이미 사용 중인 경우
```bash
# 다른 포트로 변경
PORT=3031 npm run dev
```

### 백엔드 연결 실패 시
1. 방화벽 확인
2. 백엔드 서버 로그 확인
3. `npm run backend` 단독 실행 테스트

### CORS 오류 시
- 현재 CORS 설정에 3030 포트가 포함되어 있어 문제없음

## 🧪 수동 테스트

### 백엔드 직접 테스트
```bash
curl http://localhost:3000/api/tasks
```

### 프록시 테스트 (프론트엔드 실행 후)
```bash
curl http://localhost:3030/api/tasks
```

## 📊 성공 시 예상 출력
두 요청 모두 같은 JSON 응답을 받아야 함:
```json
{
  "tasks": []
}
```
