# 환경 변수 설정 가이드

## 📋 상황 요약

프로젝트 루트에 `.env` 파일이 없어서 지도 API 키와 Clerk 키를 어디에 두어야 할지 모르는 상황입니다.

## 🎯 가장 가능성 높은 원인 Top 3

1. **`.env` 파일이 프로젝트 루트에 없음** - `docker-compose.yml`과 백엔드가 프로젝트 루트의 `.env` 파일을 참조함
2. **환경 변수 접두사 혼동** - 프론트엔드가 Vite(`VITE_`)와 Expo(`EXPO_PUBLIC_`) 두 가지 환경에서 실행됨
3. **키 발급 위치 불명확** - Clerk와 카카오 지도 API 키를 어디서 발급받는지 모름

## ✅ 즉시 적용 가능한 해결 방법

### 1단계: `.env` 파일 생성

프로젝트 루트(`C:\Users\주수아\Desktop\techeer-team-b-2026`)에 `.env` 파일을 생성하세요.

**Windows PowerShell:**
```powershell
cd C:\Users\주수아\Desktop\techeer-team-b-2026
copy .env.example .env
```

**또는 직접 생성:**
```powershell
New-Item -Path .env -ItemType File
```

### 2단계: 필요한 키 발급받기

#### 🔐 Clerk 키 발급

1. **Clerk Dashboard 접속**: https://clerk.com
2. **로그인/회원가입**
3. **새 애플리케이션 생성** (또는 기존 앱 선택)
4. **API Keys 메뉴** 클릭
5. 다음 키들을 복사:
   - **Publishable Key** (`pk_test_...`)
   - **Secret Key** (`sk_test_...`)

#### 🗺️ 카카오 지도 API 키 발급

1. **카카오 개발자 콘솔 접속**: https://developers.kakao.com
2. **내 애플리케이션** → **애플리케이션 추가하기**
3. **앱 설정** → **플랫폼** → **Web 플랫폼 등록** (도메인: `http://localhost:3000`)
4. **JavaScript 키** 복사 (지도 표시용)
5. **REST API 키** 복사 (주소 검색용)

### 3단계: `.env` 파일에 키 입력

`.env` 파일을 열고 다음 형식으로 입력하세요:

```env
# Clerk 인증
CLERK_SECRET_KEY=sk_test_실제_키_입력
CLERK_PUBLISHABLE_KEY=pk_test_실제_키_입력

# 카카오 지도 API
KAKAO_JAVASCRIPT_KEY=실제_JavaScript_키_입력
KAKAO_REST_API_KEY=실제_REST_API_키_입력

# 프론트엔드 (Vite - 웹용)
VITE_CLERK_PUBLISHABLE_KEY=pk_test_실제_키_입력
VITE_KAKAO_JAVASCRIPT_KEY=실제_JavaScript_키_입력
VITE_API_BASE_URL=http://localhost:8000/api/v1

# 프론트엔드 (Expo - 모바일용)
EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_실제_키_입력
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000

# 데이터베이스 (기본값)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
POSTGRES_DB=realestate
POSTGRES_PORT=5432

# Redis
REDIS_PORT=6379

# 서버 포트
BACKEND_PORT=8000
FRONTEND_PORT=3000

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8081
```

## 🔍 검증 방법

### 실험 A: 환경 변수 로드 확인

**목적**: `.env` 파일이 제대로 로드되는지 확인

**실행 명령**:
```powershell
# Docker Compose 사용 시
docker-compose config | Select-String "CLERK\|KAKAO"

# 또는 백엔드 로그 확인
docker-compose logs backend | Select-String "CLERK\|KAKAO"
```

**기대 결과**: 환경 변수 값이 출력되어야 함

**결과 해석**:
- ✅ 값이 출력되면: 환경 변수 로드 성공
- ❌ 값이 비어있으면: `.env` 파일 경로나 변수 이름 확인 필요

### 실험 B: 프론트엔드에서 키 확인

**목적**: 프론트엔드에서 환경 변수가 접근 가능한지 확인

**실행 방법**:
1. 프론트엔드 개발 서버 실행
2. 브라우저 콘솔에서 확인:

```javascript
// Vite 환경 (웹)
console.log('Clerk Key:', import.meta.env.VITE_CLERK_PUBLISHABLE_KEY);
console.log('Kakao Key:', import.meta.env.VITE_KAKAO_JAVASCRIPT_KEY);
```

**기대 결과**: 키 값이 출력되어야 함

**결과 해석**:
- ✅ 값이 출력되면: 프론트엔드 환경 변수 설정 성공
- ❌ `undefined`면: Vite 서버 재시작 필요 (`npm run dev` 또는 `yarn dev`)

### 실험 C: 지도 로드 확인

**목적**: 카카오 지도가 정상적으로 로드되는지 확인

**실행 방법**:
1. 프론트엔드 실행
2. 지도 페이지 접속
3. 브라우저 콘솔 확인

**기대 결과**: 지도가 표시되고 콘솔에 에러가 없어야 함

**결과 해석**:
- ✅ 지도 표시됨: 카카오 지도 API 키 설정 성공
- ❌ "Kakao Map API Key is missing" 에러: `VITE_KAKAO_JAVASCRIPT_KEY` 확인 필요

## 📍 환경 변수 위치 정리

| 환경 | 파일 위치 | 접두사 | 사용 위치 |
|------|----------|--------|----------|
| **백엔드** | 프로젝트 루트 `.env` | 없음 | `docker-compose.yml`, `backend/app/core/config.py` |
| **프론트엔드 (Vite)** | 프로젝트 루트 `.env` | `VITE_` | `frontend/src/**/*.tsx` |
| **프론트엔드 (Expo)** | 프로젝트 루트 `.env` | `EXPO_PUBLIC_` | `frontend/app/_layout.tsx` |

## ⚠️ 중요 사항

1. **`.env` 파일은 절대 Git에 커밋하지 마세요!**
   - `.gitignore`에 이미 포함되어 있음
   - 실제 키가 노출되면 보안 문제 발생

2. **접두사 규칙**
   - Vite: `VITE_` 접두사 필수 (클라이언트 번들에 포함)
   - Expo: `EXPO_PUBLIC_` 접두사 필수 (클라이언트 번들에 포함)
   - 백엔드: 접두사 없음

3. **서버 재시작 필수**
   - `.env` 파일 수정 후:
     - Docker: `docker-compose restart`
     - Vite: 개발 서버 재시작
     - Expo: Metro 서버 재시작 (`npx expo start --clear`)

## 🔄 재발 방지 체크리스트

- [ ] `.env.example` 파일을 템플릿으로 유지 (실제 키 제외)
- [ ] 새 팀원 온보딩 시 `.env.example` 복사하여 `.env` 생성 안내
- [ ] 환경 변수 변경 시 관련 문서 업데이트
- [ ] CI/CD 파이프라인에서 환경 변수 별도 관리 (GitHub Secrets 등)

## 📚 참고 문서

- [백엔드 환경 변수 가이드](./backend/docs/environment_variables.md)
- [Clerk 설정 가이드](./backend/docs/clerk_setup.md)
- [프론트엔드 환경 변수 가이드](./frontend/ENV_SETUP.md)

---

**마지막 업데이트**: 2026-01-11
