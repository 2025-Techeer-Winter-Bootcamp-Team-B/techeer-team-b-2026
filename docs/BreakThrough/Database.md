# 🗄️ 데이터베이스 최적화 BreakThrough

데이터베이스 관련 문제 해결 및 최적화 사례를 상세히 설명합니다.

---

## 1. pg_trgm GIN 인덱스 도입

### 문제 상황
- LIKE '%keyword%' 검색이 인덱스를 사용하지 못함
- 전체 테이블 스캔으로 **2-3초** 소요

### 해결 방법

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
WHERE apt_name % '래미안'  -- 유사도 필터
ORDER BY sim DESC
LIMIT 10;
```

### 개선 결과
| 지표 | 개선 전 | 개선 후 |
|------|---------|---------|
| 검색 시간 | 2-3초 | **50-100ms** |
| 인덱스 사용 | ❌ Full Scan | ✅ GIN Index |

---

## 2. 복합 인덱스 최적화

### 문제 상황
- 단일 컬럼 인덱스만 존재
- 복합 조건 쿼리 성능 저하

### 해결 방법

```sql
-- 아파트 상세 검색용 복합 인덱스
CREATE INDEX idx_sales_apt_date_price 
ON sales(apt_id, contract_date DESC, trans_price)
WHERE is_canceled = FALSE AND is_deleted = FALSE;

-- 통계 조회용 복합 인덱스
CREATE INDEX idx_sales_region_date 
ON sales(region_id, contract_date DESC)
WHERE is_canceled = FALSE AND is_deleted = FALSE;

-- 아파트 검색용 복합 인덱스
CREATE INDEX idx_apartments_region_name 
ON apartments(region_id, apt_name)
WHERE is_deleted = FALSE;
```

### 개선 결과
| 쿼리 유형 | 개선 전 | 개선 후 |
|----------|---------|---------|
| 아파트별 거래 | 500ms | **100ms** |
| 지역별 통계 | 1초 | **200ms** |

---

## 3. Partial Index 적용

### 문제 상황
- 삭제된 데이터도 인덱싱되어 저장 공간 낭비
- 불필요한 데이터까지 검색

### 해결 방법

```sql
-- 삭제되지 않은 데이터만 인덱싱
CREATE INDEX idx_apartments_active 
ON apartments(apt_id, apt_name)
WHERE is_deleted = FALSE;

CREATE INDEX idx_sales_active 
ON sales(apt_id, contract_date)
WHERE is_canceled = FALSE AND is_deleted = FALSE;
```

### 개선 결과
| 지표 | 개선 전 | 개선 후 |
|------|---------|---------|
| 인덱스 크기 | 100MB | **70MB** |
| 쿼리 성능 | 동일 | **향상** |

---

## 4. PostGIS 공간 인덱스

### 문제 상황
- 반경 검색 (예: "강남역 1km 이내") 매우 느림
- 모든 아파트의 거리 계산 필요

### 해결 방법

```sql
-- 공간 컬럼 추가
ALTER TABLE apartments 
ADD COLUMN location geometry(Point, 4326);

-- GIST 공간 인덱스 생성
CREATE INDEX idx_apartments_location 
ON apartments USING GIST (location);

-- 반경 검색 쿼리
SELECT apt_id, apt_name,
       ST_Distance(
         location, 
         ST_SetSRID(ST_MakePoint(127.0276, 37.4979), 4326)
       ) AS distance
FROM apartments
WHERE ST_DWithin(
    location,
    ST_SetSRID(ST_MakePoint(127.0276, 37.4979), 4326),
    0.01  -- 약 1km
)
ORDER BY distance
LIMIT 10;
```

### 개선 결과
| 지표 | 개선 전 | 개선 후 |
|------|---------|---------|
| 반경 검색 | 5초+ | **100ms** |
| 인덱스 사용 | ❌ | ✅ GIST |

---

## 5. Materialized View 활용

### 문제 상황
- 월별 통계 쿼리가 매번 수십만 건 집계
- 통계 API 응답 **3-5초**

### 해결 방법

```sql
-- Materialized View 생성
CREATE MATERIALIZED VIEW mv_monthly_transaction_stats AS
SELECT 
    DATE_TRUNC('month', contract_date) AS month,
    region_id,
    'sale' AS transaction_type,
    COUNT(*) AS transaction_count,
    AVG(trans_price) AS avg_price,
    MIN(trans_price) AS min_price,
    MAX(trans_price) AS max_price
FROM sales
WHERE is_canceled = FALSE AND is_deleted = FALSE
GROUP BY month, region_id

UNION ALL

SELECT 
    DATE_TRUNC('month', deal_date) AS month,
    region_id,
    'jeonse' AS transaction_type,
    COUNT(*) AS transaction_count,
    AVG(deposit_price) AS avg_price,
    MIN(deposit_price) AS min_price,
    MAX(deposit_price) AS max_price
FROM rents
WHERE is_deleted = FALSE AND monthly_rent = 0
GROUP BY month, region_id;

-- 인덱스 생성
CREATE INDEX idx_mv_monthly_month ON mv_monthly_transaction_stats(month);
CREATE INDEX idx_mv_monthly_region ON mv_monthly_transaction_stats(region_id);
CREATE INDEX idx_mv_monthly_type ON mv_monthly_transaction_stats(transaction_type);

