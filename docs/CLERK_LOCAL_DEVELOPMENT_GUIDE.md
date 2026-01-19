# 🔐 Clerk 로컬 개발 환경 가이드

> **역할**: Chief Product Officer (CPO) & System Architect  
> **목적**: 로컬 개발 환경에서 Clerk 인증이 정상 작동하도록 설정하는 종합 가이드

## 📋 목차

1. [개요](#개요)
2. [전제 조건](#전제-조건)
3. [Clerk Dashboard 설정](#clerk-dashboard-설정)
4. [환경 변수 설정](#환경-변수-설정)
5. [프론트엔드 설정](#프론트엔드-설정)
6. [백엔드 설정](#백엔드-설정)
7. [로컬 개발 플로우](#로컬-개발-플로우)
8. [문제 해결](#문제-해결)
9. [디버깅 체크리스트](#디버깅-체크리스트)

---

## 개요

### Clerk 인증 아키텍처

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  프론트엔드  │ ──────> │    Clerk    │ ──────> │   백엔드    │
│  (React)    │  JWT    │  (인증 서버) │  검증   │  (FastAPI)  │
└─────────────┘  토큰   └─────────────┘  요청   └─────────────┘
```

### 인증 플로우

1. **사용자 로그인**: 프론트엔드에서 Clerk UI로 로그인
2. **JWT 토큰 발급**: Clerk가 JWT 토큰 발급
3. **API 호출**: 프론트엔드가 토큰을 헤더에 포함하여 백엔드 호출
4. **토큰 검증**: 백엔드가 Clerk JWKS로 토큰 검증
5. **사용자 조회**: DB에서 사용자 조회 또는 자동 생성

---

## 전제 조건

### 필수 요구사항

- [ ] Clerk 계정 생성 (https://clerk.com)
- [ ] Clerk 애플리케이션 생성
- [ ] 프로젝트 루트에 `.env` 파일 존재
- [ ] 프론트엔드 서버 실행 중 (`npm run dev`)
- [ ] 백엔드 서버 실행 중 (`docker-compose up` 또는 `uvicorn`)

### 권장 도구

- **브라우저 개발자 도구**: F12 (콘솔, 네트워크 탭)
- **Postman/Insomnia**: API 테스트용
- **ngrok**: 로컬 웹훅 테스트용 (선택)

---

## Clerk Dashboard 설정

### 1단계: 애플리케이션 생성

1. **Clerk Dashboard 접속**: https://dashboard.clerk.com
2. **Create Application** 클릭
3. **애플리케이션 이름 입력**: "부동산 분석 플랫폼" (또는 원하는 이름)
4. **Sign-in options 선택**: 
   - ✅ Email
   - ✅ Google (선택)
   - ✅ GitHub (선택)

### 2단계: API Keys 발급

1. **API Keys** 메뉴 클릭
2. **Publishable Key** 복사 (예: `pk_test_abc123...`)
3. **Secret Key** 복사 (예: `sk_test_xyz789...`)

> ⚠️ **보안**: Secret Key는 절대 프론트엔드에 노출하지 마세요!

### 3단계: Allowed Origins 설정 (중요!)

로컬 개발 환경에서 CORS 오류를 방지하기 위해 **반드시** 설정해야 합니다.

1. **Settings** → **Domains** 메뉴 클릭
2. **Allowed Origins** 섹션에서 다음 추가:
   ```
   http://localhost:3000
   http://localhost:5173
   http://127.0.0.1:3000
   http://127.0.0.1:5173
   ```
3. **Save** 클릭

> ⚠️ **주의**: 프로덕션 환경에서는 실제 도메인만 추가하세요.

### 4단계: Sign-in/Sign-up 설정

1. **User & Authentication** → **Email, Phone, Username** 메뉴
2. **Email** 활성화
3. **Password** 설정:
   - 최소 길이: 8자 (권장)
   - 복잡도 요구사항 설정 (선택)

---

## 환경 변수 설정

### 프로젝트 루트 `.env` 파일

프로젝트 루트(`C:\Users\주수아\Desktop\techeer-team-b-2026\.env`)에 다음을 추가:

```env
# ============================================================
# Clerk 인증 설정
# ============================================================
# Clerk Dashboard에서 발급받은 키를 입력하세요
CLERK_SECRET_KEY=sk_test_YOUR_SECRET_KEY_HERE
CLERK_PUBLISHABLE_KEY=pk_test_YOUR_PUBLISHABLE_KEY_HERE
CLERK_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE

# ============================================================
# 프론트엔드 환경 변수 (Vite)
# ============================================================
# VITE_ 접두사가 붙은 변수만 클라이언트 번들에 포함됩니다
VITE_CLERK_PUBLISHABLE_KEY=pk_test_YOUR_PUBLISHABLE_KEY_HERE
VITE_API_BASE_URL=http://localhost:8000/api/v1

# ============================================================
# CORS 설정
# ============================================================
# 프론트엔드 도메인을 쉼표로 구분하여 추가
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8081
```

### 환경 변수 확인

**PowerShell에서 확인**:
```powershell
cd C:\Users\주수아\Desktop\techeer-team-b-2026
Get-Content .env | Select-String "CLERK"
```

**기대 결과**:
```
CLERK_SECRET_KEY=sk_test_실제_키
CLERK_PUBLISHABLE_KEY=pk_test_실제_키
VITE_CLERK_PUBLISHABLE_KEY=pk_test_실제_키
```

---

## 프론트엔드 설정

### 1단계: ClerkProvider 설정 확인

`frontend/src/lib/clerk.tsx`에서 `ClerkProvider`가 올바르게 설정되어 있는지 확인:

```typescript
const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || '';

export function ClerkAuthProvider({ children }: { children: React.ReactNode }) {
  if (!CLERK_PUBLISHABLE_KEY || CLERK_PUBLISHABLE_KEY.trim() === '') {
    console.warn('⚠️ Clerk Publishable Key가 설정되지 않았습니다.');
    return <>{children}</>;
  }

  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      {children}
    </ClerkProvider>
  );
}
```

### 2단계: 앱 루트에서 ClerkProvider 감싸기

`frontend/src/main.tsx`에서 확인:

```typescript
import { ClerkAuthProvider } from "./lib/clerk";

createRoot(rootElement).render(
  <ErrorBoundary>
    <ClerkAuthProvider>
      <App />
    </ClerkAuthProvider>
  </ErrorBoundary>
);
```

### 3단계: 로그인 버튼 추가

컴포넌트에서 로그인 버튼 사용:

```typescript
import { SafeSignInButton, useAuth } from '@/lib/clerk';

function MyComponent() {
  const { isSignedIn, getToken } = useAuth();
  
  return (
    <div>
      {!isSignedIn ? (
        <SafeSignInButton mode="modal">
          <button>로그인</button>
        </SafeSignInButton>
      ) : (
        <div>로그인됨!</div>
      )}
    </div>
  );
}
```

### 4단계: API 호출 시 토큰 포함

```typescript
import { useAuth } from '@/lib/clerk';
import apiClient from '@/lib/api';

function MyComponent() {
  const { getToken } = useAuth();
  
  const fetchData = async () => {
    const token = await getToken();
    
    const response = await apiClient.get('/auth/me', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    
    console.log(response.data);
  };
}
```

---

## 백엔드 설정

### 1단계: 환경 변수 확인

백엔드는 프로젝트 루트의 `.env` 파일을 자동으로 읽습니다.

**확인 방법**:
```python
from app.core.config import settings

print(f"CLERK_SECRET_KEY: {settings.CLERK_SECRET_KEY[:10]}...")
```

### 2단계: CORS 설정 확인

`backend/app/main.py`에서 CORS 설정 확인:

```python
from app.core.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3단계: 인증 의존성 사용

API 엔드포인트에서 인증 사용:

```python
from app.api.v1.deps import get_current_user
from app.models.account import Account

@router.get("/me")
async def get_my_profile(
    current_user: Account = Depends(get_current_user)
):
    return {
        "success": True,
        "data": current_user
    }
```

---

## 로컬 개발 플로우

### 전체 시퀀스

```
1. 프론트엔드 서버 시작
   └─> cd frontend && npm run dev

2. 백엔드 서버 시작
   └─> docker-compose up backend
   또는
   └─> cd backend && uvicorn app.main:app --reload

3. 브라우저에서 접속
   └─> http://localhost:3000

4. 로그인 버튼 클릭
   └─> Clerk 로그인 모달 표시

5. 이메일/비밀번호 입력
   └─> Clerk 인증 처리

6. 로그인 성공
   └─> JWT 토큰 발급

7. API 호출
   └─> Authorization: Bearer {token}

8. 백엔드 토큰 검증
   └─> Clerk JWKS로 검증

9. 사용자 조회/생성
   └─> DB에서 사용자 정보 반환
```

### 테스트 시나리오

#### 시나리오 1: 신규 사용자 로그인

1. **로그인**: Clerk UI로 이메일/비밀번호 입력
2. **회원가입**: 신규 사용자 자동 생성
3. **API 호출**: `/api/v1/auth/me` 호출
4. **결과**: 사용자 정보 반환

#### 시나리오 2: 기존 사용자 로그인

1. **로그인**: Clerk UI로 로그인
2. **API 호출**: `/api/v1/auth/me` 호출
3. **결과**: 기존 사용자 정보 반환

---

## 문제 해결

### 문제 1: "Clerk Key를 찾을 수 없습니다" 오류

**증상**: 브라우저 콘솔에 `hasKey: false` 출력

**원인**:
- `.env` 파일에 `VITE_CLERK_PUBLISHABLE_KEY`가 없음
- 값이 비어있음
- Vite 서버가 재시작되지 않음

**해결 방법**:
1. `.env` 파일 확인:
   ```powershell
   Get-Content .env | Select-String "VITE_CLERK"
   ```
2. 값이 비어있으면 실제 키 입력
3. Vite 서버 재시작:
   ```powershell
   # Ctrl+C로 종료 후
   cd frontend
   npm run dev
   ```

### 문제 2: CORS 오류

**증상**: 브라우저 콘솔에 `CORS policy` 오류

**원인**:
- Clerk Dashboard에 Allowed Origins 미설정
- 백엔드 CORS 설정 오류

**해결 방법**:
1. **Clerk Dashboard 설정**:
   - Settings → Domains → Allowed Origins
   - `http://localhost:3000` 추가
2. **백엔드 `.env` 확인**:
   ```env
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
   ```
3. **백엔드 서버 재시작**

### 문제 3: "INVALID_TOKEN" 오류

**증상**: API 호출 시 401 Unauthorized

**원인**:
- JWT 토큰이 만료됨
- 토큰 형식 오류
- Clerk JWKS 가져오기 실패

**해결 방법**:
1. **프론트엔드에서 토큰 재발급**:
   ```typescript
   const token = await getToken({ template: 'default' });
   ```
2. **백엔드 로그 확인**:
   ```powershell
   docker-compose logs backend | Select-String "Clerk\|JWT"
   ```
3. **Clerk Dashboard에서 키 확인**

### 문제 4: 로그인 모달이 표시되지 않음

**증상**: 로그인 버튼 클릭해도 아무 반응 없음

**원인**:
- `ClerkProvider`가 설정되지 않음
- `VITE_CLERK_PUBLISHABLE_KEY`가 비어있음

**해결 방법**:
1. **브라우저 콘솔 확인**:
   ```javascript
   console.log('Clerk Key:', import.meta.env.VITE_CLERK_PUBLISHABLE_KEY);
   ```
2. **`ClerkAuthProvider` 확인**:
   - `main.tsx`에서 `ClerkAuthProvider`로 감싸져 있는지 확인
3. **환경 변수 재확인**

### 문제 5: 백엔드에서 사용자를 찾을 수 없음

**증상**: 로그인은 성공했지만 API 호출 시 사용자 없음

**원인**:
- DB에 사용자가 없음
- 자동 생성 로직 오류

**해결 방법**:
1. **자동 생성 확인**:
   - `get_current_user` 의존성에서 자동 생성 로직 확인
2. **DB 확인**:
   ```sql
   SELECT * FROM accounts WHERE clerk_user_id = 'user_xxx';
   ```
3. **웹훅 확인** (선택):
   - Clerk 웹훅이 설정되어 있으면 자동 생성됨

---

## 디버깅 체크리스트

### 프론트엔드 체크리스트

- [ ] `.env` 파일에 `VITE_CLERK_PUBLISHABLE_KEY`가 있는가?
- [ ] 키 값이 비어있지 않은가?
- [ ] Vite 서버를 재시작했는가?
- [ ] 브라우저 콘솔에서 `hasKey: true`가 나오는가?
- [ ] `ClerkProvider`가 앱 루트를 감싸고 있는가?
- [ ] 로그인 버튼이 `SafeSignInButton`으로 구현되어 있는가?

### 백엔드 체크리스트

- [ ] `.env` 파일에 `CLERK_SECRET_KEY`가 있는가?
- [ ] 백엔드 서버가 실행 중인가?
- [ ] CORS 설정이 올바른가?
- [ ] `verify_clerk_token` 함수가 정상 작동하는가?
- [ ] DB 연결이 정상인가?

### Clerk Dashboard 체크리스트

- [ ] 애플리케이션이 생성되어 있는가?
- [ ] API Keys가 발급되어 있는가?
- [ ] Allowed Origins에 `http://localhost:3000`이 추가되어 있는가?
- [ ] Sign-in options가 활성화되어 있는가?

### 네트워크 체크리스트

- [ ] 프론트엔드가 `http://localhost:3000`에서 실행 중인가?
- [ ] 백엔드가 `http://localhost:8000`에서 실행 중인가?
- [ ] 브라우저에서 네트워크 탭에서 API 호출이 보이는가?
- [ ] Authorization 헤더가 포함되어 있는가?

---

## 빠른 참조

### 환경 변수 요약

| 변수명 | 위치 | 용도 | 필수 |
|--------|------|------|------|
| `VITE_CLERK_PUBLISHABLE_KEY` | 프론트엔드 | Clerk UI 표시 | ✅ |
| `CLERK_SECRET_KEY` | 백엔드 | JWT 검증 | ✅ |
| `CLERK_PUBLISHABLE_KEY` | 백엔드 | 참조용 | ❌ |
| `CLERK_WEBHOOK_SECRET` | 백엔드 | 웹훅 검증 | ❌ |

### 주요 파일 위치

- **프론트엔드 Clerk 설정**: `frontend/src/lib/clerk.tsx`
- **백엔드 Clerk 검증**: `backend/app/core/clerk.py`
- **환경 변수**: 프로젝트 루트 `.env`
- **CORS 설정**: `backend/app/main.py`

### 유용한 명령어

```powershell
# 환경 변수 확인
Get-Content .env | Select-String "CLERK"

# 백엔드 로그 확인
docker-compose logs backend | Select-String "Clerk\|JWT"

# 프론트엔드 서버 재시작
cd frontend
npm run dev

# 백엔드 서버 재시작
docker-compose restart backend
```

---

## 📚 추가 자료

- [Clerk 공식 문서](https://clerk.com/docs)
- [Clerk React SDK](https://clerk.com/docs/references/react/overview)
- [백엔드 Clerk 설정](./clerk_setup.md)
- [인증 플로우](./auth_flow.md)

---

**마지막 업데이트**: 2026-01-11  
**작성자**: Chief Product Officer & System Architect
