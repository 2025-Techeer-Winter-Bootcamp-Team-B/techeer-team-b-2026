# 🏠 아파트 API (Apartments)

아파트 정보 조회 API를 설명합니다.

---

## 개요

아파트 기본 정보, 상세 정보, 거래 내역을 조회하는 API입니다.

---

## API 엔드포인트

### 1. 아파트 기본 정보 조회

아파트의 기본 정보를 반환합니다.

**요청**

```http
GET /api/v1/apartments/{apt_id}
Authorization: Bearer <jwt_token>
```

**경로 파라미터**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| apt_id | int | ✓ | 아파트 ID |

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "apt_id": 12345,
    "apt_name": "래미안 강남 파크스위트",
    "region_id": 100,
    "region_name": "서울특별시 강남구 역삼동",
    "kapt_code": "A12345678",
    "is_deleted": false,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**에러 응답**

| 상태 코드 | 코드 | 설명 |
|-----------|------|------|
| 404 | APT_NOT_FOUND | 아파트를 찾을 수 없음 |

---

### 2. 아파트 상세 정보 조회

아파트의 상세 정보를 반환합니다.

**요청**

```http
GET /api/v1/apartments/{apt_id}/detail
Authorization: Bearer <jwt_token>
```

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "apt_id": 12345,
    "apt_name": "래미안 강남 파크스위트",
    "region_name": "서울특별시 강남구 역삼동",
    "road_address": "서울특별시 강남구 테헤란로 123",
    "jibun_address": "서울특별시 강남구 역삼동 123-45",
    "total_households": 500,
    "total_buildings": 5,
    "highest_floor": 25,
    "lowest_floor": 3,
    "use_approval_date": "2020-05-15",
    "latitude": 37.5012,
    "longitude": 127.0396,
    "avg_sale_price": 150000,
    "avg_jeonse_price": 80000,
    "recent_transactions": [
      {
        "type": "sale",
        "price": 155000,
        "area": 84.5,
        "floor": 15,
        "date": "2024-01-10"
      }
    ]
  }
}
```

**응답 필드**

| 필드 | 타입 | 설명 |
|------|------|------|
| apt_id | int | 아파트 ID |
| apt_name | string | 아파트명 |
| road_address | string | 도로명 주소 |
| jibun_address | string | 지번 주소 |
| total_households | int | 총 세대수 |
| total_buildings | int | 총 동 수 |
| highest_floor | int | 최고층 |
| lowest_floor | int | 최저층 |
| use_approval_date | string | 사용승인일 |
| latitude | float | 위도 |
| longitude | float | 경도 |
| avg_sale_price | int | 평균 매매가 (만원) |
| avg_jeonse_price | int | 평균 전세가 (만원) |

---

### 3. 거래 내역 조회

아파트의 매매/전월세 거래 내역을 반환합니다.

**요청**

```http
GET /api/v1/apartments/{apt_id}/transactions
Authorization: Bearer <jwt_token>
```

**쿼리 파라미터**

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| transaction_type | string | all | sale, jeonse, monthly, all |
| months | int | 12 | 조회 기간 (개월) |
| page | int | 1 | 페이지 번호 |
| size | int | 20 | 페이지 크기 |

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "trans_id": 1001,
        "type": "sale",
        "price": 155000,
        "exclusive_area": 84.5,
        "floor": 15,
        "contract_date": "2024-01-10",
        "is_canceled": false
      },
      {
        "trans_id": 1002,
        "type": "jeonse",
        "deposit": 80000,
        "monthly_rent": 0,
        "exclusive_area": 84.5,
        "floor": 12,
        "deal_date": "2024-01-05",
        "contract_type": "신규"
      }
    ],
    "total": 150,
    "page": 1,
    "size": 20
  }
}
```

**거래 필드 (매매)**

| 필드 | 타입 | 설명 |
|------|------|------|
| trans_id | int | 거래 ID |
| type | string | "sale" |
| price | int | 매매가 (만원) |
| exclusive_area | float | 전용면적 (㎡) |
| floor | int | 층 |
| contract_date | string | 계약일 |
| is_canceled | bool | 취소 여부 |

**거래 필드 (전월세)**

| 필드 | 타입 | 설명 |
|------|------|------|
| trans_id | int | 거래 ID |
| type | string | "jeonse" 또는 "monthly" |
| deposit | int | 보증금 (만원) |
| monthly_rent | int | 월세 (만원) |
| exclusive_area | float | 전용면적 (㎡) |
| floor | int | 층 |
| deal_date | string | 거래일 |
| contract_type | string | "신규" 또는 "갱신" |

---

### 4. 즐겨찾기 추가

아파트를 즐겨찾기에 추가합니다.

**요청**

```http
POST /api/v1/apartments/{apt_id}/favorite
Authorization: Bearer <jwt_token>
```

**응답 (201 Created)**

```json
{
  "success": true,
  "message": "즐겨찾기에 추가되었습니다",
  "data": {
    "favorite_id": 100,
    "apt_id": 12345,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

### 5. 즐겨찾기 삭제

아파트를 즐겨찾기에서 삭제합니다.

**요청**

```http
DELETE /api/v1/apartments/{apt_id}/favorite
Authorization: Bearer <jwt_token>
```

**응답 (200 OK)**

```json
{
  "success": true,
  "message": "즐겨찾기에서 삭제되었습니다"
}
```

---

## 캐싱 정보

| 엔드포인트 | TTL | 설명 |
|-----------|-----|------|
| /apartments/{apt_id} | 10분 | 기본 정보 캐싱 |
| /apartments/{apt_id}/detail | 10분 | 상세 정보 캐싱 |
| /apartments/{apt_id}/transactions | 5분 | 거래 내역 캐싱 |

캐시 키 형식: `realestate:apartment:{apt_id}:{endpoint}`

---

## 에러 코드

| HTTP 상태 | 코드 | 설명 |
|-----------|------|------|
| 404 | APT_NOT_FOUND | 아파트를 찾을 수 없음 |
| 503 | EXTERNAL_API_ERROR | 외부 API 호출 실패 |
| 500 | INTERNAL_SERVER_ERROR | 서버 내부 오류 |
