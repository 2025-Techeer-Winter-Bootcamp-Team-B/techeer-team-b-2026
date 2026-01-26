#!/bin/bash
# 복원 상태 확인 스크립트

echo "============================================================"
echo "  데이터베이스 복원 상태 확인"
echo "============================================================"

# Python 프로세스 확인
echo ""
echo "1. Python 복원 프로세스 확인:"
ps aux | grep -E "python.*db_admin|restore" | grep -v grep || echo "   복원 프로세스가 실행 중이지 않습니다."

# PostgreSQL 연결 확인
echo ""
echo "2. PostgreSQL 연결 확인:"
docker exec realestate-backend psql -U postgres -d realestate_db -c "SELECT version();" 2>/dev/null || echo "   PostgreSQL 연결 실패"

# 테이블 행 수 확인
echo ""
echo "3. 주요 테이블 행 수 확인:"
docker exec realestate-backend psql -U postgres -d realestate_db -c "
SELECT 
    'rents' as table_name, 
    COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size('rents')) as table_size
FROM rents
UNION ALL
SELECT 
    'sales' as table_name, 
    COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size('sales')) as table_size
FROM sales
UNION ALL
SELECT 
    'apartments' as table_name, 
    COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size('apartments')) as table_size
FROM apartments
UNION ALL
SELECT 
    'apart_details' as table_name, 
    COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size('apart_details')) as table_size
FROM apart_details;
" 2>/dev/null || echo "   테이블 조회 실패"

# 백업 파일 크기 확인
echo ""
echo "4. 백업 파일 크기 확인:"
docker exec realestate-backend ls -lh /app/backups/rents.csv /app/backups/sales.csv 2>/dev/null || echo "   백업 파일을 찾을 수 없습니다."

echo ""
echo "============================================================"
