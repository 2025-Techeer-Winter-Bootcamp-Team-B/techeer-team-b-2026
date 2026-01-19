# 🔍 Clerk 로그인 실패 원인 분석

> **분석 일시**: 2026-01-11  
> **분석 범위**: 프론트엔드, 백엔드 Clerk 인증 플로우 전체

## 📋 분석 결과 요약

프로젝트의 Clerk 관련 파일을 분석한 결과, **다음 5가지 주요 문제점**이 발견되었습니다:

1. ⚠️ **프론트엔드: `getToken()`이 null을 반환할 수 있음**
2. ⚠️ **프론트엔드: API 호출 시 토큰이 제대로 전달되지 않을 수 있음**
3. ⚠️ **백엔드: `verify_clerk_token` 함수의 로깅 부족**
4. ⚠️ **환경 변수: `VITE_CLERK_PUBLISHABLE_KEY`가 비어있을 수 있음**
5. ⚠️ **Clerk Dashboard: Allowed Origins 미설정 가능성**

---

## 🔬 상세 분석

### 1. 프론트엔드 Clerk 설정 (`frontend/src/lib/clerk.tsx`)

#### ✅ 정상 동작 부분

```typescript
// ClerkProvider가 올바르게 설정됨
export function ClerkAuthProvider({ children }: { children: React.ReactNode }) {
  const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || '';
  
  if (!CLERK_PUBLISHABLE_KEY || CLERK_PUBLISHABLE_KEY.trim() === '') {
    // 키가 없으면 Provider 없이 렌더링
    return <>{children}</>;
  }
  
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      {children}
    </ClerkProvider>
  );
}
```

#### ⚠️ 문제점 1: `useAuth()` 래퍼의 문제

```typescript
export function useAuth() {
  const hasKey = CLERK_PUBLISHABLE_KEY && CLERK_PUBLISHABLE_KEY.trim() !== '';
  
  if (!hasKey) {
    // 키가 없을 때 기본값 반환
    return React.useMemo(() => ({
      isSignedIn: false,
      userId: null,
      getToken: async () => null,  // ⚠️ 항상 null 반환!
      signOut: async () => {},
    }), []) as ReturnType<typeof useClerkAuth>;
  }
  
  return useClerkAuth();
}
```

**문제**: 키가 없을 때 `getToken()`이 항상 `null`을 반환합니다. 이 경우 로그인은 성공하지만 API 호출 시 토큰이 없어서 실패합니다.

**해결 방법**: 키가 없을 때는 로그인 자체를 막아야 합니다.

---

### 2. 프론트엔드 API 호출 (`frontend/src/hooks/useProfile.ts`)

#### ✅ 정상 동작 부분

```typescript
const fetchProfile = async () => {
  if (!isSignedIn || !getToken) {
    setProfile(null);
    return;
  }

  const token = await getToken();
  if (!token) {
    setProfile(null);
    return;  // ⚠️ 토큰이 없으면 조용히 실패
  }
  
  const response = await apiClient.get('/auth/me', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
};
```

#### ⚠️ 문제점 2: 토큰이 null일 때 에러 처리 부족

**문제**: `getToken()`이 `null`을 반환하면 조용히 실패합니다. 사용자에게 에러 메시지가 표시되지 않습니다.

**해결 방법**: 토큰이 없을 때 명확한 에러 메시지를 표시해야 합니다.

---

### 3. 백엔드 인증 의존성 (`backend/app/api/v1/deps.py`)

#### ✅ 정상 동작 부분

```python
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Account:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "MISSING_TOKEN",
                "message": "인증 토큰이 필요합니다."
            },
        )
    
    # Clerk 토큰 검증
    token_payload = await verify_clerk_token(
        authorization=f"Bearer {credentials.credentials}"
    )
    
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN",
                "message": "유효하지 않은 인증 토큰입니다."
            },
        )
```

#### ⚠️ 문제점 3: `verify_clerk_token`의 로깅 부족

`backend/app/core/clerk.py`의 `verify_clerk_token` 함수는 로깅을 하지만, 실제 에러 원인을 파악하기 어렵습니다.

---

### 4. 백엔드 토큰 검증 (`backend/app/core/clerk.py`)

#### ✅ 정상 동작 부분

```python
async def verify_clerk_token(
    authorization: Optional[str] = Header(None)
) -> Optional[dict]:
    if not authorization:
        logger.warning("Authorization 헤더가 없습니다.")
        return None
    
    if not authorization.startswith("Bearer "):
        logger.warning(f"Authorization 헤더 형식이 올바르지 않습니다: {authorization[:50]}")
        return None
    
    token = authorization.replace("Bearer ", "").strip()
    
    # JWT 검증 로직...
```

#### ⚠️ 문제점 4: JWKS 가져오기 실패 시 에러 처리

