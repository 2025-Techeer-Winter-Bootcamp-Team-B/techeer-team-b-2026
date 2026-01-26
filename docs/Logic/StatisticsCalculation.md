# 📊 통계 계산 로직 (Statistics Calculation)

RVOL, 4분면 분석 등 통계 계산 로직을 설명합니다.

---

## 1. RVOL (상대 거래량)

### 개념

RVOL(Relative Volume)은 현재 거래량을 과거 평균과 비교하여 시장 활성도를 측정합니다.

```
RVOL = 현재 거래량 / 과거 N개월 평균 거래량
```

### 계산 로직

```python
async def calculate_rvol(
    db: AsyncSession,
    region_type: str,
    transaction_type: str,
    period_months: int = 3
) -> RVOLResponse:
    """RVOL 계산"""
    
    # 1. 현재 월 거래량
    current_month = datetime.now().replace(day=1)
    current_volume = await get_transaction_count(
        db, region_type, transaction_type,
        start_date=current_month
    )
    
    # 2. 과거 N개월 평균 거래량
    past_volumes = []
    for i in range(1, period_months + 1):
        month_start = current_month - relativedelta(months=i)
        month_end = month_start + relativedelta(months=1) - timedelta(days=1)
        
        volume = await get_transaction_count(
            db, region_type, transaction_type,
            start_date=month_start, end_date=month_end
        )
        past_volumes.append(volume)
    
    average_volume = sum(past_volumes) / len(past_volumes) if past_volumes else 0
    
    # 3. RVOL 계산
    if average_volume > 0:
        rvol = current_volume / average_volume
    else:
        rvol = 0
    
    # 4. 신호 판정
    signal = get_rvol_signal(rvol)
    
    return RVOLResponse(
        region_type=region_type,
        transaction_type=transaction_type,
        current_volume=current_volume,
        average_volume=int(average_volume),
        rvol=round(rvol, 2),
        signal=signal
    )

def get_rvol_signal(rvol: float) -> str:
    """RVOL 신호 판정"""
    if rvol > 1.5:
        return "거래 급증"
    elif rvol > 1.0:
        return "거래 활발"
    elif rvol > 0.7:
        return "보통"
    else:
        return "거래 위축"
```

### 신호 해석

| RVOL 범위 | 신호 | 시장 상황 |
|-----------|------|----------|
| > 1.5 | 거래 급증 | 시장 과열 가능성, 주의 필요 |
| 1.0 ~ 1.5 | 거래 활발 | 정상적인 활성화 상태 |
| 0.7 ~ 1.0 | 보통 | 평균 수준 |
| < 0.7 | 거래 위축 | 시장 침체, 관망세 |

---

## 2. 4분면 분석 (Quadrant Analysis)

### 개념

매매가 변화율과 전세가 변화율을 기준으로 시장을 4개 분면으로 분류합니다.

```
         전세 상승 (+)
              │
    2분면     │     4분면
  (임대 선호) │   (활성화)
              │
──────────────┼────────────── 매매 변화율
  매매 하락   │   매매 상승
    (-)       │     (+)
              │
    3분면     │     1분면
  (시장 위축) │  (매수 전환)
              │
         전세 하락 (-)
```

### 계산 로직

```python
async def calculate_quadrant(
    db: AsyncSession,
    period_months: int = 6
) -> QuadrantResponse:
    """4분면 분석"""
    
    # 1. 기간 설정
    end_date = datetime.now()
    start_date = end_date - relativedelta(months=period_months)
    mid_date = end_date - relativedelta(months=period_months // 2)
    
    # 2. 매매가 변화율 계산
    sale_start_avg = await get_avg_price(db, "sale", start_date, mid_date)
    sale_end_avg = await get_avg_price(db, "sale", mid_date, end_date)
    
    if sale_start_avg > 0:
        sale_change_rate = ((sale_end_avg - sale_start_avg) / sale_start_avg) * 100
    else:
        sale_change_rate = 0
    
    # 3. 전세가 변화율 계산
    jeonse_start_avg = await get_avg_price(db, "jeonse", start_date, mid_date)
    jeonse_end_avg = await get_avg_price(db, "jeonse", mid_date, end_date)
    
    if jeonse_start_avg > 0:
        jeonse_change_rate = ((jeonse_end_avg - jeonse_start_avg) / jeonse_start_avg) * 100
    else:
        jeonse_change_rate = 0
    
    # 4. 분면 결정
    quadrant = determine_quadrant(sale_change_rate, jeonse_change_rate)
    
    return QuadrantResponse(
        quadrant=quadrant.number,
        quadrant_name=quadrant.name,
        sale_change_rate=round(sale_change_rate, 2),
        jeonse_change_rate=round(jeonse_change_rate, 2),
        analysis=quadrant.analysis
    )

def determine_quadrant(
    sale_rate: float, 
    jeonse_rate: float
) -> Quadrant:
    """분면 결정"""
    
    if sale_rate > 0 and jeonse_rate < 0:
        return Quadrant(
            number=1,
            name="매수 전환",
            analysis="매매가 상승, 전세가 하락. 전세 수요가 매수로 전환되는 신호"
        )
    elif sale_rate < 0 and jeonse_rate > 0:
        return Quadrant(
            number=2,
            name="임대 선호",
            analysis="매매가 하락, 전세가 상승. 매수보다 임대를 선호하는 시장"
        )
    elif sale_rate < 0 and jeonse_rate < 0:
        return Quadrant(
            number=3,
            name="시장 위축",
            analysis="매매가와 전세가 모두 하락. 전반적인 시장 침체"
        )
    else:  # sale_rate > 0 and jeonse_rate > 0
        return Quadrant(
            number=4,
            name="활성화",
            analysis="매매가와 전세가 모두 상승. 수요 증가로 인한 시장 활성화"
        )
```

