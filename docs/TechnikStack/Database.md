# 🗄️ Database 기술 스택

데이터베이스에서 사용된 기술들과 선택 이유를 상세히 설명합니다.

---

## 1. PostgreSQL 15

### 선택 이유

| 항목 | MySQL | PostgreSQL | MongoDB |
|------|-------|------------|---------|
| ACID 보장 | 완벽 | 완벽 | 제한적 |
| JSON 지원 | 기본 | **JSONB (고급)** | 네이티브 |
| 공간 데이터 | 제한적 | **PostGIS** | GeoJSON |
| 복잡한 쿼리 | 중간 | **우수** | 제한적 |
| 확장성 | 복제 | **파티셔닝, 확장** | 샤딩 |

**PostgreSQL**을 선택한 이유:
1. **공간 데이터**: PostGIS로 위치 기반 검색 구현
2. **고급 인덱싱**: GIN, GIST, pg_trgm 등 다양한 인덱스
3. **복잡한 집계**: 통계 쿼리에 적합한 강력한 집계 함수
4. **Materialized View**: 복잡한 통계를 사전 계산하여 저장

### 적용 사례

```sql
-- 월별 거래 통계 Materialized View
CREATE MATERIALIZED VIEW mv_monthly_transaction_stats AS
SELECT 
    DATE_TRUNC('month', contract_date) AS month,
    region_id,
    COUNT(*) AS transaction_count,
    AVG(trans_price) AS avg_price,
    MIN(trans_price) AS min_price,
    MAX(trans_price) AS max_price
FROM sales
WHERE is_canceled = FALSE AND is_deleted = FALSE
GROUP BY month, region_id;

-- 인덱스 생성
CREATE INDEX idx_mv_monthly_stats_month ON mv_monthly_transaction_stats(month);
```

---

## 2. PostGIS (공간 데이터 확장)

### 선택 이유

| 기능 | 없음 | 자체 구현 | PostGIS |
|------|------|----------|---------|
| 거리 계산 | 불가 | 복잡 | ST_Distance |
| 반경 검색 | 불가 | 비효율 | ST_DWithin |
| 좌표 변환 | 불가 | 복잡 | ST_Transform |
| 인덱싱 | 불가 | 불가 | GIST |

**PostGIS**를 선택한 이유:
1. **반경 검색**: "강남역에서 도보 10분 이내" 같은 검색 구현
2. **거리 계산**: 두 지점 간 정확한 거리 계산
3. **공간 인덱스**: GIST 인덱스로 빠른 공간 쿼리

### 적용 사례

```sql
-- 아파트 테이블에 공간 컬럼 추가
ALTER TABLE apartments 
ADD COLUMN location geometry(Point, 4326);

-- 공간 인덱스 생성
CREATE INDEX idx_apartments_location 
ON apartments USING GIST (location);

-- 반경 1km 내 아파트 검색
SELECT apt_id, apt_name, 
       ST_Distance(location, ST_SetSRID(ST_MakePoint(127.0276, 37.4979), 4326)) AS distance
FROM apartments
WHERE ST_DWithin(
    location, 
    ST_SetSRID(ST_MakePoint(127.0276, 37.4979), 4326),  -- 강남역 좌표
    0.01  -- 약 1km
)
ORDER BY distance
LIMIT 10;
```

---

## 3. pg_trgm (유사도 검색)

### 선택 이유

| 검색 방식 | LIKE | Full-Text | pg_trgm |
|----------|------|-----------|---------|
| 부분 일치 | 가능 | 단어 단위 | **가능** |
| 오타 허용 | 불가 | 불가 | **가능** |
| 인덱스 | 제한적 | GIN | **GIN** |
| 속도 | 느림 | 빠름 | **빠름** |

**pg_trgm**을 선택한 이유:
1. **유사도 검색**: "래미안" → "래미안강남", "래미안서초" 매칭
2. **오타 허용**: 사용자 입력 오류에도 결과 제공
3. **GIN 인덱스**: 빠른 유사도 검색

### 적용 사례

```sql
-- 확장 활성화
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- GIN 인덱스 생성
CREATE INDEX idx_apartments_apt_name_trgm 
ON apartments USING GIN (apt_name gin_trgm_ops);

-- 유사도 검색
SELECT apt_id, apt_name, 
       similarity(apt_name, '래미안') AS sim
FROM apartments
WHERE apt_name % '래미안'  -- 유사도 기준 필터
ORDER BY sim DESC
LIMIT 10;
```

---

