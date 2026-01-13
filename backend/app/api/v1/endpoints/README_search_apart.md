# 아파트명 검색 API 명세서

## 📋 개요

- **담당자**: 박찬영
- **우선순위**: P0 (필수)
- **엔드포인트**: `GET /api/v1/search/apartments`
- **기능**: 아파트명으로 검색하여 자동완성 결과를 반환합니다.

---

## 🎯 API 엔드포인트

### GET /api/v1/search/apartments

아파트명으로 검색합니다. 검색창에 2글자 이상 입력 시 자동완성 결과를 반환합니다.

#### Query Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 설명 | 예시 |
|---------|------|------|--------|------|------|
| `q` | string | ✅ | - | 검색어 (2글자 이상, 최대 50자) | `래미안` |
| `limit` | integer | ❌ | 10 | 결과 개수 (1~50) | `20` |

#### Request Example

```bash
GET /api/v1/search/apartments?q=래미안&limit=10
```

#### Response (200 OK)

**참고**: ERD 설계에 따라 `APARTMENTS` 테이블에는 기본 정보만 포함됩니다. 상세 정보(주소, 좌표 등)는 `APART_DETAILS` 테이블에 있으며, 필요시 별도 API를 통해 조회할 수 있습니다.

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "apt_id": 1,
        "apt_name": "래미안 원베일리",
        "kapt_code": "A14074102",
        "region_id": 1168010100,
        "address": null,
        "location": null
      },
      {
        "apt_id": 2,
        "apt_name": "래미안 힐스테이트",
        "kapt_code": "A14074103",
        "region_id": 1168010200,
        "address": null,
        "location": null
      }
    ]
  },
  "meta": {
    "query": "래미안",
    "count": 2
  }
}
```

#### Error Responses

**400 Bad Request** - 검색어가 2글자 미만
```json
{
  "detail": {
    "code": "VALIDATION_ERROR",
    "message": "검색어는 최소 2글자 이상이어야 합니다."
  }
}
```

**422 Unprocessable Entity** - 입력값 검증 실패
```json
{
  "detail": [
    {
      "loc": ["query", "q"],
      "msg": "ensure this value has at least 2 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

---

## 🏗️ 아키텍처

### 레이어드 아키텍처

이 API는 레이어드 아키텍처를 따릅니다:

```
API Layer (endpoints/search_apart.py)
  ↓
Service Layer (services/search.py)
  ↓
CRUD Layer (crud/apartment.py)
  ↓
Model Layer (models/apartment.py)
  ↓
Database (PostgreSQL)
```

### 각 레이어의 역할

1. **API Layer**: 요청/응답 처리, 파라미터 검증
2. **Service Layer**: 비즈니스 로직 처리, 데이터 변환
3. **CRUD Layer**: DB 쿼리 실행
4. **Model Layer**: 데이터 구조 정의

---

## 🔍 동작 흐름

1. 클라이언트가 검색어를 전송 (`q=래미안`)
2. API 엔드포인트에서 파라미터 검증 (Pydantic)
3. Service 레이어에서 비즈니스 로직 처리
4. CRUD 레이어에서 DB 쿼리 실행 (`ILIKE '%래미안%'`)
5. 결과를 응답 형식에 맞게 변환
6. 클라이언트로 응답 반환

---

## 📝 기술적 세부사항

### 검색 방식

- **대소문자 구분 없음**: `ILIKE` 사용
- **부분 일치**: 검색어가 포함된 모든 아파트 검색
- **정렬**: 아파트명 오름차순 (`ORDER BY apt_name`)
- **필터링**: 삭제되지 않은 아파트만 조회 (`is_deleted = False`)
- **데이터 구조**: ERD 설계에 따라 기본 정보만 반환 (상세 정보는 별도 API)

### 성능 최적화

- **인덱스**: `apt_name` 컬럼에 인덱스 필요
- **제한**: 최대 50개 결과 반환
- **캐싱**: Redis 캐싱 적용 시 TTL 1시간 권장

### 데이터베이스 쿼리

**ERD 설계에 따른 쿼리**:
```sql
SELECT 
    apt_id, apt_name, kapt_code, region_id
FROM apartments
WHERE apt_name ILIKE '%래미안%'
  AND is_deleted = False
ORDER BY apt_name
LIMIT 10;
```

**참고**: 
- `APARTMENTS` 테이블: 기본 정보 (apt_id, apt_name, kapt_code, region_id)
- `APART_DETAILS` 테이블: 상세 정보 (주소, 좌표, 건물 정보 등)
- 상세 정보가 필요한 경우 `APART_DETAILS` 테이블과 JOIN하여 조회

---

## ✅ 테스트 방법

### cURL

```bash
curl -X GET "http://localhost:8000/api/v1/search/apartments?q=래미안&limit=10"
```

### Swagger UI

1. `http://localhost:8000/docs` 접속
2. `🔍 Search (검색)` 섹션에서 `GET /api/v1/search/apartments` 선택
3. `q` 파라미터에 `래미안` 입력
4. `limit` 파라미터에 `10` 입력
5. `Execute` 클릭

---

## 📚 관련 파일

- **API 엔드포인트**: `backend/app/api/v1/endpoints/search_apart.py`
- **Service 레이어**: `backend/app/services/search.py`
- **CRUD 레이어**: `backend/app/crud/apartment.py`
- **모델**: `backend/app/models/apartment.py`
- **스키마**: `backend/app/schemas/apartment.py`

---

## 🚀 향후 개선 사항

- [ ] Redis 캐싱 추가
- [ ] 검색어 자동완성 개선 (한글 초성 검색)
- [ ] 검색 결과 순위 개선 (인기순, 거리순)
- [ ] 검색 기록 저장 (로그인 사용자)
- [ ] 페이지네이션 추가 (대량 데이터 처리)
