-- ============================================================
-- 마이그레이션: 지하철 거리 파싱 함수
-- 버전: 005
-- 설명: subway_time 필드에서 최대 시간을 추출하는 함수 생성
-- ============================================================

-- ============================================================
-- 1. 지하철 거리 파싱 함수 생성
-- ============================================================

-- 함수: subway_time에서 최대 시간(분) 추출
-- 예: "5~10분이내" → 10, "15분이내" → 15, "5분" → 5
CREATE OR REPLACE FUNCTION parse_subway_time_max_minutes(subway_time_text TEXT)
RETURNS INTEGER AS $$
DECLARE
    max_time INTEGER := NULL;
    numbers INTEGER[];
    num INTEGER;
BEGIN
    -- NULL 또는 빈 문자열 체크
    IF subway_time_text IS NULL OR subway_time_text = '' THEN
        RETURN NULL;
    END IF;
    
    -- 정규식으로 모든 숫자 추출
    -- 예: "5~10분이내" → [5, 10]
    SELECT ARRAY(
        SELECT (regexp_matches(subway_time_text, '\d+', 'g'))[1]::INTEGER
    ) INTO numbers;
    
    -- 숫자가 없으면 NULL 반환
    IF array_length(numbers, 1) IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- 최대값 찾기
    max_time := numbers[1];
    FOREACH num IN ARRAY numbers
    LOOP
        IF num > max_time THEN
            max_time := num;
        END IF;
    END LOOP;
    
    RETURN max_time;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 함수 인덱스: 파싱된 지하철 거리로 인덱스 생성
-- 이 인덱스는 WHERE parse_subway_time_max_minutes(subway_time) <= 10 같은 쿼리에 사용
CREATE INDEX IF NOT EXISTS idx_apart_details_subway_time_parsed 
ON apart_details(apt_id) 
WHERE is_deleted = FALSE
  AND subway_time IS NOT NULL
  AND subway_time != ''
  AND parse_subway_time_max_minutes(subway_time) IS NOT NULL;

-- ============================================================
-- 2. 통계 정보 업데이트
-- ============================================================

ANALYZE apart_details;

-- ============================================================
-- 완료 메시지
-- ============================================================
-- 마이그레이션 완료: 지하철 거리 파싱 함수 생성 완료!
--   - parse_subway_time_max_minutes() 함수 생성
--   - 함수 인덱스 생성 완료
