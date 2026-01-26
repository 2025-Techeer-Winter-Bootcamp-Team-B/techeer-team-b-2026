# 🔐 인증 API (Authentication)

Clerk 기반 사용자 인증 API를 설명합니다.

---

## 개요

SWEETHOME은 **Clerk**를 사용하여 사용자 인증을 처리합니다.

1. 프론트엔드에서 Clerk UI로 로그인
2. Clerk에서 JWT 토큰 발급
3. 백엔드에서 JWT 토큰 검증
4. 사용자 정보 반환

---

## API 엔드포인트

### 1. 현재 사용자 정보 조회

현재 로그인한 사용자의 정보를 반환합니다.

**요청**

```http
GET /api/v1/auth/me
Authorization: Bearer <jwt_token>
```

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "account_id": 1,
    "clerk_user_id": "user_2aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2u",
    "email": "user@example.com",
    "nickname": "홍길동",
    "profile_image": "https://clerk.com/images/...",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**에러 응답**

| 상태 코드 | 코드 | 설명 |
|-----------|------|------|
| 401 | UNAUTHORIZED | 토큰이 없거나 유효하지 않음 |
| 403 | FORBIDDEN | 권한 없음 |

---

### 2. Clerk 웹훅 처리

Clerk에서 사용자 이벤트를 수신하여 DB와 동기화합니다.

**요청**

```http
POST /api/v1/auth/webhook
Content-Type: application/json
svix-id: <svix-id>
svix-timestamp: <timestamp>
svix-signature: <signature>
```

```json
{
  "type": "user.created",
  "data": {
    "id": "user_2aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2u",
    "email_addresses": [
      { "email_address": "user@example.com" }
    ],
    "username": "honggildong"
  }
}
```

**응답 (200 OK)**

```json
{
  "success": true,
  "message": "Webhook processed"
}
```

**지원 이벤트**

| 이벤트 | 설명 |
|--------|------|
| user.created | 새 사용자 생성 → DB에 계정 추가 |
| user.updated | 사용자 정보 수정 → DB 업데이트 |
| user.deleted | 사용자 삭제 → DB에서 soft delete |

---

## 인증 플로우

### 1단계: 프론트엔드 로그인

```typescript
// React + Clerk
import { useAuth } from '@clerk/clerk-react';

function LoginButton() {
  const { signIn } = useAuth();
  
  return (
    <button onClick={() => signIn()}>
      로그인
    </button>
  );
}
```

### 2단계: JWT 토큰 획득

```typescript
import { useAuth } from '@clerk/clerk-react';

function MyComponent() {
  const { getToken } = useAuth();
  
  const fetchData = async () => {
    const token = await getToken();
    // token = "eyJhbGciOiJSUzI1NiIs..."
  };
}
```

### 3단계: API 요청

```typescript
const response = await fetch('/api/v1/auth/me', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### 4단계: 백엔드 검증

```python
# app/api/v1/deps.py
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Account:
    token = credentials.credentials
    
    # Clerk JWT 검증
    payload = await verify_clerk_token(f"Bearer {token}")
    clerk_user_id = payload.get("sub")
    
    # DB에서 사용자 조회
    user = await account_crud.get_by_clerk_user_id(db, clerk_user_id)
    
    # 없으면 자동 생성
    if not user:
        user = await create_user_from_token(db, payload)
    
    return user
```

---

## JWT 토큰 구조

Clerk에서 발급한 JWT 토큰의 페이로드:

```json
{
  "sub": "user_2aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2u",
  "email": "user@example.com",
  "iss": "https://careful-snipe-83.clerk.accounts.dev",
  "iat": 1234567890,
  "exp": 1234571490,
  "azp": "https://sweethome.vercel.app"
}
```

| 필드 | 설명 |
|------|------|
| sub | Clerk 사용자 ID |
| email | 사용자 이메일 |
| iss | 토큰 발급자 (Clerk) |
| iat | 발급 시간 |
| exp | 만료 시간 |
| azp | 인가된 클라이언트 |

---

## 에러 코드

| HTTP 상태 | 코드 | 설명 |
|-----------|------|------|
| 401 | TOKEN_MISSING | Authorization 헤더 없음 |
| 401 | TOKEN_INVALID | 토큰 형식이 잘못됨 |
| 401 | TOKEN_EXPIRED | 토큰 만료됨 |
| 401 | SIGNATURE_INVALID | 서명 검증 실패 |
| 403 | USER_DISABLED | 비활성화된 사용자 |

---

## 보안 고려사항

### 1. 토큰 저장
- **권장**: HttpOnly 쿠키 또는 메모리
- **비권장**: localStorage, sessionStorage

### 2. 토큰 갱신
- Clerk SDK가 자동으로 토큰 갱신 처리
- 만료 전 자동 리프레시

### 3. HTTPS 필수
- 프로덕션에서 반드시 HTTPS 사용
- 토큰 탈취 방지
