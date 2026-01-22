-- ============================================================
-- 마이그레이션: my_properties 테이블에 누락된 컬럼 추가
-- 날짜: 2026-01-22
-- 설명: purchase_price, loan_amount, purchase_date 컬럼 추가
-- ============================================================

-- purchase_price 컬럼 추가 (구매가, 만원 단위)
ALTER TABLE my_properties 
ADD COLUMN IF NOT EXISTS purchase_price INTEGER;

COMMENT ON COLUMN my_properties.purchase_price IS '구매가 (만원)';

-- loan_amount 컬럼 추가 (대출 금액, 만원 단위)
ALTER TABLE my_properties 
ADD COLUMN IF NOT EXISTS loan_amount INTEGER;

COMMENT ON COLUMN my_properties.loan_amount IS '대출 금액 (만원)';

-- purchase_date 컬럼 추가 (매입일)
ALTER TABLE my_properties 
ADD COLUMN IF NOT EXISTS purchase_date TIMESTAMP;

COMMENT ON COLUMN my_properties.purchase_date IS '매입일';
