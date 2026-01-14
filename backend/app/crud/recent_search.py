"""
최근 검색어 CRUD

데이터베이스 작업을 담당하는 레이어
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

# 모든 모델을 import하여 SQLAlchemy 관계 설정이 제대로 작동하도록 함
from app.models import (  # noqa: F401
    Account,
    State,
    Apartment,
    Sale,
    Rent,
    HouseScore,
    FavoriteLocation,
    FavoriteApartment,
    MyProperty,
    RecentSearch,
)

from app.crud.base import CRUDBase
from app.models.recent_search import RecentSearch, SearchType
from app.schemas.recent_search import RecentSearchCreate, RecentSearchUpdate


class CRUDRecentSearch(CRUDBase[RecentSearch, RecentSearchCreate, RecentSearchUpdate]):
    """
    최근 검색어 CRUD 클래스
    
    RecentSearch 모델에 대한 데이터베이스 작업을 수행합니다.
    """
    
    async def get_by_user(
        self,
        db: AsyncSession,
        *,
        account_id: int,
        limit: int = 10,
        skip: int = 0
    ) -> List[RecentSearch]:
        """
        사용자의 최근 검색어 목록 조회
        
        Args:
            db: 데이터베이스 세션
            account_id: 계정 ID
            limit: 가져올 레코드 수 (기본 10개)
            skip: 건너뛸 레코드 수
        
        Returns:
            RecentSearch 객체 목록 (최신순)
        """
        result = await db.execute(
            select(RecentSearch)
            .where(RecentSearch.account_id == account_id)
            .where(RecentSearch.is_deleted == False)
            .order_by(desc(RecentSearch.searched_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def create_search(
        self,
        db: AsyncSession,
        *,
        account_id: int,
        query: str,
        search_type: SearchType
    ) -> RecentSearch:
        """
        최근 검색어 생성
        
        중복된 검색어가 최근에 검색되었다면, 기존 레코드를 업데이트합니다.
        (같은 사용자가 같은 검색어를 다시 검색한 경우)
        
        Args:
            db: 데이터베이스 세션
            account_id: 계정 ID
            query: 검색어
            search_type: 검색 유형
        
        Returns:
            생성된 또는 업데이트된 RecentSearch 객체
        """
        # 최근 같은 검색어가 있는지 확인 (최근 1시간 이내)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        existing = await db.execute(
            select(RecentSearch)
            .where(RecentSearch.account_id == account_id)
            .where(RecentSearch.query == query)
            .where(RecentSearch.search_type == search_type)
            .where(RecentSearch.is_deleted == False)
            .where(RecentSearch.searched_at >= one_hour_ago)
            .order_by(desc(RecentSearch.searched_at))
            .limit(1)
        )
        existing_search = existing.scalar_one_or_none()
        
        if existing_search:
            # 기존 레코드의 검색 시간만 업데이트
            existing_search.searched_at = datetime.utcnow()
            existing_search.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(existing_search)
            return existing_search
        
        # 새 레코드 생성
        db_obj = RecentSearch(
            account_id=account_id,
            query=query,
            search_type=search_type,
            searched_at=datetime.utcnow()
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete_by_id(
        self,
        db: AsyncSession,
        *,
        search_id: int,
        account_id: int
    ) -> bool:
        """
        최근 검색어 삭제 (소프트 삭제)
        
        본인의 검색 기록만 삭제할 수 있습니다.
        
        Args:
            db: 데이터베이스 세션
            search_id: 삭제할 검색어 ID
            account_id: 계정 ID (본인 확인용)
        
        Returns:
            삭제 성공 여부
        
        Raises:
            ValueError: 검색어를 찾을 수 없거나 본인의 검색 기록이 아닌 경우
        """
        result = await db.execute(
            select(RecentSearch)
            .where(RecentSearch.search_id == search_id)
            .where(RecentSearch.is_deleted == False)
        )
        search_record = result.scalar_one_or_none()
        
        if not search_record:
            raise ValueError("검색어를 찾을 수 없습니다.")
        
        if search_record.account_id != account_id:
            raise ValueError("본인의 검색 기록만 삭제할 수 있습니다.")
        
        # 소프트 삭제
        search_record.is_deleted = True
        search_record.updated_at = datetime.utcnow()
        await db.commit()
        return True


# CRUD 인스턴스 생성
recent_search = CRUDRecentSearch(RecentSearch)
