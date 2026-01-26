# 🗃️ 캐싱 전략 (Cache Strategy)

Redis 기반 캐싱 전략과 구현 방법을 설명합니다.

---

## 캐싱 개요

### 캐싱 목표

1. **응답 속도 향상**: DB 쿼리 대신 캐시에서 즉시 응답
2. **DB 부하 감소**: 반복 쿼리 제거
3. **Cold Start 방지**: 서버 시작 시 주요 데이터 사전 캐싱

### 캐싱 흐름

```
요청 수신
    │
    ▼
┌─────────────────────┐
│    캐시 키 생성      │
│    (해시 기반)       │
└─────────┬───────────┘
          │
          ▼
      캐시 조회
          │
    ┌─────┴─────┐
    │           │
   HIT        MISS
    │           │
    ▼           ▼
캐시 반환    DB 쿼리
              │
              ▼
         캐시 저장
              │
              ▼
          응답 반환
```

---

## 캐시 키 설계

### 해시 기반 캐시 키

파라미터가 많아도 고정 길이의 키를 생성합니다.

```python
# app/utils/cache.py
import hashlib
import orjson

def generate_hash_key(*args, **kwargs) -> str:
    """해시 기반 캐시 키 생성"""
    key_data = orjson.dumps({
        "args": args,
        "kwargs": sorted(kwargs.items())
    })
    hash_value = hashlib.md5(key_data).hexdigest()
    return f"realestate:{hash_value}"
```

**예시:**
```python
key = generate_hash_key(
    "statistics", "rvol",
    region_type="전국",
    transaction_type="sale",
    period_months=3
)
# → "realestate:a1b2c3d4e5f6..."
```

### 계층적 캐시 키

```python
def build_cache_key(*parts: str) -> str:
    """계층적 캐시 키 생성"""
    return "realestate:" + ":".join(str(p) for p in parts)
```

**예시:**
```python
key = build_cache_key("apartment", "12345", "detail")
# → "realestate:apartment:12345:detail"
```

---

## TTL 전략

### 데이터 유형별 TTL

| 데이터 유형 | TTL | 이유 |
|------------|-----|------|
| 홈 화면 (예열) | 12시간 | 부동산 데이터 업데이트 빈도 낮음 |
| 통계 데이터 | 6시간 | 복잡한 집계, 자주 변하지 않음 |
| 아파트 상세 | 10분 | 자주 변경되지 않음 |
| 검색 결과 | 5분 | 빠른 응답 필요 |
| 세션 데이터 | 1시간 | 보안상 짧게 유지 |

### TTL 상수 정의

```python
# app/core/config.py
class CacheSettings:
    HOME_PRELOAD_TTL = 43200    # 12시간
    STATISTICS_TTL = 21600      # 6시간
    APARTMENT_DETAIL_TTL = 600  # 10분
    SEARCH_RESULT_TTL = 300     # 5분
    SESSION_TTL = 3600          # 1시간
```

---

## 캐시 구현

### 기본 캐시 함수

```python
# app/utils/cache.py
from redis.asyncio import Redis
import orjson
from typing import Optional, Any

redis_client: Optional[Redis] = None

async def get_redis_client() -> Redis:
    """Redis 클라이언트 초기화"""
    global redis_client
    if redis_client is None:
        redis_client = Redis.from_url(settings.REDIS_URL)
    return redis_client

async def get_from_cache(key: str) -> Optional[Any]:
    """캐시에서 데이터 조회"""
    client = await get_redis_client()
    data = await client.get(key)
    if data:
        return orjson.loads(data)
    return None

async def set_to_cache(key: str, data: Any, ttl: int = 3600) -> bool:
    """캐시에 데이터 저장"""
    client = await get_redis_client()
    try:
        await client.setex(key, ttl, orjson.dumps(data))
        return True
    except Exception as e:
        logger.warning(f"캐시 저장 실패: {e}")
        return False

async def delete_from_cache(key: str) -> bool:
    """캐시에서 데이터 삭제"""
    client = await get_redis_client()
    await client.delete(key)
    return True

async def delete_cache_pattern(pattern: str) -> int:
    """패턴 매칭으로 캐시 일괄 삭제"""
    client = await get_redis_client()
    cursor = 0
    deleted = 0
    
    while True:
        cursor, keys = await client.scan(cursor, match=pattern, count=100)
        if keys:
            await client.delete(*keys)
            deleted += len(keys)
        if cursor == 0:
            break
    
    return deleted
```

---

## 캐시 예열 (Cache Warmup)

### 서버 시작 시 캐시 예열

