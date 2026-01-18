-- ============================================================
-- 마이그레이션: DB 성능 최적화
-- 버전: 003
-- 설명: 복합 인덱스, 부분 인덱스 추가로 검색 속도 향상
-- ============================================================

-- ============================================================
-- 1. SALES 테이블 최적화 인덱스
-- ============================================================

-- 복합 인덱스: apt_id + contract_date (아파트별 거래 조회 최적화)
CREATE INDEX IF NOT EXISTS idx_sales_apt_id_contract_date 
ON sales(apt_id, contract_date DESC);

-- 복합 인덱스: contract_date + 필터 조건 (날짜 범위 검색 최적화)
CREATE INDEX IF NOT EXISTS idx_sales_contract_date_filtered 
ON sales(contract_date DESC) 
WHERE is_canceled = FALSE 
  AND (is_deleted = FALSE OR is_deleted IS NULL)
  AND (remarks != '더미' OR remarks IS NULL);

-- 복합 인덱스: apt_id + 필터 조건 (아파트별 유효 거래 조회)
CREATE INDEX IF NOT EXISTS idx_sales_apt_id_filtered 
ON sales(apt_id) 
WHERE is_canceled = FALSE 
  AND (is_deleted = FALSE OR is_deleted IS NULL)
  AND (remarks != '더미' OR remarks IS NULL);

-- 복합 인덱스: contract_date + trans_price (날짜별 가격 통계)
CREATE INDEX IF NOT EXISTS idx_sales_date_price 
ON sales(contract_date DESC, trans_price) 
WHERE is_canceled = FALSE 
  AND (is_deleted = FALSE OR is_deleted IS NULL)
  AND (remarks != '더미' OR remarks IS NULL)
  AND trans_price IS NOT NULL;

-- 복합 인덱스: exclusive_area + trans_price (면적별 가격 검색)
CREATE INDEX IF NOT EXISTS idx_sales_area_price 
ON sales(exclusive_area, trans_price) 
WHERE is_canceled = FALSE 
  AND (is_deleted = FALSE OR is_deleted IS NULL)
  AND (remarks != '더미' OR remarks IS NULL)
  AND trans_price IS NOT NULL
  AND exclusive_area > 0;

-- 부분 인덱스: is_deleted = FALSE (삭제되지 않은 거래만)
CREATE INDEX IF NOT EXISTS idx_sales_not_deleted 
ON sales(apt_id, contract_date DESC) 
WHERE is_deleted = FALSE OR is_deleted IS NULL;

-- 부분 인덱스: is_canceled = FALSE (취소되지 않은 거래만)
CREATE INDEX IF NOT EXISTS idx_sales_not_canceled 
ON sales(apt_id, contract_date DESC) 
WHERE is_canceled = FALSE;

-- 부분 인덱스: remarks != '더미' (더미가 아닌 거래만)
CREATE INDEX IF NOT EXISTS idx_sales_not_dummy 
ON sales(apt_id, contract_date DESC) 
WHERE remarks != '더미' OR remarks IS NULL;

-- ============================================================
-- 2. RENTS 테이블 최적화 인덱스
-- ============================================================

-- 복합 인덱스: apt_id + deal_date (아파트별 거래 조회 최적화)
CREATE INDEX IF NOT EXISTS idx_rents_apt_id_deal_date 
ON rents(apt_id, deal_date DESC);

-- 복합 인덱스: deal_date + 필터 조건 (날짜 범위 검색 최적화)
CREATE INDEX IF NOT EXISTS idx_rents_deal_date_filtered 
ON rents(deal_date DESC) 
WHERE (is_deleted = FALSE OR is_deleted IS NULL)
  AND (remarks != '더미' OR remarks IS NULL);

-- 복합 인덱스: apt_id + 필터 조건 (아파트별 유효 거래 조회)
CREATE INDEX IF NOT EXISTS idx_rents_apt_id_filtered 
ON rents(apt_id) 
WHERE (is_deleted = FALSE OR is_deleted IS NULL)
  AND (remarks != '더미' OR remarks IS NULL);

-- 복합 인덱스: monthly_rent + deposit_price (전세/월세 구분 검색)
CREATE INDEX IF NOT EXISTS idx_rents_rent_type_price 
ON rents(monthly_rent, deposit_price) 
WHERE (is_deleted = FALSE OR is_deleted IS NULL)
  AND (remarks != '더미' OR remarks IS NULL)
  AND deposit_price IS NOT NULL;