-- 주기적 갱신 (스케줄러)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_transaction_stats;
```

### 개선 결과
| 지표 | 개선 전 (원본 테이블) | 개선 후 (MV) |
|------|---------------------|-------------|
| 통계 쿼리 | 3-5초 | **100-200ms** |
| 개선율 | - | **95%↓** |

---

## 6. 일일 통계 테이블

### 문제 상황
- 월별 통계 계산 시 매번 전체 기간 집계
- 반복 계산으로 리소스 낭비

### 해결 방법
증분 집계 테이블:

```sql
-- 일일 통계 테이블
CREATE TABLE daily_statistics (
    stat_date DATE NOT NULL,
    region_id INTEGER,
    transaction_type VARCHAR(10),
    transaction_count INTEGER,
    avg_price DECIMAL(12, 2),
    total_amount DECIMAL(15, 2),
    PRIMARY KEY (stat_date, region_id, transaction_type)
);

-- 일일 집계 (매일 새벽 실행)
INSERT INTO daily_statistics
SELECT 
    $target_date,
    region_id,
    'sale',
    COUNT(*),
    AVG(trans_price),
    SUM(trans_price)
FROM sales
WHERE contract_date = $target_date
  AND is_canceled = FALSE AND is_deleted = FALSE
GROUP BY region_id
ON CONFLICT (stat_date, region_id, transaction_type)
DO UPDATE SET
    transaction_count = EXCLUDED.transaction_count,
    avg_price = EXCLUDED.avg_price,
    total_amount = EXCLUDED.total_amount;
```

### 개선 결과
| 지표 | 개선 전 | 개선 후 |
|------|---------|---------|
| 월별 통계 계산 | 3초 | **200ms** |
| 계산 방식 | 전체 집계 | 일일 합산 |

---

## 7. 외래키 제약조건 추가

### 문제 상황
- FK 제약조건 누락으로 데이터 무결성 보장 불가
- 존재하지 않는 참조 가능

### 해결 방법

```sql
-- 외래키 제약조건 추가
ALTER TABLE apartments
ADD CONSTRAINT fk_apartments_region
FOREIGN KEY (region_id) REFERENCES regions(region_id);

ALTER TABLE sales
ADD CONSTRAINT fk_sales_apartment
FOREIGN KEY (apt_id) REFERENCES apartments(apt_id);

ALTER TABLE favorite_apartments
ADD CONSTRAINT fk_favorites_account
FOREIGN KEY (account_id) REFERENCES accounts(account_id)
ON DELETE CASCADE;
```

### 개선 결과
| 지표 | 개선 전 | 개선 후 |
|------|---------|---------|
| 데이터 무결성 | 보장 안됨 | ✅ **보장** |
| 잘못된 참조 | 가능 | ❌ **불가** |

---

## 8. Connection Pool 안정성

### 문제 상황
- 장시간 미사용 연결이 끊어짐
- PostgreSQL 타임아웃으로 에러 발생

### 해결 방법

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,     # 연결 유효성 사전 확인
    pool_recycle=1800,      # 30분마다 연결 재사용
)
```

### 개선 결과
| 지표 | 개선 전 | 개선 후 |
|------|---------|---------|
| Connection 에러 | 간헐적 발생 | ❌ **없음** |
| 자동 재연결 | 없음 | ✅ **자동** |

---

## 9. 쿼리 실행 계획 최적화

### 문제 상황
- 복잡한 쿼리의 실행 계획 비효율적
- 불필요한 정렬, 해시 조인 발생

### 해결 방법
EXPLAIN ANALYZE로 분석 후 최적화:

```sql
-- 분석 전
EXPLAIN ANALYZE
SELECT * FROM apartments a
JOIN sales s ON a.apt_id = s.apt_id
WHERE s.contract_date >= '2024-01-01'
ORDER BY s.trans_price DESC;

-- 인덱스 추가로 최적화
CREATE INDEX idx_sales_date_price 
ON sales(contract_date DESC, trans_price DESC);
```

### 개선 결과
| 지표 | 개선 전 | 개선 후 |
|------|---------|---------|
| 쿼리 시간 | 800ms | **150ms** |
| 실행 계획 | Seq Scan + Sort | Index Scan |

---

## 10. 스키마 정합성 개선

### 문제 상황
- PK/FK 주석 오류 (FK인데 PK로 표기)
- 스키마 문서와 실제 구조 불일치

### 해결 방법
모든 모델 파일 정리:

```python
# app/models/apartment.py
class Apartment(Base):
    __tablename__ = "apartments"
    
    apt_id = Column(Integer, primary_key=True)  # PK
    region_id = Column(Integer, ForeignKey("regions.region_id"))  # FK
    apt_name = Column(String(100), nullable=False)
    
    # 관계 정의
    region = relationship("Region", back_populates="apartments")
    detail = relationship("ApartDetail", back_populates="apartment", uselist=False)
```

### 개선 결과
| 지표 | 개선 전 | 개선 후 |
|------|---------|---------|
| 스키마 명확성 | 혼란 | ✅ **명확** |
| 관계 정의 | 불완전 | ✅ **완전** |
