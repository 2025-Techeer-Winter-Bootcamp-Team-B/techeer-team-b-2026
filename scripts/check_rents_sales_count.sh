#!/bin/bash
# rents와 sales 테이블의 현재 행 수를 빠르게 확인하는 스크립트

echo "============================================================"
echo "  rents & sales 테이블 행 수 확인"
echo "============================================================"

docker exec realestate-backend python3 <<'PYTHON_SCRIPT'
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import os
from datetime import datetime

# 환경 변수에서 DATABASE_URL 가져오기
database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost:5432/realestate_db')

async def check_counts():
    engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)
    
    try:
        async with engine.connect() as conn:
            # rents 테이블 확인
            result = await conn.execute(text('SELECT COUNT(*) FROM rents'))
            rents_count = result.scalar() or 0
            
            # sales 테이블 확인
            result = await conn.execute(text('SELECT COUNT(*) FROM sales'))
            sales_count = result.scalar() or 0
            
            # 현재 시간
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"\n⏰ 확인 시간: {now}")
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"rents:  {rents_count:>12,} 행")
            print(f"sales:  {sales_count:>12,} 행")
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            # 예상 행 수와 비교
            estimated_rents = 5702411
            estimated_sales = 3237595
            
            if rents_count > 0:
                rents_pct = (rents_count / estimated_rents * 100) if estimated_rents > 0 else 0
                print(f"\nrents 진행률: {rents_pct:.1f}% ({rents_count:,}/{estimated_rents:,})")
            
            if sales_count > 0:
                sales_pct = (sales_count / estimated_sales * 100) if estimated_sales > 0 else 0
                print(f"sales 진행률: {sales_pct:.1f}% ({sales_count:,}/{estimated_sales:,})")
            
            # 상태 판단
            if rents_count == 0 and sales_count == 0:
                print(f"\n💡 아직 데이터가 삽입되지 않았습니다.")
                print(f"   - COPY 초기화 중일 수 있습니다 (5-10초 소요)")
                print(f"   - 잠시 후 다시 확인하세요")
            elif rents_count > 0 or sales_count > 0:
                print(f"\n✅ 복원이 진행 중입니다!")
                if rents_count < estimated_rents:
                    print(f"   - rents 복원 중...")
                if sales_count < estimated_sales:
                    print(f"   - sales 복원 중...")
    
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

asyncio.run(check_counts())
PYTHON_SCRIPT

echo ""
echo "============================================================"
echo "💡 반복 확인: watch -n 2 ./scripts/check_rents_sales_count.sh"
echo "============================================================"
