"""
최근 본 아파트 CRUD

데이터베이스 작업을 담당하는 레이어
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# 모든 모델을 import하여 SQLAlchemy 관계 설정이 제대로 작동하도록 함
from app.models import (  # noqa: F401
    Account,
    State,
    Apartment,
    ApartDetail,
    Sale,
    Rent,
    HouseScore,
    FavoriteLocation,
    FavoriteApartment,
    MyProperty,
    RecentSearch,
    RecentView,
)

from app.crud.base import CRUDBase
from app.models.recent_view import RecentView
from app.schemas.recent_view import RecentViewCreate


class CRUDRecentView(CRUDBase[RecentView, RecentViewCreate, dict]):
    """
    최근 본 아파트 CRUD 클래스
    
    RecentView 모델에 대한 데이터베이스 작업을 수행합니다.
    """
    
    async def get_by_account(
        self,
        db: AsyncSession,
        *,
        account_id: int,
        limit: int = 20
    ) -> List[RecentView]:
        """
        사용자별 최근 본 아파트 목록 조회
        
        Args:
            db: 데이터베이스 세션
            account_id: 계정 ID
            limit: 가져올 레코드 수 (기본 20개, 최대 50개)
        
        Returns:
            RecentView 객체 목록 (최신순, Apartment 관계 포함)
        """
        result = await db.execute(
            select(RecentView)
            .where(
                and_(
                    RecentView.account_id == account_id,
                    RecentView.is_deleted == False
                )
            )
            .options(
                selectinload(RecentView.apartment).selectinload(Apartment.region)  # Apartment와 State 관계 로드
            )
            .order_by(RecentView.viewed_at.desc().nulls_last())
            .limit(min(limit, 50))
        )
        return list(result.scalars().all())
    
    async def create_or_update(
        self,
        db: AsyncSession,
        *,
        account_id: int,
        apt_id: int
    ) -> RecentView:
        """
        최근 본 아파트 생성 또는 업데이트
        
        같은 아파트를 이미 본 기록이 있으면 기존 레코드의 viewed_at을 업데이트하고,
        없으면 새로 생성합니다.
        
        Args:
            db: 데이터베이스 세션
            account_id: 계정 ID
            apt_id: 아파트 ID
        
        Returns:
            RecentView 객체
        """
        # 같은 아파트를 본 기록이 있는지 확인
        existing = await db.execute(
            select(RecentView)
            .where(
                and_(
                    RecentView.account_id == account_id,
                    RecentView.apt_id == apt_id,
                    RecentView.is_deleted == False
                )
            )
        )
        existing_view = existing.scalar_one_or_none()
        
        now = datetime.utcnow()
        
        if existing_view:
            # 기존 레코드가 있으면 viewed_at만 업데이트 (최신순 정렬을 위해)
            existing_view.viewed_at = now
            existing_view.updated_at = now
            db.add(existing_view)
            await db.commit()
            await db.refresh(existing_view)
            # Apartment 관계도 함께 로드
            await db.refresh(existing_view, ["apartment"])
            return existing_view
        else:
            # 새 레코드 생성
            db_obj = RecentView(
                account_id=account_id,
                apt_id=apt_id,
                viewed_at=now,
                created_at=now,
                updated_at=now,
                is_deleted=False
            )
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            # Apartment 관계도 함께 로드
            await db.refresh(db_obj, ["apartment"])
            return db_obj
    
    async def count_by_account(
        self,
        db: AsyncSession,
        *,
        account_id: int
    ) -> int:
        """
        사용자별 최근 본 아파트 개수 조회
        
        Args:
            db: 데이터베이스 세션
            account_id: 계정 ID
        
        Returns:
            최근 본 아파트 개수
        """
        result = await db.execute(
            select(func.count(RecentView.view_id))
            .where(
                and_(
                    RecentView.account_id == account_id,
                    RecentView.is_deleted == False
                )
            )
        )
        return result.scalar() or 0
    
    async def delete_all_by_account(
        self,
        db: AsyncSession,
        *,
        account_id: int
    ) -> int:
        """
        사용자별 최근 본 아파트 전체 삭제 (소프트 삭제)
        
        Args:
            db: 데이터베이스 세션
            account_id: 계정 ID
        
        Returns:
            삭제된 레코드 수
        """
        from datetime import datetime
        now = datetime.utcnow()
        
        result = await db.execute(
            select(RecentView)
            .where(
                and_(
                    RecentView.account_id == account_id,
                    RecentView.is_deleted == False
                )
            )
        )
        views = result.scalars().all()
        
        deleted_count = 0
        for view in views:
            view.is_deleted = True
            view.updated_at = now
            db.add(view)
            deleted_count += 1
        
        await db.commit()
        return deleted_count
    
    async def delete_by_id(
        self,
        db: AsyncSession,
        *,
        view_id: int,
        account_id: int
    ) -> bool:
        """
        특정 최근 본 아파트 기록 삭제 (소프트 삭제)
        
        Args:
            db: 데이터베이스 세션
            view_id: 조회 기록 ID
            account_id: 계정 ID (본인 확인용)
        
        Returns:
            삭제 성공 여부
        """
        from datetime import datetime
        now = datetime.utcnow()
        
        result = await db.execute(
            select(RecentView)
            .where(
                and_(
                    RecentView.view_id == view_id,
                    RecentView.account_id == account_id,
                    RecentView.is_deleted == False
                )
            )
        )
        view = result.scalar_one_or_none()
        
        if not view:
            return False
        
        view.is_deleted = True
        view.updated_at = now
        db.add(view)
        await db.commit()
        return True


# CRUD 인스턴스 생성
recent_view = CRUDRecentView(RecentView)