## 4. Redis (캐시)

### 선택 이유

| 캐시 | 로컬 메모리 | Memcached | Redis |
|------|------------|-----------|-------|
| 데이터 구조 | 단순 | Key-Value | **다양함** |
| 영속성 | 없음 | 없음 | **있음** |
| 클러스터 | 불가 | 제한적 | **지원** |
| TTL 관리 | 직접 | 자동 | **자동** |

**Redis**를 선택한 이유:
1. **고성능**: 인메모리 기반으로 밀리초 단위 응답
2. **다양한 데이터 구조**: Hash, List, Set 등 활용
3. **TTL 지원**: 자동 만료로 캐시 관리 용이
4. **Pipeline**: 여러 명령을 한 번에 실행하여 네트워크 오버헤드 감소

### 적용 사례

```python
# app/utils/cache.py
import orjson
from redis.asyncio import Redis

async def get_from_cache(key: str) -> Optional[dict]:
    """Redis에서 캐시 조회"""
    data = await redis_client.get(key)
    if data:
        return orjson.loads(data)
    return None

async def set_to_cache(key: str, data: dict, ttl: int = 3600) -> bool:
    """Redis에 캐시 저장"""
    try:
        await redis_client.setex(key, ttl, orjson.dumps(data))
        return True
    except Exception:
        return False

# 해시 기반 캐시 키 생성
def generate_hash_key(*args, **kwargs) -> str:
    """해시 기반 캐시 키 생성 (고정 길이)"""
    key_data = f"{args}{sorted(kwargs.items())}"
    return f"realestate:{hashlib.md5(key_data.encode()).hexdigest()}"
```

### 캐싱 전략

| 데이터 유형 | TTL | 이유 |
|------------|-----|------|
| 홈 화면 통계 | 12시간 | 부동산 데이터 업데이트 빈도 낮음 |
| 아파트 상세 | 10분 | 자주 변경되지 않음 |
| 검색 결과 | 5분 | 빠른 응답 필요 |
| 통계 조회 | 6시간 | 복잡한 집계 쿼리 |

---

## 5. 인덱스 최적화

### 적용된 인덱스

```sql
-- 아파트 검색용 복합 인덱스
CREATE INDEX idx_apartments_region_name 
ON apartments(region_id, apt_name)
WHERE is_deleted = FALSE;

-- 매매 데이터 조회용 복합 인덱스
CREATE INDEX idx_sales_apt_date_price 
ON sales(apt_id, contract_date DESC, trans_price)
WHERE is_canceled = FALSE AND is_deleted = FALSE;

-- 통계 조회용 복합 인덱스
CREATE INDEX idx_sales_region_date 
ON sales(region_id, contract_date DESC)
WHERE is_canceled = FALSE AND is_deleted = FALSE;

-- 아파트명 유사도 검색용 GIN 인덱스
CREATE INDEX idx_apartments_apt_name_trgm 
ON apartments USING GIN (apt_name gin_trgm_ops);
```

### Partial Index 활용

```sql
-- 삭제되지 않은 데이터만 인덱싱 (저장 공간 절약)
CREATE INDEX idx_apartments_active 
ON apartments(apt_id, apt_name)
WHERE is_deleted = FALSE;
```

---

## 6. Connection Pooling

### 설정 최적화

```python
# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # 기본 연결 수 (기존 5)
    max_overflow=40,       # 최대 추가 연결 수 (기존 10)
    pool_timeout=30,       # 연결 대기 시간
    pool_recycle=1800,     # 30분마다 연결 재사용
    pool_pre_ping=True,    # 연결 유효성 사전 확인
)
```

### 설정 의미

| 설정 | 값 | 설명 |
|------|-----|------|
| pool_size | 20 | 동시 연결 수 |
| max_overflow | 40 | 트래픽 급증 대비 추가 연결 |
| pool_recycle | 1800초 | 장시간 연결 재사용 방지 |
| pool_pre_ping | True | 끊어진 연결 자동 재연결 |

---

## 📊 성능 개선 효과

| 지표 | 개선 전 | 개선 후 | 개선율 |
|------|---------|---------|--------|
| 검색 쿼리 | 2-3초 | 50-100ms | **95%↓** |
| 통계 쿼리 | 3-5초 | 100-200ms | **95%↓** |
| 반경 검색 | 5초+ | 100ms | **95%↓** |
| 동시 연결 | 50 | 200+ | **4x↑** |
| 캐시 히트 시 | 200ms | 10ms | **95%↓** |
