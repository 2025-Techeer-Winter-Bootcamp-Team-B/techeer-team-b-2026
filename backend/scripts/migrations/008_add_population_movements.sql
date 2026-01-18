-- ============================================================
-- 마이그레이션 008: POPULATION_MOVEMENTS 테이블 추가
-- ============================================================
-- 날짜: 2026-01-25
-- 설명: 인구 이동 데이터를 저장하는 테이블 추가 (KOSIS 통계청 데이터)

-- POPULATION_MOVEMENTS 테이블 (인구 이동)
CREATE TABLE IF NOT EXISTS population_movements (
    movement_id SERIAL PRIMARY KEY,
    region_id INTEGER NOT NULL,
    base_ym CHAR(6) NOT NULL,
    in_migration INTEGER NOT NULL DEFAULT 0,
    out_migration INTEGER NOT NULL DEFAULT 0,
    net_migration INTEGER NOT NULL DEFAULT 0,
    movement_type VARCHAR(20) NOT NULL DEFAULT 'TOTAL',
    data_source VARCHAR(50) NOT NULL DEFAULT 'KOSIS',
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_population_movements_region FOREIGN KEY (region_id) REFERENCES states(region_id)
);

COMMENT ON TABLE population_movements IS '인구 이동 테이블 (KOSIS 통계청 데이터)';
COMMENT ON COLUMN population_movements.movement_id IS 'PK';
COMMENT ON COLUMN population_movements.region_id IS 'FK (states.region_id)';
COMMENT ON COLUMN population_movements.base_ym IS '기준 년월 (YYYYMM)';
COMMENT ON COLUMN population_movements.in_migration IS '전입 인구 수 (명)';
COMMENT ON COLUMN population_movements.out_migration IS '전출 인구 수 (명)';
COMMENT ON COLUMN population_movements.net_migration IS '순이동 인구 수 (전입 - 전출, 명)';
COMMENT ON COLUMN population_movements.movement_type IS '이동 유형: TOTAL=전체, DOMESTIC=국내이동';
COMMENT ON COLUMN population_movements.data_source IS '데이터 출처';
COMMENT ON COLUMN population_movements.is_deleted IS '소프트 삭제';

-- 인덱스 생성 (조회 성능 최적화)
CREATE INDEX IF NOT EXISTS idx_population_movements_region_ym ON population_movements(region_id, base_ym);
CREATE INDEX IF NOT EXISTS idx_population_movements_base_ym ON population_movements(base_ym);
