import logging
import asyncio
from typing import List, Tuple, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal

# Services
from app.services import statistics_service

# Endpoints (Treating them as services for now)
from app.api.v1.endpoints.dashboard import (
    get_dashboard_summary,
    get_dashboard_rankings,
    get_regional_heatmap,
    get_regional_trends
)

logger = logging.getLogger(__name__)

async def preload_all_statistics():
    """
    서버 시작 시 모든 통계 데이터를 미리 캐싱합니다.
    
    대상:
    1. 대시보드 (요약, 랭킹, 히트맵, 추이)
    2. 통계 (RVOL, 4분면, HPI, HPI 히트맵)
    
    이 작업은 백그라운드에서 실행됩니다.
    """
    logger.info(" [Warmup] 통계 데이터 전체 캐싱 시작...")
    
    success_count = 0
    fail_count = 0
    
    async with AsyncSessionLocal() as db:
        # 1. Statistics Service (RVOL, Quadrant, HPI) - Hashed Keys
        stats_tasks = []
        
        # RVOL (Sale/Rent, Periods)
        for trans_type in ["sale", "rent"]:
            # 기본 기간 (6, 6)
            stats_tasks.append(
                ("rvol", statistics_service.get_rvol(db, trans_type, 6, 6))
            )
            # 추가 기간 (3, 3) - 빠르면 좋음
            stats_tasks.append(
                ("rvol", statistics_service.get_rvol(db, trans_type, 3, 3))
            )
            
        # Quadrant (Periods)
        for period in [1, 2, 3, 6]:
            stats_tasks.append(
                ("quadrant", statistics_service.get_quadrant(db, period))
            )
            
        # HPI (Index Types, Months)
        for index_type in ["APT", "ALL"]:
            for months in [12, 24, 36, 60]:
                stats_tasks.append(
                    ("hpi", statistics_service.get_hpi(db, None, index_type, months))
                )
        
        # HPI Heatmap
        for index_type in ["APT", "ALL"]:
            stats_tasks.append(
                ("hpi_heatmap", statistics_service.get_hpi_heatmap(db, index_type))
            )
            
        # Statistics Summary (Combine RVOL + Quadrant)
        for trans_type in ["sale", "rent"]:
            stats_tasks.append(
                ("stat_summary", statistics_service.get_statistics_summary(db, trans_type, 6, 6, 2))
            )

        # 2. Dashboard Endpoints (Summary, Rankings, etc.) - Simple Keys
        dash_tasks = []
        
        # Dashboard Summary & Trends
        for trans_type in ["sale", "jeonse"]:
            for months in [6, 12]:
                dash_tasks.append(
                    ("dash_summary", get_dashboard_summary(trans_type, months, db))
                )
                dash_tasks.append(
                    ("dash_trends", get_regional_trends(trans_type, months, db))
                )
            
            # Regional Heatmap
            dash_tasks.append(
                ("dash_heatmap", get_regional_heatmap(trans_type, 3, db))
            )
            
            # Rankings
            dash_tasks.append(
                ("dash_rankings", get_dashboard_rankings(trans_type, 7, 3, db))
            )
            dash_tasks.append(
                ("dash_rankings", get_dashboard_rankings(trans_type, 30, 6, db))
            )

        # Execute All Tasks
        all_tasks = stats_tasks + dash_tasks
        
        # 순차적으로 실행하지 않고 병렬로 실행하되, DB 커넥션 풀 고갈 방지를 위해 세마포어 사용
        # AWS t4g.micro는 CPU가 약하므로 너무 많은 병렬 처리는 오히려 독이 될 수 있음
        semaphore = asyncio.Semaphore(5)  # 동시에 5개까지만 실행
        
        async def run_task(name, coroutine):
            nonlocal success_count, fail_count
            async with semaphore:
                try:
                    await coroutine
                    # logger.info(f" [Warmup] {name} 완료")
                    return True
                except Exception as e:
                    logger.warning(f" [Warmup] {name} 실패: {e}")
                    return False

        results = await asyncio.gather(*[run_task(name, coro) for name, coro in all_tasks])
        
        success_count = sum(1 for r in results if r)
        fail_count = sum(1 for r in results if not r)
        
    logger.info(f" [Warmup] 통계 데이터 캐싱 완료 - 성공: {success_count}, 실패: {fail_count}")
