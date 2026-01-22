#!/usr/bin/env python3
"""
아파트 ID 불일치 분석 스크립트

apartments와 apart_details 간의 apt_id 매핑 문제를 분석합니다.
어느 쪽이 문제인지 판단하는 데 도움을 줍니다.

사용법:
    python backend/scripts/analyze_apt_id_mismatch.py
"""
import asyncio
import sys
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text, func
from app.core.config import settings
from app.models.apartment import Apartment
from app.models.apart_detail import ApartDetail

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def analyze_apt_id_mismatch():
    """아파트 ID 불일치 분석 메인 함수"""
    logger.info("=" * 80)
    logger.info("🔍 아파트 ID 불일치 분석 시작")
    logger.info("=" * 80)
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # 1. apartments 테이블의 apt_id 시퀀스 상태 확인
        logger.info("\n1️⃣  apartments 테이블 시퀀스 상태 확인")
        # 시퀀스 이름 먼저 찾기
        seq_name_result = await db.execute(
            text("""
                SELECT pg_get_serial_sequence('apartments', 'apt_id') as seq_name
            """)
        )
        seq_name_info = seq_name_result.first()
        if seq_name_info and seq_name_info.seq_name:
            seq_full_name = seq_name_info.seq_name
            logger.info(f"   시퀀스 이름: {seq_full_name}")
            # last_value 직접 조회 (안전한 방식)
            last_val_result = await db.execute(
                text(f"SELECT last_value FROM {seq_full_name}")
            )
            last_val = last_val_result.scalar()
            logger.info(f"   마지막 값: {last_val}")
        else:
            logger.warning("   ⚠️  시퀀스를 찾을 수 없습니다.")
        
        # 2. apartments 테이블의 실제 데이터 확인
        logger.info("\n2️⃣  apartments 테이블 데이터 분석")
        apt_stats = await db.execute(
            select(
                func.count(Apartment.apt_id).label('total_count'),
                func.min(Apartment.apt_id).label('min_id'),
                func.max(Apartment.apt_id).label('max_id')
            ).where(Apartment.is_deleted == False)
        )
        stats = apt_stats.first()
        logger.info(f"   총 레코드 수: {stats.total_count}")
        logger.info(f"   최소 apt_id: {stats.min_id}")
        logger.info(f"   최대 apt_id: {stats.max_id}")
        
        # 3. apt_id 간격 확인 (삭제된 레코드 감지)
        logger.info("\n3️⃣  apt_id 간격 분석 (삭제된 레코드 감지)")
        gap_result = await db.execute(
            text("""
                WITH ordered_apts AS (
                    SELECT apt_id, 
                           LAG(apt_id) OVER (ORDER BY apt_id) as prev_id
                    FROM apartments
                    WHERE is_deleted = FALSE
                    ORDER BY apt_id
                )
                SELECT 
                    prev_id,
                    apt_id as current_id,
                    apt_id - prev_id as gap
                FROM ordered_apts
                WHERE prev_id IS NOT NULL AND apt_id - prev_id > 1
                ORDER BY apt_id
                LIMIT 20
            """)
        )
        gaps = gap_result.all()
        if gaps:
            logger.info(f"   ⚠️  {len(gaps)}개의 ID 간격 발견 (삭제된 레코드 가능성)")
            for gap in gaps[:10]:
                logger.info(f"      apt_id {gap.prev_id} -> {gap.current_id} (간격: {gap.gap})")
            if len(gaps) > 10:
                logger.info(f"      ... 외 {len(gaps) - 10}건")
        else:
            logger.info("   ✅ ID 간격 없음 (연속적)")
        
        # 4. apart_details와 apartments 조인하여 매핑 확인
        logger.info("\n4️⃣  apart_details와 apartments 매핑 분석")
        mapping_result = await db.execute(
            select(
                ApartDetail.apt_detail_id,
                ApartDetail.apt_id.label('detail_apt_id'),
                ApartDetail.road_address,
                ApartDetail.jibun_address,
                Apartment.apt_id.label('apartment_apt_id'),
                Apartment.apt_name,
                Apartment.kapt_code
            )
            .join(Apartment, ApartDetail.apt_id == Apartment.apt_id)
            .where(ApartDetail.is_deleted == False)
            .where(Apartment.is_deleted == False)
            .order_by(ApartDetail.apt_detail_id)
        )
        mappings = mapping_result.all()
        logger.info(f"   총 {len(mappings)}개의 매핑 확인")
        
        # 5. 불일치 감지 (주소에 아파트 이름이 포함되어 있는지 확인)
        logger.info("\n5️⃣  매핑 정확성 검증 (주소 기반)")
        mismatches: List[Dict] = []
        correct_mappings = 0
        
        for mapping in mappings:
            detail_apt_id = mapping.detail_apt_id
            apartment_apt_id = mapping.apartment_apt_id
            apt_name = mapping.apt_name
            road_address = mapping.road_address or ""
            jibun_address = mapping.jibun_address or ""
            
            # 주소에 아파트 이름이 포함되어 있는지 확인
            clean_apt_name = apt_name.replace(" ", "").replace("-", "")
            clean_road = road_address.replace(" ", "").replace("-", "")
            clean_jibun = jibun_address.replace(" ", "").replace("-", "")
            
            is_match = (
                clean_apt_name in clean_road or 
                clean_apt_name in clean_jibun or
                clean_road in clean_apt_name or
                clean_jibun in clean_apt_name
            )
            
            # 아파트 이름이 너무 짧으면 검증 스킵
            if len(clean_apt_name) < 2:
                is_match = True
            
            if not is_match:
                mismatches.append({
                    'detail_apt_id': detail_apt_id,
                    'detail_apt_id_fk': detail_apt_id,
                    'apartment_apt_id': apartment_apt_id,
                    'apt_name': apt_name,
                    'road_address': road_address,
                    'jibun_address': jibun_address,
                    'gap': apartment_apt_id - detail_apt_id
                })
            else:
                correct_mappings += 1
        
        logger.info(f"   ✅ 정확한 매핑: {correct_mappings}개")
        logger.info(f"   ⚠️  의심스러운 매핑: {len(mismatches)}개")
        
        # 6. 불일치 패턴 분석
        if mismatches:
            logger.info("\n6️⃣  불일치 패턴 분석")
            
            # Gap별 그룹화
            gap_groups = defaultdict(list)
            for mismatch in mismatches:
                gap = mismatch['gap']
                gap_groups[gap].append(mismatch)
            
            logger.info("   Gap별 분포:")
            for gap in sorted(gap_groups.keys()):
                count = len(gap_groups[gap])
                logger.info(f"      차이 {gap:+d}: {count}개")
                if gap == 2:
                    logger.info(f"         ⚠️  차이 +2 패턴 발견! (apart_details의 apt_id가 apartments보다 2 작음)")
                    # 예시 출력
                    for example in gap_groups[gap][:3]:
                        logger.info(f"         예시: {example['apt_name']} - detail FK: {example['detail_apt_id_fk']}, apt ID: {example['apartment_apt_id']}")
            
            # 7. 문제 진단
            logger.info("\n7️⃣  문제 진단")
            logger.info("=" * 80)
            
            if 2 in gap_groups and len(gap_groups[2]) > 0:
                logger.info("🔴 문제 발견: apart_details의 apt_id가 apartments의 apt_id보다 2 작습니다.")
                logger.info("")
                logger.info("가능한 원인:")
                logger.info("  1. apartments 테이블에서 일부 레코드가 삭제되었을 가능성")
                logger.info("     - apt_id가 5418, 5420인 레코드가 삭제되었다면")
                logger.info("     - apart_details는 5417, 5419를 참조하지만")
                logger.info("     - 실제 apartments는 5417, 5419, 5421이 존재")
                logger.info("")
                logger.info("  2. 데이터 수집 순서 문제")
                logger.info("     - apartments 수집 후 일부 레코드가 삭제됨")
                logger.info("     - apart_details는 삭제 전 apt_id를 참조")
                logger.info("")
                logger.info("해결 방법:")
                logger.info("  - fix_data_mismatch.py 스크립트 실행 (자동 수정)")
                logger.info("  - 또는 수동으로 apart_details의 apt_id를 +2 조정")
            else:
                logger.info("✅ 일관된 패턴이 발견되지 않았습니다.")
                logger.info("   다른 원인을 확인해야 할 수 있습니다.")
            
            logger.info("=" * 80)
        
        # 8. apart_details가 참조하는 apt_id 중 존재하지 않는 것 확인
        logger.info("\n8️⃣  존재하지 않는 apt_id 참조 확인")
        orphan_result = await db.execute(
            select(ApartDetail.apt_id, func.count(ApartDetail.apt_detail_id).label('count'))
            .outerjoin(Apartment, ApartDetail.apt_id == Apartment.apt_id)
            .where(Apartment.apt_id.is_(None))
            .where(ApartDetail.is_deleted == False)
            .group_by(ApartDetail.apt_id)
        )
        orphans = orphan_result.all()
        if orphans:
            logger.info(f"   ⚠️  {len(orphans)}개의 존재하지 않는 apt_id 참조 발견")
            for orphan in orphans[:10]:
                logger.info(f"      apt_id {orphan.apt_id}: {orphan.count}개 상세정보")
        else:
            logger.info("   ✅ 모든 apart_details가 유효한 apartments를 참조")
    
    await engine.dispose()
    logger.info("\n✅ 분석 완료")


if __name__ == "__main__":
    asyncio.run(analyze_apt_id_mismatch())