```python
try:
    jwks = await get_clerk_jwks(issuer=issuer)
except HTTPException as e:
    logger.error(f"JWKS 가져오기 실패: {e.detail}")
    return None  # ⚠️ 조용히 실패
```

**문제**: JWKS를 가져오지 못하면 조용히 실패합니다. 네트워크 문제인지, Clerk 설정 문제인지 알 수 없습니다.

---

## 🎯 주요 원인 후보

### 원인 1: 환경 변수 미설정 (가장 가능성 높음)

**증상**: 
- 브라우저 콘솔에 `hasKey: false` 출력
- 로그인 버튼 클릭 시 alert 표시

**확인 방법**:
```powershell
Get-Content .env | Select-String "VITE_CLERK"
```

**해결 방법**:
1. 프로젝트 루트 `.env` 파일에 `VITE_CLERK_PUBLISHABLE_KEY=pk_test_실제_키` 추가
2. Vite 서버 재시작

---

### 원인 2: Clerk Dashboard Allowed Origins 미설정

**증상**:
- 브라우저 콘솔에 CORS 오류
- 로그인 모달이 표시되지 않음

**확인 방법**:
1. Clerk Dashboard → Settings → Domains
2. Allowed Origins에 `http://localhost:3000` 추가되어 있는지 확인

**해결 방법**:
```
http://localhost:3000
http://localhost:5173
http://127.0.0.1:3000
```

---

### 원인 3: `getToken()`이 null 반환

**증상**:
- 로그인은 성공하지만 API 호출 시 401 에러
- 브라우저 네트워크 탭에서 Authorization 헤더가 없음

**확인 방법**:
```javascript
// 브라우저 콘솔에서
const { getToken } = useAuth();
const token = await getToken();
console.log('Token:', token);  // null이면 문제!
```

**해결 방법**:
1. `VITE_CLERK_PUBLISHABLE_KEY` 확인
2. ClerkProvider가 정상적으로 설정되었는지 확인
3. 로그인 상태 확인: `isSignedIn`이 `true`인지 확인

---

### 원인 4: 백엔드 토큰 검증 실패

**증상**:
- API 호출 시 401 Unauthorized
- 백엔드 로그에 "INVALID_TOKEN" 에러

**확인 방법**:
```powershell
docker-compose logs backend | Select-String "Clerk\|JWT\|INVALID"
```

**해결 방법**:
1. 백엔드 `.env`에 `CLERK_SECRET_KEY` 확인
2. Clerk Dashboard에서 Secret Key 확인
3. 네트워크 연결 확인 (JWKS 가져오기 실패 가능)

---

### 원인 5: DB에 사용자 없음 (자동 생성 실패)

**증상**:
- 로그인은 성공하지만 API 호출 시 사용자 없음 에러
- 백엔드 로그에 "USER_CREATION_FAILED" 에러

**확인 방법**:
```sql
SELECT * FROM accounts WHERE clerk_user_id = 'user_xxx';
```

**해결 방법**:
1. `get_current_user`의 자동 생성 로직 확인
2. DB 연결 확인
3. `account_crud.create_from_clerk` 함수 확인

---

## 🔧 단계별 진단 방법

### 1단계: 프론트엔드 환경 변수 확인

```powershell
# PowerShell에서
cd C:\Users\주수아\Desktop\techeer-team-b-2026
Get-Content .env | Select-String "VITE_CLERK"
```

**기대 결과**:
```
VITE_CLERK_PUBLISHABLE_KEY=pk_test_실제_키값
```

**실패 시**: `.env` 파일에 키 추가 후 Vite 서버 재시작

---

### 2단계: 브라우저 콘솔 확인

브라우저 개발자 도구(F12) → Console:

```javascript
// 1. 환경 변수 확인
console.log('Clerk Key:', import.meta.env.VITE_CLERK_PUBLISHABLE_KEY);

// 2. 로그인 상태 확인
import { useAuth } from '@/lib/clerk';
const { isSignedIn, getToken } = useAuth();
console.log('로그인 상태:', isSignedIn);

// 3. 토큰 가져오기 테스트
if (isSignedIn) {
  const token = await getToken();
  console.log('Token:', token ? '있음' : '없음');
}
```

**기대 결과**:
- `Clerk Key:` 실제 키 값 출력
- `로그인 상태:` true (로그인 후)
- `Token:` '있음'

---

### 3단계: 네트워크 탭 확인

브라우저 개발자 도구(F12) → Network:

1. **로그인 요청 확인**:
   - Clerk 로그인 API 호출이 있는지 확인
   - 응답 코드가 200인지 확인

2. **API 호출 확인**:
   - `/api/v1/auth/me` 호출 확인
   - Request Headers에 `Authorization: Bearer ...` 있는지 확인
   - Response Status가 200인지 확인