### 분면별 해석

| 분면 | 조건 | 의미 | 투자 전략 |
|------|------|------|----------|
| 1분면 | 매매↑, 전세↓ | 매수 전환 | 매수 타이밍 검토 |
| 2분면 | 매매↓, 전세↑ | 임대 선호 | 전세 투자 유리 |
| 3분면 | 매매↓, 전세↓ | 시장 위축 | 관망 권장 |
| 4분면 | 매매↑, 전세↑ | 활성화 | 신중한 진입 |

---

## 3. HPI (주택가격지수)

### 개념

기준 시점(2021-01) 대비 현재 주택 가격의 상대적 수준을 100을 기준으로 표시합니다.

### 계산 로직

```python
async def calculate_hpi(
    db: AsyncSession,
    region_type: str,
    index_type: str,  # sale or jeonse
    max_years: int = 5
) -> HPIResponse:
    """HPI 계산"""
    
    # 1. 기준 시점 평균 가격 (2021-01)
    base_date = datetime(2021, 1, 1)
    base_price = await get_avg_price(db, index_type, base_date, base_date + relativedelta(months=1))
    
    if base_price == 0:
        raise ValueError("기준 시점 데이터 없음")
    
    # 2. 월별 HPI 계산
    trend = []
    current_date = base_date
    end_date = datetime.now()
    
    while current_date <= end_date:
        month_price = await get_avg_price(
            db, index_type, 
            current_date, 
            current_date + relativedelta(months=1)
        )
        
        if month_price > 0:
            hpi_value = (month_price / base_price) * 100
            trend.append({
                "date": current_date.strftime("%Y-%m"),
                "value": round(hpi_value, 1)
            })
        
        current_date += relativedelta(months=1)
    
    # 3. 최신 값
    current_value = trend[-1]["value"] if trend else 100.0
    change_rate = current_value - 100.0
    
    return HPIResponse(
        region_type=region_type,
        index_type=index_type,
        base_date="2021-01",
        base_value=100.0,
        current_value=current_value,
        change_rate=round(change_rate, 1),
        trend=trend[-max_years*12:]  # 최근 N년만
    )
```

---

## 4. Materialized View 활용

복잡한 통계 쿼리를 사전 계산하여 저장합니다.

### 뷰 생성

```sql
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
    CASE WHEN monthly_rent = 0 THEN 'jeonse' ELSE 'monthly' END AS transaction_type,
    COUNT(*) AS transaction_count,
    AVG(deposit_price) AS avg_price,
    MIN(deposit_price) AS min_price,
    MAX(deposit_price) AS max_price
FROM rents
WHERE is_deleted = FALSE
GROUP BY month, region_id, 
         CASE WHEN monthly_rent = 0 THEN 'jeonse' ELSE 'monthly' END;

-- 인덱스 생성
CREATE INDEX idx_mv_monthly_stats_month ON mv_monthly_transaction_stats(month);
CREATE INDEX idx_mv_monthly_stats_region ON mv_monthly_transaction_stats(region_id);
CREATE INDEX idx_mv_monthly_stats_type ON mv_monthly_transaction_stats(transaction_type);
```

### 주기적 갱신

```sql
-- 동시 접근 가능하게 갱신
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_transaction_stats;
```

### 성능 개선 효과

| 쿼리 | 원본 테이블 | Materialized View |
|------|------------|-------------------|
| 월별 거래량 | 3-5초 | **100-200ms** |
| 평균 가격 추이 | 2-3초 | **50-100ms** |
| 지역별 통계 | 5초+ | **200ms 이하** |
