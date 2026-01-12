# 🔍 아파트명 검색 API 명세서 (search_apart.py)

> **파일**: `search_apart.py`  
> **PRD 참조**: FEAT-004 아파트 검색  
> **담당자**: 박찬영  
> **작성일**: 2026-01-12

---

## 📋 개요

아파트명 검색 (자동완성) API를 제공합니다.

---

## 🌐 API 엔드포인트

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/api/v1/search/apartments` | 아파트명 검색 (자동완성) | ❌ |

---

## 📌 아파트명 검색 (자동완성)

### `GET /api/v1/search/apartments`

아파트명으로 검색합니다. 검색창에 2글자 이상 입력 시 자동완성 결과를 반환합니다.

### Request

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| `q` | string | ✅ | - | 검색어 (최소 2글자) |
| `limit` | integer | ❌ | 10 | 결과 개수 (1~50) |

### Response (200 OK)

```json
{
    "success": true,
    "data": {
        "results": [
            {
                "apt_id": 1,
                "apt_name": "래미안 원베일리",
                "address": "서울시 서초구 반포동 123-45",
                "sigungu_name": "서초구",
                "dong_name": "반포동",
                "location": {
                    "lat": 37.5049,
                    "lng": 127.0020
                }
            }
        ]
    },
    "meta": {
        "query": "래미안",
        "count": 1
    }
}
```

### 사용 예시

```bash
# cURL
curl "http://localhost:8000/api/v1/search/apartments?q=래미안&limit=10"
```

```javascript
// JavaScript
const response = await fetch('/api/v1/search/apartments?q=래미안&limit=10');
const data = await response.json();
```

---

## ⚙️ 기술 상세

### 데이터베이스 쿼리

```sql
SELECT * FROM apartments 
WHERE apt_name ILIKE '%검색어%'
ORDER BY apt_name
LIMIT 10;
```

### 의존 모델

```python
# app/models/apartment.py
class Apartment:
    apt_id: int          # PK
    apt_name: str        # 아파트명
    address: str         # 주소
    sigungu_name: str    # 시군구명
    dong_name: str       # 동명
    latitude: float      # 위도
    longitude: float     # 경도
```

---

## 📊 성능 목표

| 항목 | 목표 |
|------|------|
| 응답 시간 | < 100ms |
| 동시 요청 처리 | 100 req/s |

---

## 🚀 향후 개선 계획

| 우선순위 | 기능 | 설명 |
|----------|------|------|
| P1 | Redis 캐싱 | 자주 검색되는 키워드 캐싱 |
| P1 | Full-Text Search | PostgreSQL FTS 적용 |
| P2 | 검색어 하이라이팅 | 매칭된 부분 강조 |

---

## 🧪 테스트 방법

### Swagger UI
- **URL**: http://localhost:8000/docs
- Search 섹션에서 테스트

### cURL
```bash
curl "http://localhost:8000/api/v1/search/apartments?q=래미안&limit=5"
```

---

> 📅 최종 수정: 2026-01-12  
> ✍️ 작성자: 박찬영
