-- ============================================================
-- 마이그레이션: 고급 인덱스 최적화
-- 버전: 004
-- 설명: detailed_search 쿼리 최적화를 위한 고급 인덱스 추가
-- ============================================================

-- ============================================================
-- 1. SALES 테이블: 최근 6개월 거래 최적화 인덱스
-- ============================================================

-- 복합 인덱스: apt_id + contract_date + trans_price + exclusive_area
-- detailed_search에서 아파트별 평균 가격/면적 계산 시 사용
CREATE INDEX IF NOT EXISTS idx_sales_apt_date_price_area_recent 
ON sales(apt_id, contract_date DESC, trans_price, exclusive_area) 
WHERE is_canceled = FALSE 
  AND (is_deleted = FALSE OR is_deleted IS NULL)
  AND trans_price IS NOT NULL
  AND exclusive_area > 0
  AND contract_date >= CURRENT_DATE - INTERVAL '180 days';

-- 복합 인덱스: contract_date + trans_price + exclusive_area (전역 검색용)
-- region_id 없이 전체 검색 시 사용
CREATE INDEX IF NOT EXISTS idx_sales_date_price_area_global 
ON sales(contract_date DESC, trans_price, exclusive_area, apt_id) 
WHERE is_canceled = FALSE 
  AND (is_deleted = FALSE OR is_deleted IS NULL)
  AND trans_price IS NOT NULL
  AND exclusive_area > 0
  AND contract_date >= CURRENT_DATE - INTERVAL '180 days';

-- ============================================================
-- 2. RENTS 테이블: 최근 6개월 거래 최적화 인덱스
-- ============================================================

-- 복합 인덱스: apt_id + deal_date + deposit_price + monthly_rent
CREATE INDEX IF NOT EXISTS idx_rents_apt_date_price_recent 
ON rents(apt_id, deal_date DESC, deposit_price, monthly_rent) 
WHERE (is_deleted = FALSE OR is_deleted IS NULL)
  AND deal_date >= CURRENT_DATE - INTERVAL '180 days';

-- ============================================================
-- 3. APART_DETAILS 테이블: 검색 조건 최적화 인덱스
-- ============================================================

-- 복합 인덱스: apt_id + educationFacility (교육시설 필터링)
CREATE INDEX IF NOT EXISTS idx_apart_details_apt_education 
ON apart_details(apt_id) 
WHERE is_deleted = FALSE
  AND educationFacility IS NOT NULL
  AND educationFacility != '';

-- 복합 인덱스: apt_id + subway_time (지하철 거리 필터링)
CREATE INDEX IF NOT EXISTS idx_apart_details_apt_subway 
ON apart_details(apt_id) 
WHERE is_deleted = FALSE
  AND subway_time IS NOT NULL
  AND subway_time != '';

-- ============================================================
-- 4. APARTMENTS 테이블: 지역 검색 최적화 인덱스
-- ============================================================

-- 복합 인덱스: region_id + apt_id + apt_name (지역별 정렬 최적화)
CREATE INDEX IF NOT EXISTS idx_apartments_region_apt_name 
ON apartments(region_id, apt_name, apt_id) 
WHERE is_deleted = FALSE;

-- ============================================================
-- 5. 통계 정보 업데이트
-- ============================================================

-- 테이블 통계 정보 업데이트 (쿼리 플래너 최적화)
ANALYZE sales;
ANALYZE rents;
ANALYZE apartments;
ANALYZE apart_details;
ANALYZE states;

-- ============================================================
-- 완료 메시지
-- ============================================================
DO $$
BEGIN
    RAISE NOTICE '✅ 고급 인덱스 최적화 완료!';
    RAISE NOTICE '   - 최근 6개월 거래 데이터에 대한 복합 인덱스 추가';
    RAISE NOTICE '   - detailed_search 쿼리 최적화를 위한 인덱스 추가';
    RAISE NOTICE '   - 통계 정보 업데이트 완료';
END $$;
