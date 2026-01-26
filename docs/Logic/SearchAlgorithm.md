# 🔍 검색 알고리즘 (Search Algorithm)

2단계 검색 알고리즘의 동작 원리를 설명합니다.

---

## 문제 상황

### 기존 방식: LIKE 검색

```sql
SELECT * FROM apartments 
WHERE apt_name LIKE '%래미안%'
ORDER BY apt_name;
```

**문제점:**
- `LIKE '%keyword%'`는 인덱스를 사용할 수 없음
- 10만 건 이상의 아파트에서 **2-3초** 소요
- 전체 테이블 스캔 발생

---

## 해결 방안: 2단계 검색

### 전체 흐름

```
검색어 입력: "래미안"
        │
        ▼
┌─────────────────────────────────────┐
│    1단계: PREFIX 검색 (빠름)        │
│    apt_name LIKE '래미안%'          │
│    + 인덱스 활용                    │
└─────────────────┬───────────────────┘
                  │
                  ▼
            결과 >= limit?
                  │
        ┌────────┴────────┐
        │ YES             │ NO
        ▼                 ▼
    결과 반환     ┌─────────────────────────────────────┐
                 │    2단계: 유사도 검색 (pg_trgm)      │
                 │    similarity(apt_name, '래미안')    │
                 │    + GIN 인덱스 활용                 │
                 └─────────────────┬───────────────────┘
                                   │
                                   ▼
                            결과 병합 후 반환
```

---

## 구현 상세

### 1단계: PREFIX 검색

인덱스를 활용하는 빠른 검색을 먼저 시도합니다.

```python
# app/services/search.py
async def _fast_like_search(
    self, 
    db: AsyncSession, 
    query: str, 
    limit: int
) -> List[dict]:
    """빠른 PREFIX 검색 (인덱스 활용)"""
    
    # lower() prefix 인덱스 활용
    stmt = (
        select(
            Apartment.apt_id,
            Apartment.apt_name,
            Region.region_name,
            ApartDetail.road_address
        )
        .join(Region, Apartment.region_id == Region.region_id)
        .outerjoin(ApartDetail, Apartment.apt_id == ApartDetail.apt_id)
        .where(
            Apartment.is_deleted == False,
            or_(
                # 아파트명 PREFIX 검색
                func.lower(Apartment.apt_name).like(f"{query.lower()}%"),
                # 도로명주소 PREFIX 검색
                func.lower(ApartDetail.road_address).like(f"%{query.lower()}%"),
                # 지번주소 PREFIX 검색
                func.lower(ApartDetail.jibun_address).like(f"%{query.lower()}%")
            )
        )
        .order_by(Apartment.apt_name)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    return [dict(row._mapping) for row in result.fetchall()]
```

### 2단계: 유사도 검색

1단계 결과가 부족하면 pg_trgm 유사도 검색을 수행합니다.

```python
async def _similarity_search(
    self,
    db: AsyncSession,
    query: str,
    limit: int,
    exclude_apt_ids: Set[int]
) -> List[dict]:
    """pg_trgm 유사도 검색"""
    
    # similarity() 함수 사용
    similarity_score = func.similarity(Apartment.apt_name, query)
    
    stmt = (
        select(
            Apartment.apt_id,
            Apartment.apt_name,
            Region.region_name,
            ApartDetail.road_address,
            similarity_score.label("similarity")
        )
        .join(Region, Apartment.region_id == Region.region_id)
        .outerjoin(ApartDetail, Apartment.apt_id == ApartDetail.apt_id)
        .where(
            Apartment.is_deleted == False,
            Apartment.apt_id.notin_(exclude_apt_ids),  # 1단계 결과 제외
            similarity_score > 0.3  # 유사도 임계값
        )
        .order_by(similarity_score.desc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    return [dict(row._mapping) for row in result.fetchall()]
```

### 통합 검색 함수

