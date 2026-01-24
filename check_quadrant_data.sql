-- 1. 전체 매매 데이터 건수 (기간별)
SELECT 
    EXTRACT(YEAR FROM contract_date) as year,
    EXTRACT(MONTH FROM contract_date) as month,
    COUNT(*) as total_count,
    SUM(CASE WHEN remarks = '더미' THEN 1 ELSE 0 END) as dummy_count,
    SUM(CASE WHEN is_canceled = true THEN 1 ELSE 0 END) as canceled_count,
    SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) as deleted_count,
    COUNT(*) - SUM(CASE WHEN remarks = '더미' THEN 1 ELSE 0 END) - 
        SUM(CASE WHEN is_canceled = true THEN 1 ELSE 0 END) - 
        SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) as valid_count
FROM sales
WHERE contract_date >= '2024-01-01' AND contract_date < '2026-02-01'
GROUP BY EXTRACT(YEAR FROM contract_date), EXTRACT(MONTH FROM contract_date)
ORDER BY year DESC, month DESC;

-- 2. 전체 전월세 데이터 건수 (기간별)
SELECT 
    EXTRACT(YEAR FROM deal_date) as year,
    EXTRACT(MONTH FROM deal_date) as month,
    COUNT(*) as total_count,
    SUM(CASE WHEN remarks = '더미' THEN 1 ELSE 0 END) as dummy_count,
    SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) as deleted_count,
    COUNT(*) - SUM(CASE WHEN remarks = '더미' THEN 1 ELSE 0 END) - 
        SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) as valid_count
FROM rents
WHERE deal_date >= '2024-01-01' AND deal_date < '2026-02-01'
GROUP BY EXTRACT(YEAR FROM deal_date), EXTRACT(MONTH FROM deal_date)
ORDER BY year DESC, month DESC;

-- 3. 특정 기간 (2024-09 ~ 2025-05) 매매 유효 데이터
SELECT 
    COUNT(*) as valid_count
FROM sales
WHERE 
    is_canceled = false
    AND (is_deleted = false OR is_deleted IS NULL)
    AND contract_date IS NOT NULL
    AND contract_date >= '2024-09-01'
    AND contract_date < '2025-05-01'
    AND (remarks != '더미' OR remarks IS NULL);

-- 4. 특정 기간 (2025-05 ~ 2026-01) 매매 유효 데이터
SELECT 
    EXTRACT(YEAR FROM contract_date) as year,
    EXTRACT(MONTH FROM contract_date) as month,
    COUNT(*) as valid_count
FROM sales
WHERE 
    is_canceled = false
    AND (is_deleted = false OR is_deleted IS NULL)
    AND contract_date IS NOT NULL
    AND contract_date >= '2025-05-01'
    AND contract_date < '2026-01-01'
    AND (remarks != '더미' OR remarks IS NULL)
GROUP BY EXTRACT(YEAR FROM contract_date), EXTRACT(MONTH FROM contract_date)
ORDER BY year, month;
