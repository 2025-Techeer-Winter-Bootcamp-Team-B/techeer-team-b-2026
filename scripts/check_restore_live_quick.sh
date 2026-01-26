#!/bin/bash
# 복원 진행 상황 빠른 확인 스크립트 (rents, sales 전용)

echo "============================================================"
echo "  복원 진행 상황 빠른 확인 (rents, sales)"
echo "============================================================"

# Docker 컨테이너에서 Python으로 직접 확인
docker exec realestate-backend python3 <<'PYTHON_SCRIPT'
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import os
from datetime import datetime

# 환경 변수에서 DATABASE_URL 가져오기
database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost:5432/realestate_db')

async def check_progress():
    engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)
    
    try:
        async with engine.connect() as conn:
            # rents 테이블 확인
            result = await conn.execute(text('SELECT COUNT(*) FROM rents'))
            rents_count = result.scalar() or 0
            
            # sales 테이블 확인
            result = await conn.execute(text('SELECT COUNT(*) FROM sales'))
            sales_count = result.scalar() or 0
            
            # 예상 행 수
            estimated_rents = 5702411
            estimated_sales = 3237595
            
            # 현재 시간
            now = datetime.now().strftime("%H:%M:%S")
            
            print(f"\n⏰ 확인 시간: {now}")
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            # rents 진행률
            if rents_count > 0:
                rents_pct = (rents_count / estimated_rents * 100) if estimated_rents > 0 else 0
                print(f"✅ rents:    {rents_count:>10,} / {estimated_rents:>10,} 행 ({rents_pct:>5.1f}%)")
            else:
                print(f"⏳ rents:    아직 시작되지 않음 (COPY 초기화 중일 수 있음)")
            
            # sales 진행률
            if sales_count > 0:
                sales_pct = (sales_count / estimated_sales * 100) if estimated_sales > 0 else 0
                print(f"✅ sales:    {sales_count:>10,} / {estimated_sales:>10,} 행 ({sales_pct:>5.1f}%)")
            else:
                print(f"⏳ sales:    아직 시작되지 않음 (COPY 초기화 중일 수 있음)")
            
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            # 상태 판단
            if rents_count == 0 and sales_count == 0:
                print(f"\n💡 COPY가 아직 데이터를 삽입하지 않았습니다.")
                print(f"   - COPY는 내부 버퍼링으로 시작까지 5-10초 걸릴 수 있습니다.")
                print(f"   - 잠시 후 다시 확인하세요: watch -n 2 ./scripts/check_restore_live_quick.sh")
            elif rents_count > 0 or sales_count > 0:
                print(f"\n✅ 복원이 진행 중입니다!")
                if rents_count < estimated_rents or sales_count < estimated_sales:
                    print(f"   - 계속 모니터링하세요: watch -n 2 ./scripts/check_restore_live_quick.sh")
    
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
    finally:
        await engine.dispose()

asyncio.run(check_progress())
PYTHON_SCRIPT

echo ""
echo "============================================================"