-- 부분 인덱스: 전세 (monthly_rent = 0)
CREATE INDEX IF NOT EXISTS idx_rents_jeonse 
ON rents(apt_id, deal_date DESC, deposit_price) 
WHERE monthly_rent = 0 
  AND (is_deleted = FALSE OR is_deleted IS NULL)
  AND (remarks != '더미' OR remarks IS NULL)
  AND deposit_price IS NOT NULL;

-- 부분 인덱스: 월세 (monthly_rent > 0)
CREATE INDEX IF NOT EXISTS idx_rents_wolse 
ON rents(apt_id, deal_date DESC, deposit_price, monthly_rent) 
WHERE monthly_rent > 0 
  AND (is_deleted = FALSE OR is_deleted IS NULL)
  AND (remarks != '더미' OR remarks IS NULL)
  AND deposit_price IS NOT NULL;

-- 부분 인덱스: is_deleted = FALSE (삭제되지 않은 거래만)
CREATE INDEX IF NOT EXISTS idx_rents_not_deleted 
ON rents(apt_id, deal_date DESC) 
WHERE is_deleted = FALSE OR is_deleted IS NULL;

-- 부분 인덱스: remarks != '더미' (더미가 아닌 거래만)
CREATE INDEX IF NOT EXISTS idx_rents_not_dummy 
ON rents(apt_id, deal_date DESC) 
WHERE remarks != '더미' OR remarks IS NULL;

-- ============================================================
-- 3. APARTMENTS 테이블 최적화 인덱스
-- ============================================================

-- 복합 인덱스: region_id + is_deleted (지역별 아파트 조회)
CREATE INDEX IF NOT EXISTS idx_apartments_region_not_deleted 
ON apartments(region_id, apt_id) 
WHERE is_deleted = FALSE;

-- 복합 인덱스: region_id + kapt_code (지역별 단지코드 검색)
CREATE INDEX IF NOT EXISTS idx_apartments_region_kapt 
ON apartments(region_id, kapt_code) 
WHERE is_deleted = FALSE;

-- 부분 인덱스: is_deleted = FALSE (삭제되지 않은 아파트만)
CREATE INDEX IF NOT EXISTS idx_apartments_not_deleted 
ON apartments(region_id, apt_id) 
WHERE is_deleted = FALSE;

-- ============================================================
-- 4. STATES 테이블 최적화 인덱스
-- ============================================================

-- 복합 인덱스: city_name + region_name (시도별 시군구 검색)
CREATE INDEX IF NOT EXISTS idx_states_city_region 
ON states(city_name, region_name) 
WHERE is_deleted = FALSE;

-- 부분 인덱스: is_deleted = FALSE (삭제되지 않은 지역만)
CREATE INDEX IF NOT EXISTS idx_states_not_deleted 
ON states(city_name, region_name) 
WHERE is_deleted = FALSE;

-- ============================================================
-- 5. APART_DETAILS 테이블 최적화 인덱스
-- ============================================================

-- 복합 인덱스: apt_id + is_deleted (아파트 상세 정보 조회)
CREATE INDEX IF NOT EXISTS idx_apart_details_apt_not_deleted 
ON apart_details(apt_id) 
WHERE is_deleted = FALSE;

-- 부분 인덱스: is_deleted = FALSE (삭제되지 않은 상세 정보만)
CREATE INDEX IF NOT EXISTS idx_apart_details_not_deleted 
ON apart_details(apt_id) 
WHERE is_deleted = FALSE;

-- ============================================================
-- 6. 통계 정보 업데이트
-- ============================================================

-- 테이블 통계 정보 업데이트 (쿼리 플래너 최적화)
ANALYZE sales;
ANALYZE rents;
ANALYZE apartments;
ANALYZE states;
ANALYZE apart_details;

-- ============================================================
-- 완료 메시지
-- ============================================================
DO $$
BEGIN
    RAISE NOTICE '✅ DB 성능 최적화 인덱스 생성 완료!';
    RAISE NOTICE '   - 복합 인덱스: 자주 함께 사용되는 필터 조합 최적화';
    RAISE NOTICE '   - 부분 인덱스: 특정 조건만 인덱싱하여 인덱스 크기 감소';
    RAISE NOTICE '   - 통계 정보 업데이트 완료';
END $$;
