-- ============================================================
-- 테스트 아파트 데이터 (ERD 설계에 맞춤)
-- .agent/data.sql ERD 설계 기반
-- ============================================================

-- 먼저 states 테이블에 테스트 지역 데이터 삽입 (apartments의 FK인 region_id 필요)
-- region_id는 SERIAL이므로 자동 증가, 직접 지정하지 않음
-- 중복 방지를 위해 먼저 확인 후 삽입
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM states WHERE region_code = '1168000000') THEN
        INSERT INTO states (region_name, region_code, city_name, created_at, updated_at, is_deleted)
        VALUES ('강남구', '1168000000', '서울특별시', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM states WHERE region_code = '1165000000') THEN
        INSERT INTO states (region_name, region_code, city_name, created_at, updated_at, is_deleted)
        VALUES ('서초구', '1165000000', '서울특별시', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM states WHERE region_code = '1171000000') THEN
        INSERT INTO states (region_name, region_code, city_name, created_at, updated_at, is_deleted)
        VALUES ('송파구', '1171000000', '서울특별시', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM states WHERE region_code = '1144000000') THEN
        INSERT INTO states (region_name, region_code, city_name, created_at, updated_at, is_deleted)
        VALUES ('마포구', '1144000000', '서울특별시', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM states WHERE region_code = '1156000000') THEN
        INSERT INTO states (region_name, region_code, city_name, created_at, updated_at, is_deleted)
        VALUES ('영등포구', '1156000000', '서울특별시', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE);
    END IF;
END $$;

-- ERD 설계에 맞는 아파트 테스트 데이터 삽입
-- APARTMENTS 테이블: apt_id, region_id, apt_name, kapt_code, is_available, created_at, updated_at, is_deleted
-- region_id는 states 테이블에서 조회하여 사용
INSERT INTO apartments (region_id, apt_name, kapt_code, is_available, created_at, updated_at, is_deleted) 
SELECT region_id, '래미안 강남퍼스트', 'A1234567890', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '강남구'
UNION ALL SELECT region_id, '래미안 대치팰리스', 'A1234567891', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '강남구'
UNION ALL SELECT region_id, '힐스테이트 강남', 'A1234567892', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '강남구'
UNION ALL SELECT region_id, '타워팰리스', 'A1234567893', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '강남구'
UNION ALL SELECT region_id, '삼성래미안', 'A1234567894', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '강남구'
UNION ALL SELECT region_id, '래미안 서초 STG', 'A1234567895', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '서초구'
UNION ALL SELECT region_id, '시 서초', 'A1234567896', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '서초구'
UNION ALL SELECT region_id, '아크로 리버파크', 'A1234567897', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '서초구'
UNION ALL SELECT region_id, '반포 시', 'A1234567898', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '서초구'
UNION ALL SELECT region_id, '래미안 퍼스티지', 'A1234567899', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '서초구'
UNION ALL SELECT region_id, '래미안 송파 파크뷰', 'A1234567900', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '송파구'
UNION ALL SELECT region_id, '롯데 캐슬 골드', 'A1234567901', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '송파구'
UNION ALL SELECT region_id, '잠실 엘루트', 'A1234567902', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '송파구'
UNION ALL SELECT region_id, '파크리오', 'A1234567903', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '송파구'
UNION ALL SELECT region_id, '헬리오폴리스', 'A1234567904', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '송파구'
UNION ALL SELECT region_id, '프루지오 마포', 'A1234567905', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '마포구'
UNION ALL SELECT region_id, '마포 래미안 프루지오', 'A1234567906', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '마포구'
UNION ALL SELECT region_id, '마포 시 타워', 'A1234567907', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '마포구'
UNION ALL SELECT region_id, '더샵 영등포', 'A1234567908', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '영등포구'
UNION ALL SELECT region_id, '영등포 래미안 퍼스티지', 'A1234567909', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '영등포구'
UNION ALL SELECT region_id, '여의도 시', 'A1234567910', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE FROM states WHERE region_name = '영등포구'
ON CONFLICT (kapt_code) DO NOTHING;

SELECT COUNT(*) as total_apartments FROM apartments WHERE is_deleted = FALSE;
