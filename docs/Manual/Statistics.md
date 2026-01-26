# 📊 통계 API (Statistics)

부동산 시장 분석을 위한 통계 API를 설명합니다.

---

## 개요

부동산 시장 분석에 필요한 다양한 통계 데이터를 제공합니다:

- **RVOL**: 상대 거래량 (시장 활성도)
- **4분면 분석**: 매매/전세 변화율 기반 시장 분류
- **HPI**: 주택가격지수
- **거래량 추이**: 월별 거래량

---

## API 엔드포인트

### 1. RVOL (상대 거래량)

현재 거래량과 과거 평균을 비교하여 시장 활성도를 측정합니다.

**요청**

```http
GET /api/v1/statistics/rvol
Authorization: Bearer <jwt_token>
```

**쿼리 파라미터**

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| region_type | string | 전국 | 전국, 수도권, 지방5대광역시 |
| city_name | string | - | 도시명 (지방5대광역시 시 필수) |
| transaction_type | string | sale | sale, jeonse |
| period_months | int | 3 | 비교 기간 (개월) |

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "region_type": "전국",
    "transaction_type": "sale",
    "current_volume": 45000,
    "average_volume": 30000,
    "rvol": 1.5,
    "signal": "거래 급증",
    "trend": "상승",
    "period": {
      "current": "2024-01",
      "compare_start": "2023-10",
      "compare_end": "2023-12"
    }
  }
}
```

**RVOL 해석**

| RVOL 값 | 신호 | 의미 |
|---------|------|------|
| > 1.5 | 거래 급증 | 시장 과열 가능성 |
| 1.0 ~ 1.5 | 거래 활발 | 정상 활성화 |
| 0.7 ~ 1.0 | 보통 | 평균 수준 |
| < 0.7 | 거래 위축 | 시장 침체 |

---

### 2. 4분면 분석

매매 변화율과 전세 변화율을 기준으로 시장을 분류합니다.

**요청**

```http
GET /api/v1/statistics/quadrant
Authorization: Bearer <jwt_token>
```

**쿼리 파라미터**

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| period_months | int | 6 | 분석 기간 (개월) |

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "quadrant": 1,
    "quadrant_name": "매수 전환",
    "sale_change_rate": 5.2,
    "jeonse_change_rate": -2.1,
    "analysis": "매매가 상승, 전세가 하락 중. 매수 수요 증가 신호",
    "regions": [
      {
        "region_name": "서울특별시 강남구",
        "quadrant": 1,
        "sale_change_rate": 7.5,
        "jeonse_change_rate": -3.2
      }
    ]
  }
}
```

**4분면 설명**

```
         전세 상승 (+)
              │
    2분면     │     4분면
  (임대 선호) │   (활성화)
              │
──────────────┼────────────── 매매
  매매 하락   │   매매 상승
    (-)       │     (+)
              │
    3분면     │     1분면
  (시장 위축) │  (매수 전환)
              │
         전세 하락 (-)
```

| 분면 | 조건 | 의미 |
|------|------|------|
| 1분면 | 매매↑, 전세↓ | 매수 전환 (전세→매매) |
| 2분면 | 매매↓, 전세↑ | 임대 선호 (매매→전세) |
| 3분면 | 매매↓, 전세↓ | 시장 위축 |
| 4분면 | 매매↑, 전세↑ | 시장 활성화 |

---

### 3. HPI (주택가격지수)

지역별 주택가격지수 추이를 반환합니다.

**요청**

```http
GET /api/v1/statistics/hpi
Authorization: Bearer <jwt_token>
```

**쿼리 파라미터**

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| region_type | string | 전국 | 전국, 수도권, 지방5대광역시 |
| city_name | string | - | 도시명 |
| index_type | string | sale | sale, jeonse |
| max_years | int | 5 | 조회 기간 (년) |

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "region_type": "전국",
    "index_type": "sale",
    "base_date": "2021-01",
    "base_value": 100.0,
    "current_value": 115.2,
    "change_rate": 15.2,
    "trend": [
      {"date": "2023-01", "value": 110.5},
      {"date": "2023-02", "value": 111.2},
      {"date": "2023-03", "value": 112.8}
    ]
  }
}
```

---

### 4. HPI 히트맵

지역별 HPI를 히트맵 형태로 반환합니다.

**요청**

```http
GET /api/v1/statistics/hpi/heatmap
Authorization: Bearer <jwt_token>
```

**쿼리 파라미터**

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| index_type | string | sale | sale, jeonse |

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "index_type": "sale",
    "date": "2024-01",
    "regions": [
      {
        "region_name": "서울특별시",
        "value": 125.3,
        "change_rate": 2.5,
        "color": "#ff4444"
      },
      {
        "region_name": "경기도",
        "value": 118.7,
        "change_rate": 1.8,
        "color": "#ff7744"
      }
    ]
  }
}
```

---

### 5. 거래량 추이

월별 거래량 추이를 반환합니다.

**요청**

```http
GET /api/v1/statistics/transaction-volume
Authorization: Bearer <jwt_token>
```

**쿼리 파라미터**

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| region_type | string | 전국 | 전국, 수도권, 지방5대광역시 |
| transaction_type | string | sale | sale, jeonse |
| max_years | int | 5 | 조회 기간 (년) |

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "region_type": "전국",
    "transaction_type": "sale",
    "volumes": [
      {"month": "2023-01", "count": 45000, "avg_price": 52000},
      {"month": "2023-02", "count": 48000, "avg_price": 53500},
      {"month": "2023-03", "count": 52000, "avg_price": 54200}
    ]
  }
}
```

---

## 캐싱 정보

| 엔드포인트 | TTL | 설명 |
|-----------|-----|------|
| /statistics/rvol | 6시간 | RVOL 캐싱 |
| /statistics/quadrant | 6시간 | 4분면 분석 캐싱 |
| /statistics/hpi | 6시간 | HPI 캐싱 |
| /statistics/hpi/heatmap | 6시간 | 히트맵 캐싱 |
| /statistics/transaction-volume | 6시간 | 거래량 캐싱 |

### 캐시 예열

서버 시작 시 통계 캐시를 미리 계산합니다:

```python
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(precompute_all_statistics())
```

---

## 에러 코드

| HTTP 상태 | 코드 | 설명 |
|-----------|------|------|
| 400 | INVALID_REGION_TYPE | 잘못된 지역 유형 |
| 400 | CITY_NAME_REQUIRED | 도시명 필수 (지방5대광역시) |
| 404 | NO_DATA_AVAILABLE | 데이터 없음 |
| 500 | CALCULATION_ERROR | 통계 계산 오류 |
