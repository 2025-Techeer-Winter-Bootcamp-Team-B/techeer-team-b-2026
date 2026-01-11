# 📱 Frontend - Clerk 인증 테스트 앱

Clerk 인증을 테스트하기 위한 간단한 React 웹 앱입니다.

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
cd frontend
npm install
```

### 2. 환경변수 설정

`.env` 파일이 이미 생성되어 있습니다. 필요시 수정하세요:

```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_Y2FyZWZ1bC1zbmlwZS04My5jbGVyay5hY2NvdW50cy5kZXYk
VITE_API_BASE_URL=http://localhost:8000
```

### 3. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 http://localhost:3000 접속

## 🧪 테스트 방법

1. **로그인**: Clerk 로그인 화면에서 이메일로 가입/로그인
2. **API 테스트**: 
   - "내 프로필 조회" 버튼 클릭 → `/api/v1/auth/me` 호출
   - "Health Check" 버튼 클릭 → `/health` 호출
3. **응답 확인**: API 응답이 화면에 표시됩니다

## 📦 사용 기술

- React 18
- Vite
- Clerk React SDK
- Axios

## 🔧 개발 모드

```bash
npm run dev      # 개발 서버 (포트 3000)
npm run build    # 프로덕션 빌드
npm run preview  # 빌드 결과 미리보기
```
