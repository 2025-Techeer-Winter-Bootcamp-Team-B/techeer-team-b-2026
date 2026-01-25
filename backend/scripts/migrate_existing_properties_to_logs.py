"""
기존 my_properties 및 favorite_apartments 데이터를 asset_activity_logs로 마이그레이션

실행 방법:
    python backend/scripts/migrate_existing_properties_to_logs.py
    
또는 Docker 컨테이너 내에서:
    docker exec realestate-backend python /app/scripts/migrate_existing_properties_to_logs.py
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models.my_property import MyProperty
from app.models.favorite import FavoriteApartment
from app.models.asset_activity_log import AssetActivityLog


async def migrate_existing_properties(db: AsyncSession):
    """기존 my_properties를 asset_activity_logs로 마이그레이션"""
    # 모든 활성 my_properties 조회 (is_deleted=False)
    print("\n" + "="*60)
    print("📋 [1/2] my_properties 테이블 마이그레이션 시작")
    print("="*60)
    result = await db.execute(
        select(MyProperty).where(MyProperty.is_deleted == False)
    )
    properties = result.scalars().all()
    
    total = len(properties)
    success_count = 0
    skip_count = 0
    error_count = 0
    errors = []
    
    if total == 0:
        print("✅ 마이그레이션할 레코드가 없습니다.")
    else:
        print(f"📊 총 {total}개의 레코드를 처리합니다...\n")
        
        for idx, property in enumerate(properties, 1):
            try:
                # 중복 체크: 이미 로그가 있는지 확인
                existing_log_result = await db.execute(
                    select(AssetActivityLog).where(
                        AssetActivityLog.account_id == property.account_id,
                        AssetActivityLog.apt_id == property.apt_id,
                        AssetActivityLog.event_type == 'ADD',
                        AssetActivityLog.category == 'MY_ASSET'
                    )
                )
                existing_log = existing_log_result.scalar_one_or_none()
                
                if existing_log:
                    skip_count += 1
                    print(f"[{idx}/{total}] ⏭️  스킵 (이미 존재): property_id={property.property_id}, account_id={property.account_id}, apt_id={property.apt_id}")
                    continue
                
                # 로그 생성
                log = AssetActivityLog(
                    account_id=property.account_id,
                    apt_id=property.apt_id,
                    category='MY_ASSET',
                    event_type='ADD',
                    current_price=property.current_market_price,
                    created_at=property.created_at if property.created_at else datetime.utcnow()
                )
                
                db.add(log)
                success_count += 1
                print(f"[{idx}/{total}] ✅ 처리 완료: property_id={property.property_id}, account_id={property.account_id}, apt_id={property.apt_id}")
                
                # 일정 개수마다 커밋 (성능 최적화)
                if idx % 100 == 0:
                    await db.commit()
                    print(f"   💾 중간 커밋 완료 ({idx}/{total})")
            
            except Exception as e:
                error_count += 1
                error_msg = f"property_id={property.property_id}: {str(e)}"
                errors.append(error_msg)
                print(f"[{idx}/{total}] ❌ 오류: {error_msg}")
                # 개별 레코드 오류 시 롤백하지 않고 계속 진행
                await db.rollback()
    
    return {
        'total': total,
        'success': success_count,
        'skip': skip_count,
        'error': error_count,
        'errors': errors
    }


async def migrate_existing_favorites(db: AsyncSession):
    """기존 favorite_apartments를 asset_activity_logs로 마이그레이션"""
    # 모든 활성 favorite_apartments 조회 (is_deleted=False, account_id가 있는 것만)
    print("\n" + "="*60)
    print("📋 [2/2] favorite_apartments 테이블 마이그레이션 시작")
    print("="*60)
    result = await db.execute(
        select(FavoriteApartment).where(
            FavoriteApartment.is_deleted == False,
            FavoriteApartment.account_id.isnot(None)  # account_id가 있는 것만 처리
        )
    )
    favorites = result.scalars().all()
    
    total = len(favorites)
    success_count = 0
    skip_count = 0
    error_count = 0
    errors = []
    
    if total == 0:
        print("✅ 마이그레이션할 레코드가 없습니다.")
    else:
        print(f"📊 총 {total}개의 레코드를 처리합니다...\n")
        
        for idx, favorite in enumerate(favorites, 1):
            try:
                # 중복 체크: 이미 로그가 있는지 확인
                existing_log_result = await db.execute(
                    select(AssetActivityLog).where(
                        AssetActivityLog.account_id == favorite.account_id,
                        AssetActivityLog.apt_id == favorite.apt_id,
                        AssetActivityLog.event_type == 'ADD',
                        AssetActivityLog.category == 'INTEREST'
                    )
                )
                existing_log = existing_log_result.scalar_one_or_none()
                
                if existing_log:
                    skip_count += 1
                    print(f"[{idx}/{total}] ⏭️  스킵 (이미 존재): favorite_id={favorite.favorite_id}, account_id={favorite.account_id}, apt_id={favorite.apt_id}")
                    continue
                
                # 로그 생성
                log = AssetActivityLog(
                    account_id=favorite.account_id,
                    apt_id=favorite.apt_id,
                    category='INTEREST',
                    event_type='ADD',
                    created_at=favorite.created_at if favorite.created_at else datetime.utcnow()
                )
                
                db.add(log)
                success_count += 1
                print(f"[{idx}/{total}] ✅ 처리 완료: favorite_id={favorite.favorite_id}, account_id={favorite.account_id}, apt_id={favorite.apt_id}")
                
                # 일정 개수마다 커밋 (성능 최적화)
                if idx % 100 == 0:
                    await db.commit()
                    print(f"   💾 중간 커밋 완료 ({idx}/{total})")
            
            except Exception as e:
                error_count += 1
                error_msg = f"favorite_id={favorite.favorite_id}: {str(e)}"
                errors.append(error_msg)
                print(f"[{idx}/{total}] ❌ 오류: {error_msg}")
                # 개별 레코드 오류 시 롤백하지 않고 계속 진행
                await db.rollback()
    
    return {
        'total': total,
        'success': success_count,
        'skip': skip_count,
        'error': error_count,
        'errors': errors
    }


async def migrate_all():
    """my_properties와 favorite_apartments를 모두 마이그레이션"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            # my_properties 마이그레이션
            properties_result = await migrate_existing_properties(db)
            
            # favorite_apartments 마이그레이션
            favorites_result = await migrate_existing_favorites(db)
            
            # 최종 커밋
            if properties_result['success'] > 0 or favorites_result['success'] > 0:
                await db.commit()
                print(f"\n💾 최종 커밋 완료")
            
            # 전체 결과 출력
            print("\n" + "="*60)
            print("🎉 전체 마이그레이션 완료!")
            print("="*60)
            print("\n📊 my_properties 결과:")
            print(f"  ✅ 성공: {properties_result['success']}개")
            print(f"  ⏭️  스킵: {properties_result['skip']}개 (이미 존재)")
            print(f"  ❌ 오류: {properties_result['error']}개")
            print("\n📊 favorite_apartments 결과:")
            print(f"  ✅ 성공: {favorites_result['success']}개")
            print(f"  ⏭️  스킵: {favorites_result['skip']}개 (이미 존재)")
            print(f"  ❌ 오류: {favorites_result['error']}개")
            print("\n📊 전체 합계:")
            total_success = properties_result['success'] + favorites_result['success']
            total_skip = properties_result['skip'] + favorites_result['skip']
            total_error = properties_result['error'] + favorites_result['error']
            print(f"  ✅ 성공: {total_success}개")
            print(f"  ⏭️  스킵: {total_skip}개")
            print(f"  ❌ 오류: {total_error}개")
            print("="*60)
            
            # 오류 상세 출력
            all_errors = properties_result['errors'] + favorites_result['errors']
            if all_errors:
                print("\n⚠️  오류 상세:")
                for error in all_errors:
                    print(f"  - {error}")
            
            # 검증: 마이그레이션된 로그 수 확인
            if total_success > 0:
                print("\n🔍 마이그레이션 결과 검증 중...")
                
                # MY_ASSET 검증
                my_asset_result = await db.execute(
                    select(AssetActivityLog).where(
                        AssetActivityLog.category == 'MY_ASSET',
                        AssetActivityLog.event_type == 'ADD'
                    )
                )
                my_asset_logs = my_asset_result.scalars().all()
                print(f"✅ MY_ASSET/ADD 로그: {len(my_asset_logs)}개")
                
                # INTEREST 검증
                interest_result = await db.execute(
                    select(AssetActivityLog).where(
                        AssetActivityLog.category == 'INTEREST',
                        AssetActivityLog.event_type == 'ADD'
                    )
                )
                interest_logs = interest_result.scalars().all()
                print(f"✅ INTEREST/ADD 로그: {len(interest_logs)}개")
                
                print(f"✅ 전체 로그: {len(my_asset_logs) + len(interest_logs)}개")
            
    except Exception as e:
        print(f"\n❌ 치명적 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate_all())
