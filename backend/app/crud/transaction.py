"""
거래 내역 CRUD

매매(Sale)와 전월세(Rent) 거래 내역을 관리하는 CRUD
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy import select, and_, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.sale import Sale
from app.schemas.transaction import SaleCreate


class CRUDSale(CRUDBase[Sale, SaleCreate, dict]):
    """
    매매 거래 정보 CRUD
    
    기본 CRUD + 매매 거래 전용 기능:
    - 아파트별 거래 내역 조회
    - 날짜 범위로 거래 내역 조회
    - 가격 범위로 거래 내역 조회
    - 취소되지 않은 거래만 조회
    """

    async def get_by_apartment(
        self,
        db: AsyncSession,
        *,
        apt_id: int,
        skip: int = 0,  # 페이지네이션: 건너뛸 레코드 수 (offset)
        limit: int = 100
    ) -> List[Sale]:
        """특정 아파트의 매매 거래 내역 조회"""
        result = await db.execute(
            select(Sale)
            .where(Sale.apt_id == apt_id)
            .where(Sale.is_deleted.is_(False))  # 삭제되지 않은 것만
            .order_by(Sale.contract_date.desc())  # 최신순
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_date_range(
        self,
        db: AsyncSession,
        *,
        apt_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Sale]:
        """
        날짜 범위로 매매 거래 내역 조회
        
        Args:
            apt_id: 아파트 ID (선택, None이면 전체)
            start_date: 시작일 (선택)
            end_date: 종료일 (선택)
        """
        query = select(Sale).where(Sale.is_deleted.is_(False))
        
        if apt_id:
            query = query.where(Sale.apt_id == apt_id)
        if start_date:
            query = query.where(Sale.contract_date >= start_date)
        if end_date:
            query = query.where(Sale.contract_date <= end_date)
        
        result = await db.execute(
            query
            .order_by(Sale.contract_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_price_range(
        self,
        db: AsyncSession,
        *,
        apt_id: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Sale]:
        """
        가격 범위로 매매 거래 내역 조회
        
        Note: `and_()`는 여러 조건을 AND로 묶을 때 사용합니다.
        예: WHERE A AND B AND C
        """
        query = select(Sale).where(
            and_(
                Sale.is_deleted.is_(False),
                Sale.is_canceled.is_(False),  # 취소되지 않은 거래만
                Sale.trans_price.isnot(None)  # 가격 정보가 있는 것만
            )
        )
        
        if apt_id:
            query = query.where(Sale.apt_id == apt_id)
        if min_price:
            query = query.where(Sale.trans_price >= min_price)
        if max_price:
            query = query.where(Sale.trans_price <= max_price)
        
        result = await db.execute(
            query
            .order_by(Sale.trans_price.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_active_transactions(
        self,
        db: AsyncSession,
        *,
        apt_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Sale]:
        """취소되지 않은 활성 거래만 조회"""
        result = await db.execute(
            select(Sale)
            .where(
                and_(
                    Sale.apt_id == apt_id,
                    Sale.is_canceled.is_(False),
                    Sale.is_deleted.is_(False)
                )
            )
            .order_by(Sale.contract_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def check_duplicate(
        self,
        db: AsyncSession,
        *,
        apt_id: int,
        contract_date: Optional[date],
        trans_price: Optional[int] = None,
        exclusive_area: Optional[float] = None,
        floor: Optional[int] = None
    ) -> Optional[Sale]:
        """
        중복 거래 체크
        
        같은 아파트, 같은 날짜, 같은 가격/면적/층인 거래가 이미 있는지 확인
        """
        if not contract_date:
            return None
        
        query = select(Sale).where(
            and_(
                Sale.apt_id == apt_id,
                Sale.contract_date == contract_date,
                Sale.is_deleted.is_(False)
            )
        )
        
        # 선택적 조건 추가
        if trans_price:
            query = query.where(Sale.trans_price == trans_price)
        if exclusive_area:
            query = query.where(Sale.exclusive_area == exclusive_area)
        if floor:
            query = query.where(Sale.floor == floor)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_or_skip(
        self,
        db: AsyncSession,
        *,
        obj_in: SaleCreate
    ) -> tuple[Optional[Sale], bool]:
        """
        매매 거래 정보 생성 또는 건너뛰기
        
        중복 거래가 있으면 건너뛰고, 없으면 생성합니다.
        
        Returns:
            (Sale 객체 또는 None, 생성 여부)
            - (Sale, True): 새로 생성됨
            - (Sale, False): 이미 존재하여 건너뜀
        """
        # 중복 확인
        existing = await self.check_duplicate(
            db,
            apt_id=obj_in.apt_id,
            contract_date=obj_in.contract_date,
            trans_price=obj_in.trans_price,
            exclusive_area=obj_in.exclusive_area,
            floor=obj_in.floor
        )
        
        if existing:
            return existing, False
        
        # 새로 생성
        try:
            db_obj = Sale(**obj_in.model_dump())
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj, True
        except Exception as e:
            await db.rollback()
            raise e


# 싱글톤 인스턴스
sale = CRUDSale(Sale)

