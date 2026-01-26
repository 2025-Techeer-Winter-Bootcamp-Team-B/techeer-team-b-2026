# 📖 API 설명서 (Manual)

SWEETHOME API의 사용법과 엔드포인트를 설명합니다.

## 🌐 API 개요

### Base URL

| 환경 | URL |
|------|-----|
| 개발 | `http://localhost:8000` |
| 프로덕션 | `https://api.sweethome.com` |

### 인증

대부분의 API는 인증이 필요합니다. Clerk JWT 토큰을 사용합니다.

```http
Authorization: Bearer <jwt_token>
```

### 응답 형식

모든 API는 JSON 형식으로 응답합니다.

```json
{
  "success": true,
  "data": { ... },
  "message": "성공"
}
```

### 에러 응답

```json
{
  "success": false,
  "error": {
    "code": "APT_NOT_FOUND",
    "message": "아파트를 찾을 수 없습니다"
  }
}
```

---

## 📁 API 카테고리

| 카테고리 | 설명 | 문서 |
|----------|------|------|
| **인증** | 로그인, 회원가입, 사용자 정보 | [Authentication.md](./Authentication.md) |
| **아파트** | 아파트 조회, 상세 정보 | [Apartments.md](./Apartments.md) |
| **검색** | 아파트 검색, AI 검색 | [Search.md](./Search.md) |
| **통계** | RVOL, 4분면, HPI 등 | [Statistics.md](./Statistics.md) |
| **대시보드** | 홈 화면 데이터 | [Dashboard.md](./Dashboard.md) |

---

## 🔗 API 엔드포인트 요약

### 인증 API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/v1/auth/me` | 현재 사용자 정보 |
| POST | `/api/v1/auth/webhook` | Clerk 웹훅 처리 |

### 아파트 API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/v1/apartments/{apt_id}` | 아파트 기본 정보 |
| GET | `/api/v1/apartments/{apt_id}/detail` | 아파트 상세 정보 |
| GET | `/api/v1/apartments/{apt_id}/transactions` | 거래 내역 |

### 검색 API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/v1/search` | 아파트 검색 |
| POST | `/api/v1/search/ai` | AI 자연어 검색 |

### 통계 API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/v1/statistics/rvol` | RVOL (상대 거래량) |
| GET | `/api/v1/statistics/quadrant` | 4분면 분석 |
| GET | `/api/v1/statistics/hpi` | 주택가격지수 |
| GET | `/api/v1/statistics/hpi/heatmap` | HPI 히트맵 |

### 대시보드 API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/v1/dashboard/summary` | 대시보드 요약 |
| GET | `/api/v1/dashboard/rankings` | 지역별 랭킹 |

---

## 📊 공통 파라미터

### 페이지네이션

```
?page=1&size=20
```

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| page | int | 1 | 페이지 번호 |
| size | int | 20 | 페이지 크기 |

### 거래 유형

```
?transaction_type=sale
```

| 값 | 설명 |
|----|------|
| sale | 매매 |
| jeonse | 전세 |
| monthly | 월세 |

### 기간

```
?months=6
```

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| months | int | 6 | 조회 기간 (개월) |

---

## 🔍 Swagger UI

자동 생성된 API 문서를 확인할 수 있습니다:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 📝 요청 예시

### cURL

```bash
curl -X GET "http://localhost:8000/api/v1/apartments/12345" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIs..."
```

### JavaScript (Axios)

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const response = await api.get('/apartments/12345');
```

### Python (httpx)

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/v1/apartments/12345",
        headers={"Authorization": f"Bearer {token}"}
    )
```
