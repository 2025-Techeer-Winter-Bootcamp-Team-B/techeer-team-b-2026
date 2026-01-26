-- ============================================================
-- sales 테이블 region_id 인덱스 제거 (region_id 컬럼이 없음)
-- 생성일: 2026-01-26
-- 설명: sales 테이블에는 region_id 컬럼이 없으므로 해당 인덱스 생성 제거
-- ============================================================

-- sales 테이블에 region_id 컬럼이 없으므로 인덱스 생성 시도 제거
-- region_id는 apartments 테이블에 있으므로, 조인을 통해 접근해야 함
-- 기존에 잘못 생성된 인덱스가 있다면 제거
DROP INDEX IF EXISTS idx_sales_region_date_canceled;

-- 대신 apt_id와 contract_date를 활용한 인덱스만 유지
-- (이미 존재할 수 있으므로 IF NOT EXISTS 사용)
CREATE INDEX IF NOT EXISTS idx_sales_apt_date_canceled
ON sales(apt_id, contract_date DESC, is_canceled)
WHERE (is_deleted = FALSE OR is_deleted IS NULL);