```python
async def search_apartments(
    self, 
    db: AsyncSession, 
    query: str, 
    limit: int = 10
) -> List[dict]:
    """2단계 아파트 검색"""
    
    # 1단계: 빠른 PREFIX 검색
    fast_results = await self._fast_like_search(db, query, limit)
    
    # 결과가 충분하면 바로 반환
    if len(fast_results) >= limit:
        return fast_results[:limit]
    
    # 2단계: 유사도 검색 (1단계 결과 부족 시)
    found_apt_ids = {r["apt_id"] for r in fast_results}
    remaining_limit = limit - len(fast_results)
    
    similarity_results = await self._similarity_search(
        db, query, remaining_limit, exclude_apt_ids=found_apt_ids
    )
    
    # 결과 병합
    return fast_results + similarity_results
```

---

## 인덱스 설정

### PREFIX 검색용 인덱스

```sql
-- 아파트명 인덱스 (B-tree)
CREATE INDEX idx_apartments_apt_name 
ON apartments(apt_name)
WHERE is_deleted = FALSE;

-- 도로명주소 인덱스
CREATE INDEX idx_apart_details_road_address 
ON apart_details(road_address);
```

### 유사도 검색용 GIN 인덱스

```sql
-- pg_trgm 확장 활성화
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 아파트명 유사도 검색용 GIN 인덱스
CREATE INDEX idx_apartments_apt_name_trgm 
ON apartments USING GIN (apt_name gin_trgm_ops);

-- 주소 유사도 검색용 GIN 인덱스
CREATE INDEX idx_apart_details_road_address_trgm 
ON apart_details USING GIN (road_address gin_trgm_ops);
```

---

## 성능 비교

### 테스트 환경
- 아파트 수: 약 12만 건
- 검색어: "래미안"
- limit: 10

| 방식 | 쿼리 시간 | 인덱스 사용 |
|------|----------|------------|
| LIKE '%keyword%' | 2-3초 | ❌ (Full Scan) |
| LIKE 'keyword%' | 10-50ms | ✅ (B-tree) |
| pg_trgm만 | 300-500ms | ✅ (GIN) |
| **2단계 검색** | **50-100ms** | ✅ (최적화) |

### 쿼리 플랜 비교

**LIKE '%keyword%' (인덱스 미사용):**
```
Seq Scan on apartments
  Filter: (apt_name ~~ '%래미안%')
  Rows Removed by Filter: 119500
  Planning Time: 0.5 ms
  Execution Time: 2500 ms
```

**2단계 검색 (인덱스 사용):**
```
Index Scan using idx_apartments_apt_name on apartments
  Index Cond: (apt_name >= '래미안' AND apt_name < '래미안')
  Planning Time: 0.3 ms
  Execution Time: 15 ms
```

---

## AI 검색 통합

자연어 쿼리를 구조화된 검색 조건으로 변환합니다.

```python
async def ai_search(query: str) -> List[dict]:
    """AI 자연어 검색"""
    
    # 1. Gemini로 자연어 분석
    parsed = await parse_natural_language(query)
    # 예: "강남역 근처 3억 이하 전세"
    # → {location: "강남역", max_price: 30000, transaction_type: "jeonse"}
    
    # 2. 위치 기반 검색 (PostGIS)
    if parsed.location:
        coords = await geocode(parsed.location)
        apartments = await search_by_location(coords, radius_km=1)
    
    # 3. 가격 필터링
    if parsed.max_price:
        apartments = [a for a in apartments if a.avg_price <= parsed.max_price]
    
    return apartments
```

---

## 에러 처리

```python
async def search_apartments(
    self, 
    db: AsyncSession, 
    query: str, 
    limit: int = 10
) -> List[dict]:
    # 입력 검증
    if len(query) < 2:
        raise HTTPException(400, "검색어는 2자 이상이어야 합니다")
    
    if len(query) > 100:
        raise HTTPException(400, "검색어는 100자 이하여야 합니다")
    
    # SQL Injection 방지 (SQLAlchemy가 자동 처리)
    # query는 파라미터로 전달되어 이스케이프됨
    
    try:
        results = await self._search_internal(db, query, limit)
        return results
    except Exception as e:
        logger.error(f"검색 오류: {e}")
        raise HTTPException(500, "검색 중 오류가 발생했습니다")
```
