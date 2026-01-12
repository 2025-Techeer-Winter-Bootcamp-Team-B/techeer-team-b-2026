-- ============================================================
-- 🏠 부동산 분석 플랫폼 - 데이터베이스 초기화 스크립트
-- ============================================================
-- 사용법: psql -U postgres -d realestate -f init_db.sql
-- 또는 Docker 컨테이너에서 실행:
-- docker exec -i realestate-db psql -U postgres -d realestate < init_db.sql

-- ============================================================
-- PostGIS 확장 활성화 (공간 데이터 지원)
-- ============================================================
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- ============================================================
-- ACCOUNTS 테이블 (사용자 계정) - Clerk 인증 사용
-- ============================================================
CREATE TABLE IF NOT EXISTS accounts (
    account_id SERIAL PRIMARY KEY,
    clerk_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    nickname VARCHAR(50) NOT NULL,
    profile_image_url VARCHAR(500),
    last_login_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_accounts_clerk_user_id ON accounts(clerk_user_id);
CREATE INDEX IF NOT EXISTS idx_accounts_email ON accounts(email);
CREATE INDEX IF NOT EXISTS idx_accounts_is_deleted ON accounts(is_deleted);

-- 코멘트 추가
COMMENT ON TABLE accounts IS '사용자 계정 테이블 (Clerk 인증 사용)';
COMMENT ON COLUMN accounts.clerk_user_id IS 'Clerk 사용자 ID (유니크)';
COMMENT ON COLUMN accounts.email IS '이메일 주소 (유니크)';
COMMENT ON COLUMN accounts.is_deleted IS '소프트 삭제 여부';

-- ============================================================
-- APARTMENTS 테이블 (아파트 기본정보)
-- ============================================================
CREATE TABLE IF NOT EXISTS apartments (
    apt_id SERIAL PRIMARY KEY,
    apt_name VARCHAR(200) NOT NULL,
    address VARCHAR(500),
    sigungu_code VARCHAR(10),
    sigungu_name VARCHAR(50),
    dong_name VARCHAR(50),
    latitude FLOAT,
    longitude FLOAT,
    total_units INTEGER,
    build_year INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성 (검색 성능 향상)
CREATE INDEX IF NOT EXISTS idx_apartments_apt_name ON apartments(apt_name);
CREATE INDEX IF NOT EXISTS idx_apartments_sigungu_code ON apartments(sigungu_code);
CREATE INDEX IF NOT EXISTS idx_apartments_dong_name ON apartments(dong_name);

-- 코멘트 추가
COMMENT ON TABLE apartments IS '아파트 기본정보 테이블 (국토교통부 API)';
COMMENT ON COLUMN apartments.apt_name IS '아파트명';
COMMENT ON COLUMN apartments.sigungu_code IS '시군구 코드';

-- ============================================================
-- 완료 메시지
-- ============================================================
DO $$
BEGIN
    RAISE NOTICE '데이터베이스 초기화 완료!';
    RAISE NOTICE 'accounts, apartments 테이블이 생성되었습니다.';
END $$;
