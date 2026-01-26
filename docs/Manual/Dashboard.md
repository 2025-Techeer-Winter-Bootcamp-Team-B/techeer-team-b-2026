# 📈 대시보드 API (Dashboard)

홈 화면에 표시되는 대시보드 데이터 API를 설명합니다.

---

## 개요

홈 화면에서 사용자에게 보여주는 핵심 지표들을 제공합니다:

- **요약 데이터**: 거래량, 평균 가격, 변화율
- **지역별 랭킹**: 거래량/가격 기준 지역 순위

---

## API 엔드포인트

### 1. 대시보드 요약

홈 화면의 주요 지표를 반환합니다.

**요청**

```http
GET /api/v1/dashboard/summary
Authorization: Bearer <jwt_token>
```

**쿼리 파라미터**

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| transaction_type | string | sale | sale, jeonse |
| months | int | 6 | 조회 기간 (개월) |

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "transaction_type": "sale",
    "period_months": 6,
    "summary": {
      "total_transactions": 285000,
      "avg_price": 52000,
      "price_change_rate": 3.5,
      "volume_change_rate": 12.3
    },
    "monthly_trend": [
      {"month": "2023-08", "count": 45000, "avg_price": 50000},
      {"month": "2023-09", "count": 47000, "avg_price": 50500},
      {"month": "2023-10", "count": 48500, "avg_price": 51200},
      {"month": "2023-11", "count": 46000, "avg_price": 51800},
      {"month": "2023-12", "count": 49000, "avg_price": 52000},
      {"month": "2024-01", "count": 49500, "avg_price": 52000}
    ],
    "top_regions": [
      {
        "region_name": "서울특별시 강남구",
        "transaction_count": 1200,
        "avg_price": 180000
      },
      {
        "region_name": "경기도 성남시 분당구",
        "transaction_count": 980,
        "avg_price": 120000
      }
    ]
  }
}
```

**응답 필드**

| 필드 | 타입 | 설명 |
|------|------|------|
| total_transactions | int | 기간 내 총 거래 건수 |
| avg_price | int | 평균 거래가 (만원) |
| price_change_rate | float | 가격 변화율 (%) |
| volume_change_rate | float | 거래량 변화율 (%) |
| monthly_trend | array | 월별 거래 추이 |
| top_regions | array | 상위 거래 지역 |

---

### 2. 지역별 랭킹

거래량 또는 가격 기준으로 지역 순위를 반환합니다.

**요청**

```http
GET /api/v1/dashboard/rankings
Authorization: Bearer <jwt_token>
```

**쿼리 파라미터**

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| transaction_type | string | sale | sale, jeonse |
| rank_by | string | volume | volume, price |
| limit | int | 10 | 결과 수 |

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "transaction_type": "sale",
    "rank_by": "volume",
    "rankings": [
      {
        "rank": 1,
        "region_name": "서울특별시 강남구",
        "transaction_count": 1200,
        "avg_price": 180000,
        "change_rate": 5.2
      },
      {
        "rank": 2,
        "region_name": "경기도 성남시 분당구",
        "transaction_count": 980,
        "avg_price": 120000,
        "change_rate": 3.8
      },
      {
        "rank": 3,
        "region_name": "서울특별시 송파구",
        "transaction_count": 920,
        "avg_price": 150000,
        "change_rate": 4.1
      }
    ]
  }
}
```

---

### 3. 최신 뉴스

부동산 관련 최신 뉴스를 반환합니다.

**요청**

```http
GET /api/v1/dashboard/news
Authorization: Bearer <jwt_token>
```

**쿼리 파라미터**

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| limit | int | 5 | 결과 수 |
| category | string | all | all, policy, market, analysis |

**응답 (200 OK)**

```json
{
  "success": true,
  "data": {
    "news": [
      {
        "news_id": 1,
        "title": "서울 아파트 거래량 3개월 연속 증가",
        "summary": "서울 아파트 매매 거래량이 3개월 연속 증가세를 보이고 있다...",
        "source": "한국경제",
        "published_at": "2024-01-15T09:00:00Z",
        "url": "https://example.com/news/12345",
        "category": "market"
      }
    ]
  }
}
```

---

## 캐싱 정보

### 서버 시작 시 캐시 예열

홈 화면은 가장 많이 접근되는 페이지이므로, 서버 시작 시 캐시를 미리 준비합니다.

| 엔드포인트 | TTL (일반) | TTL (예열) |
|-----------|-----------|-----------|
| /dashboard/summary (sale) | 30분 | **12시간** |
| /dashboard/summary (jeonse) | 30분 | **12시간** |
| /dashboard/rankings (sale) | 30분 | **12시간** |
| /dashboard/rankings (jeonse) | 30분 | **12시간** |

### 캐시 예열 코드

```python
@app.on_event("startup")
async def startup_event():
    # Redis 연결 초기화 후
    asyncio.create_task(preload_home_cache())

async def preload_home_cache():
    """홈 화면 캐시 미리 로드"""
    PRELOAD_TTL = 43200  # 12시간
    
    cache_tasks = [
        ("summary", {"transaction_type": "sale", "months": 6}),
        ("summary", {"transaction_type": "jeonse", "months": 6}),
        ("rankings", {"transaction_type": "sale"}),
        ("rankings", {"transaction_type": "jeonse"}),
    ]
    
    for endpoint, params in cache_tasks:
        data = await fetch_dashboard_data(endpoint, params)
        await cache_data(endpoint, params, data, ttl=PRELOAD_TTL)
```

---

## Cold Start 문제 해결

### 문제

서버 재시작 후 첫 요청이 3-5초 소요됨.

### 원인

복잡한 통계 쿼리를 실행해야 함.

### 해결

서버 시작 시 백그라운드로 캐시 예열:

```python
@app.on_event("startup")
async def startup_event():
    await get_redis_client()
    # 백그라운드 태스크로 실행 (서버 시작 블로킹 없음)
    asyncio.create_task(preload_home_cache())
```

### 효과

| 지표 | 개선 전 | 개선 후 |
|------|---------|---------|
| 첫 요청 응답 시간 | 3-5초 | 50-100ms |
| 캐시 미스 시 | 100% | 0% (예열 후) |

---

## 에러 코드

| HTTP 상태 | 코드 | 설명 |
|-----------|------|------|
| 400 | INVALID_TRANSACTION_TYPE | 잘못된 거래 유형 |
| 400 | INVALID_RANK_BY | 잘못된 정렬 기준 |
| 404 | NO_DATA_AVAILABLE | 데이터 없음 |
| 500 | CALCULATION_ERROR | 통계 계산 오류 |
