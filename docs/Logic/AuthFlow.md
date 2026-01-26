# 🔐 인증 플로우 (Auth Flow)

Clerk 기반 사용자 인증의 전체 흐름을 설명합니다.

---

## 전체 플로우

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   사용자    │     │  프론트엔드  │     │    Clerk    │     │   백엔드    │
└─────┬───────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
      │                    │                   │                   │
      │  1. 로그인 요청    │                   │                   │
      │───────────────────>│                   │                   │
      │                    │                   │                   │
      │                    │  2. 인증 요청     │                   │
      │                    │──────────────────>│                   │
      │                    │                   │                   │
      │                    │  3. 세션 생성     │                   │
      │                    │<──────────────────│                   │
      │                    │                   │                   │
      │  4. 로그인 완료    │                   │                   │
      │<───────────────────│                   │                   │
      │                    │                   │                   │
      │  5. API 호출 요청  │                   │                   │
      │───────────────────>│                   │                   │
      │                    │                   │                   │
      │                    │  6. JWT 토큰 요청 │                   │
      │                    │──────────────────>│                   │
      │                    │                   │                   │
      │                    │  7. JWT 발급      │                   │
      │                    │<──────────────────│                   │
      │                    │                   │                   │
      │                    │  8. API 호출 (JWT)│                   │
      │                    │──────────────────────────────────────>│
      │                    │                   │                   │
      │                    │                   │   9. 토큰 검증    │
      │                    │                   │<──────────────────│
      │                    │                   │──────────────────>│
      │                    │                   │                   │
      │                    │                   │  10. 사용자 조회  │
      │                    │                   │   (DB)            │
      │                    │                   │                   │
      │                    │  11. 응답 반환    │                   │
      │<─────────────────────────────────────────────────────────────
```

---

## 단계별 상세 설명

### 1단계: 프론트엔드 로그인

사용자가 Clerk UI를 통해 로그인합니다.

```typescript
// React + Clerk
import { SignIn } from '@clerk/clerk-react';

function LoginPage() {
  return (
    <SignIn
      appearance={{
        elements: {
          rootBox: "mx-auto",
          card: "bg-white shadow-lg rounded-lg"
        }
      }}
    />
  );
}
```

**지원 로그인 방식:**
- 이메일/비밀번호
- Google OAuth
- GitHub OAuth
- 기타 소셜 로그인

---

### 2단계: JWT 토큰 획득

프론트엔드에서 API 호출 전 JWT 토큰을 가져옵니다.

```typescript
import { useAuth } from '@clerk/clerk-react';

function useApiClient() {
  const { getToken } = useAuth();
  
  const apiCall = async (endpoint: string, options?: RequestInit) => {
    // JWT 토큰 가져오기
    const token = await getToken();
    
    return fetch(`/api/v1${endpoint}`, {
      ...options,
      headers: {
        ...options?.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
  };
  
  return { apiCall };
}
```

---

### 3단계: 백엔드 토큰 검증

백엔드에서 JWT 토큰을 검증합니다.

```python
# app/api/v1/deps.py
from jose import jwt
from jose.jwk import PyJWKClient

async def verify_clerk_token(authorization: str) -> dict:
    """Clerk JWT 토큰 검증"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header")
    
    token = authorization[7:]  # "Bearer " 제거
    
    try:
        # 1. JWKS에서 공개 키 가져오기
        jwks_client = PyJWKClient(settings.CLERK_JWKS_URL)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # 2. 토큰 검증
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.CLERK_ISSUER,
            options={"verify_aud": False}
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.JWTClaimsError:
        raise HTTPException(401, "Invalid claims")
    except Exception as e:
        raise HTTPException(401, f"Token validation failed: {str(e)}")
```

---

### 4단계: 사용자 조회/생성

토큰에서 사용자 정보를 추출하고 DB에서 조회합니다.

```python
# app/api/v1/deps.py
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Account:
    """현재 로그인한 사용자 조회"""
    token = credentials.credentials
    
    # 토큰 검증
    payload = await verify_clerk_token(f"Bearer {token}")
    clerk_user_id = payload.get("sub")
    
    if not clerk_user_id:
        raise HTTPException(401, "Invalid token: missing user ID")
    
    # DB에서 사용자 조회
    user = await account_crud.get_by_clerk_user_id(db, clerk_user_id)
    
    # 없으면 자동 생성
    if not user:
        email = payload.get("email") or f"{clerk_user_id}@clerk.user"
        nickname = payload.get("username") or email.split("@")[0]
        
        user = await account_crud.create_from_clerk(
            db,
            clerk_user_id=clerk_user_id,
            email=email,
            nickname=nickname[:50]
        )
    
    return user
```

---

## 웹훅 동기화

Clerk에서 사용자 이벤트가 발생하면 웹훅으로 백엔드에 알립니다.

```python
# app/api/v1/endpoints/auth.py
from svix.webhooks import Webhook

@router.post("/webhook")
async def clerk_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Clerk 웹훅 처리"""
    # 서명 검증
    payload = await request.body()
    headers = {
        "svix-id": request.headers.get("svix-id"),
        "svix-timestamp": request.headers.get("svix-timestamp"),
        "svix-signature": request.headers.get("svix-signature"),
    }
    
    wh = Webhook(settings.CLERK_WEBHOOK_SECRET)
    event = wh.verify(payload, headers)
    
    # 이벤트 처리
    event_type = event.get("type")
    data = event.get("data")
    
    if event_type == "user.created":
        await create_user(db, data)
    elif event_type == "user.updated":
        await update_user(db, data)
    elif event_type == "user.deleted":
        await delete_user(db, data["id"])
    
    return {"success": True}
```

---

## JWT 토큰 구조

```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "ins_2a..."
  },
  "payload": {
    "sub": "user_2aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2u",
    "email": "user@example.com",
    "iss": "https://careful-snipe-83.clerk.accounts.dev",
    "iat": 1705312200,
    "exp": 1705315800,
    "azp": "https://sweethome.vercel.app"
  }
}
```

| 필드 | 설명 |
|------|------|
| sub | Clerk 사용자 고유 ID |
| email | 사용자 이메일 |
| iss | 토큰 발급자 (Clerk 인스턴스) |
| iat | 발급 시간 (Unix timestamp) |
| exp | 만료 시간 (Unix timestamp) |
| azp | 인가된 클라이언트 URL |

---

## 보안 고려사항

### 1. 토큰 저장 위치

| 저장소 | 보안 | 권장 |
|--------|------|------|
| localStorage | XSS 취약 | ❌ |
| sessionStorage | XSS 취약 | ❌ |
| HttpOnly Cookie | 안전 | ✅ |
| 메모리 (변수) | 안전 | ✅ |

### 2. 토큰 자동 갱신

Clerk SDK가 만료 전 자동으로 토큰을 갱신합니다.

```typescript
// 토큰 갱신은 Clerk SDK가 자동 처리
const token = await getToken();  // 항상 유효한 토큰 반환
```

### 3. HTTPS 필수

프로덕션 환경에서는 반드시 HTTPS를 사용해야 합니다.

```nginx
# nginx 설정
server {
    listen 443 ssl;
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    
    # HSTS 헤더
    add_header Strict-Transport-Security "max-age=31536000" always;
}
```
