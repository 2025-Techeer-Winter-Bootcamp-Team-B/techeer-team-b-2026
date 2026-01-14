# 주변 아파트 평균 가격 조회 기능 구현 문서

## 개요
`GET /apartments/{apt_id}/nearby_price` 엔드포인트를 구현하여, 특정 아파트와 같은 지역의 주변 아파트들의 평균 거래가격을 조회하는 기능을 추가했습니다.

## 구현 일자
2026-01-14

## 수정된 파일 목록

### 1. `backend/app/crud/sale.py` (신규 생성)
**목적**: 매매 거래 정보 CRUD 레이어 추가

**주요 메서드**:
- `get_target_apartment_average_area()`: 기준 아파트의 최근 거래 평균 면적 조회
- `get_nearby_average_price()`: 주변 아파트들의 평균 평당가 조회

**계산 방식**:
- 평당가 = `SUM(trans_price) / SUM(exclusive_area)`
- 거래 개수 = `COUNT(*)`

**필터 조건**:
- 같은 지역 (`region_id`)
- 자기 자신 제외 (`apt_id != target_apt_id`)
- 취소되지 않은 거래 (`is_canceled = False`)
- 삭제되지 않은 거래 (`is_deleted != True`)
- 최근 N개월 거래 (`contract_date >= date_from`)
- 가격 및 면적이 유효한 거래만

### 2. `backend/app/services/apartment.py` (수정)
**추가된 메서드**: `get_nearby_price()`

**기능**:
- 기준 아파트 정보 조회
- 지역 정보 조회 (lazy loading 방지를 위해 `state_crud.get()` 사용)
- 기준 아파트의 최근 거래 평균 면적 조회
- 주변 아파트 평균 가격 조회
- 예상 가격 계산: 평당가 × 기준 아파트 면적
- 거래 개수 5개 이하일 경우 `average_price = -1` 반환

**주의사항**:
- `target_apartment.region` 직접 접근 시 lazy loading 에러 발생 가능
- `state_crud.get()`을 사용하여 명시적으로 조회

### 3. `backend/app/api/v1/endpoints/apartments.py` (수정)
**추가된 엔드포인트**: `GET /apartments/{apt_id}/nearby_price`

**Query 파라미터**:
- `months`: 조회 기간 (개월, 기본값: 6, 범위: 1~24)

**응답 형식**:
```json
{
  "success": true,
  "data": {
    "apt_id": 1,
    "apt_name": "래미안 강남파크",
    "region_name": "강남구",
    "period_months": 6,
    "target_exclusive_area": 84.5,
    "average_price_per_sqm": 1005.9,
    "estimated_price": 85000,
    "transaction_count": 150,
    "average_price": 85000
  }
}
```

**캐싱**:
- Redis 캐싱 적용 (TTL: 10분 = 600초)
- 캐시 키: `realestate:apartment:nearby_price:apt:{apt_id}:months:{months}`

### 4. `backend/app/schemas/apartment.py` (수정)
**추가된 스키마**: `NearbyPriceResponse`

**필드**:
- `apt_id`: 아파트 ID
- `apt_name`: 아파트명
- `region_name`: 지역명
- `period_months`: 조회 기간 (개월)
- `target_exclusive_area`: 기준 아파트 전용면적 (㎡)
- `average_price_per_sqm`: 평당가 평균 (만원/㎡)
- `estimated_price`: 예상 가격 (만원)
- `transaction_count`: 거래 개수
- `average_price`: 평균 가격 (만원, 거래 개수 5개 이하면 -1)

### 5. `backend/app/utils/cache.py` (수정)
**추가된 함수**: `get_nearby_price_cache_key()`

**용도**: 주변 아파트 평균 가격 조회 결과 캐싱을 위한 키 생성

## 데이터베이스 변경사항
- **없음**: 기존 테이블 구조를 활용하며, 새로운 테이블이나 컬럼을 추가하지 않았습니다.
- **계산된 값 저장**: 계산된 평균 가격은 DB에 저장하지 않고, Redis 캐시에만 임시 저장합니다 (TTL: 10분).

## 에러 처리

### 발생했던 에러
**greenlet_spawn 에러**: SQLAlchemy 비동기 세션에서 lazy loading이 발생할 때 나타나는 에러

**원인**:
- `target_apartment.region` 직접 접근 시 lazy loading 트리거
- `target_detail` 변수가 정의되지 않았는데 사용됨

**해결 방법**:
- `state_crud.get()`을 사용하여 명시적으로 지역 정보 조회
- `target_exclusive_area` 변수를 이미 조회한 값으로 사용

## 성능 고려사항
- Redis 캐싱으로 동일한 요청에 대한 DB 쿼리 최소화
- SQL 집계 함수(`SUM`, `COUNT`) 사용으로 효율적인 계산
- 인덱스 활용: `sales.apt_id`, `sales.contract_date`, `apartments.region_id` 인덱스 필요

## 향후 개선 사항
- 인덱스 추가 검토: `sales` 테이블에 `(apt_id, contract_date)`, `(region_id, contract_date)` 복합 인덱스 고려
- 거래 개수 최소값 설정 가능하도록 파라미터 추가 검토
- 면적 범위 필터링 옵션 추가 검토