```python
# app/main.py
@app.on_event("startup")
async def startup_event():
    # Redis 연결 초기화
    await get_redis_client()
    
    # 백그라운드로 캐시 예열 (서버 시작 블로킹 없음)
    asyncio.create_task(preload_all_caches())

async def preload_all_caches():
    """모든 캐시 예열"""
    try:
        # 1. 홈 화면 캐시
        await preload_home_cache()
        
        # 2. 통계 캐시
        await preload_statistics_cache()
        
        logger.info("✅ 캐시 예열 완료")
    except Exception as e:
        logger.error(f"❌ 캐시 예열 실패: {e}")
```

### 홈 화면 캐시 예열

```python
# app/services/warmup.py
async def preload_home_cache():
    """홈 화면 캐시 예열"""
    PRELOAD_TTL = 43200  # 12시간
    
    cache_tasks = [
        # 대시보드 요약
        ("dashboard/summary", {"transaction_type": "sale", "months": 6}),
        ("dashboard/summary", {"transaction_type": "jeonse", "months": 6}),
        # 랭킹
        ("dashboard/rankings", {"transaction_type": "sale"}),
        ("dashboard/rankings", {"transaction_type": "jeonse"}),
    ]
    
    async with AsyncSessionLocal() as db:
        for endpoint, params in cache_tasks:
            try:
                # 데이터 조회
                data = await fetch_dashboard_data(db, endpoint, params)
                
                # 캐시 저장
                cache_key = generate_hash_key(endpoint, **params)
                await set_to_cache(cache_key, data, ttl=PRELOAD_TTL)
                
                logger.info(f"✅ {endpoint} 캐싱 완료")
            except Exception as e:
                logger.error(f"❌ {endpoint} 캐싱 실패: {e}")
```

### 통계 캐시 예열

```python
async def preload_statistics_cache():
    """통계 캐시 예열"""
    region_types = ["전국", "수도권", "지방5대광역시"]
    transaction_types = ["sale", "jeonse"]
    max_years_options = [1, 3, 5, 10]
    
    async with AsyncSessionLocal() as db:
        for region_type in region_types:
            for transaction_type in transaction_types:
                for max_years in max_years_options:
                    # RVOL 캐싱
                    await cache_rvol(db, region_type, transaction_type)
                    
                    # 거래량 추이 캐싱
                    await cache_transaction_volume(
                        db, region_type, transaction_type, max_years
                    )
```

---

## 캐시 무효화

### 데이터 업데이트 시 캐시 무효화

```python
# app/services/cache_invalidation.py
async def invalidate_apartment_cache(apt_id: int):
    """아파트 관련 캐시 무효화"""
    patterns = [
        f"realestate:apartment:{apt_id}:*",
        f"realestate:*:apt:{apt_id}:*",
    ]
    
    for pattern in patterns:
        deleted = await delete_cache_pattern(pattern)
        logger.debug(f"캐시 삭제: {pattern}, {deleted}건")

async def invalidate_statistics_cache(
    region_id: Optional[int] = None,
    transaction_type: Optional[str] = None
):
    """통계 캐시 무효화"""
    patterns = []
    
    if region_id:
        patterns.append(f"realestate:statistics:*:region:{region_id}:*")
    
    if transaction_type:
        patterns.append(f"realestate:statistics:*:type:{transaction_type}:*")
    
    for pattern in patterns:
        await delete_cache_pattern(pattern)
```

### 스케줄러 기반 갱신

```python
# app/services/statistics_cache_scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def start_statistics_scheduler():
    """통계 캐시 스케줄러 시작"""
    
    # 매일 새벽 2시에 통계 캐시 갱신
    scheduler.add_job(
        precompute_all_statistics,
        trigger="cron",
        hour=2,
        minute=0
    )
    
    scheduler.start()
    logger.info("통계 캐시 스케줄러 시작됨")
```

---

## 성능 측정

### 캐시 히트율 모니터링

```python
import prometheus_client as prom

cache_hits = prom.Counter("cache_hits_total", "Total cache hits")
cache_misses = prom.Counter("cache_misses_total", "Total cache misses")

async def get_from_cache_with_metrics(key: str) -> Optional[Any]:
    data = await get_from_cache(key)
    if data:
        cache_hits.inc()
    else:
        cache_misses.inc()
    return data
```

### 성능 개선 효과

| 지표 | 캐시 없음 | 캐시 적용 |
|------|----------|----------|
| 통계 API 응답 | 3-5초 | **50-100ms** |
| 첫 요청 (Cold) | 5초+ | **100ms (예열 후)** |
| DB 쿼리 수 | 100회/분 | **10회/분** |
| 캐시 히트율 | 0% | **80%+** |