**실패 시**:
- Authorization 헤더가 없으면: `getToken()` 문제
- 401 에러면: 백엔드 토큰 검증 실패
- CORS 에러면: Clerk Dashboard 설정 문제

---

### 4단계: 백엔드 로그 확인

```powershell
# Docker 사용 시
docker-compose logs backend | Select-String "Clerk\|JWT\|INVALID\|MISSING"

# 또는 직접 실행 시
# 백엔드 터미널에서 로그 확인
```

**확인할 로그**:
- `Authorization 헤더가 없습니다.` → 토큰이 전달되지 않음
- `INVALID_TOKEN` → 토큰 검증 실패
- `JWKS 가져오기 실패` → Clerk 연결 문제

---

## 🚨 즉시 확인할 체크리스트

### 프론트엔드

- [ ] `.env` 파일에 `VITE_CLERK_PUBLISHABLE_KEY`가 있는가?
- [ ] 키 값이 비어있지 않은가?
- [ ] Vite 서버를 재시작했는가?
- [ ] 브라우저 콘솔에서 `hasKey: true`가 나오는가?
- [ ] 로그인 후 `isSignedIn`이 `true`인가?
- [ ] `getToken()`이 `null`이 아닌 값을 반환하는가?

### 백엔드

- [ ] `.env` 파일에 `CLERK_SECRET_KEY`가 있는가?
- [ ] 백엔드 서버가 실행 중인가?
- [ ] CORS 설정이 올바른가?
- [ ] DB 연결이 정상인가?

### Clerk Dashboard

- [ ] 애플리케이션이 생성되어 있는가?
- [ ] API Keys가 발급되어 있는가?
- [ ] Allowed Origins에 `http://localhost:3000`이 추가되어 있는가?
- [ ] Sign-in options가 활성화되어 있는가?

---

## 💡 권장 해결 순서

1. **환경 변수 확인** (가장 빠름)
   - `.env` 파일에 키가 있는지 확인
   - Vite 서버 재시작

2. **Clerk Dashboard 설정 확인**
   - Allowed Origins 추가
   - API Keys 확인

3. **브라우저 콘솔 확인**
   - 환경 변수 로드 상태
   - 로그인 상태
   - 토큰 가져오기 테스트

4. **네트워크 탭 확인**
   - API 호출 헤더 확인
   - 에러 응답 확인

5. **백엔드 로그 확인**
   - 토큰 검증 에러 확인
   - JWKS 가져오기 실패 확인

---

## 📝 추가 디버깅 코드

### 프론트엔드 디버깅 코드 추가

`frontend/src/lib/clerk.tsx`에 추가:

```typescript
export function useAuth() {
  const hasKey = CLERK_PUBLISHABLE_KEY && CLERK_PUBLISHABLE_KEY.trim() !== '';
  
  if (!hasKey) {
    console.error('❌ Clerk Key가 없습니다!');
    return React.useMemo(() => ({
      isSignedIn: false,
      userId: null,
      getToken: async () => {
        console.error('❌ getToken() 호출 실패: Clerk Key가 없습니다.');
        return null;
      },
      signOut: async () => {},
    }), []) as ReturnType<typeof useClerkAuth>;
  }
  
  const auth = useClerkAuth();
  
  // 디버깅: 토큰 가져오기 테스트
  if (auth.isSignedIn) {
    auth.getToken().then(token => {
      console.log('🔑 Token 가져오기 테스트:', token ? '성공' : '실패');
    });
  }
  
  return auth;
}
```

### 백엔드 디버깅 코드 추가

`backend/app/core/clerk.py`의 `verify_clerk_token` 함수에 추가:

```python
async def verify_clerk_token(
    authorization: Optional[str] = Header(None)
) -> Optional[dict]:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    logger.info(f"🔍 verify_clerk_token 호출됨")
    logger.info(f"🔍 authorization 헤더: {authorization[:50] if authorization else 'None'}...")
    
    # ... 기존 코드 ...
    
    try:
        jwks = await get_clerk_jwks(issuer=issuer)
        logger.info(f"✅ JWKS 가져오기 성공: {issuer}")
    except Exception as e:
        logger.error(f"❌ JWKS 가져오기 실패: {str(e)}")
        logger.error(f"❌ Issuer: {issuer}")
        return None
```

---

## 📚 참고 자료

- [Clerk 로컬 개발 가이드](./CLERK_LOCAL_DEVELOPMENT_GUIDE.md)
- [Clerk 공식 문서](https://clerk.com/docs)
- [백엔드 Clerk 설정](../backend/docs/clerk_setup.md)

---

**마지막 업데이트**: 2026-01-11  
**작성자**: Chief Product Officer & System Architect
