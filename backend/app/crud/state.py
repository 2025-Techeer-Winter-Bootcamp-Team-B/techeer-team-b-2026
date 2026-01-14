"""
지역 정보 CRUD

데이터베이스 작업을 담당하는 레이어
"""
from typing import Optional, List
from sqlalchemy import select, or_, func
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
)

from app.crud.base import CRUDBase
from app.models.state import State
from app.schemas.state import StateCreate, StateUpdate


class CRUDState(CRUDBase[State, StateCreate, StateUpdate]):
    """
    지역 정보 CRUD 클래스
    
    State 모델에 대한 데이터베이스 작업을 수행합니다.
    """
    
    async def get_by_region_code(
        self,
        db: AsyncSession,
        *,
        region_code: str
    ) -> Optional[State]:
        """
        지역코드로 지역 정보 조회
        
        Args:
            db: 데이터베이스 세션
            region_code: 지역코드 (10자리)
        
        Returns:
            State 객체 또는 None
        """
        result = await db.execute(
            select(State)
            .where(State.region_code == region_code)
            .where(State.is_deleted == False)
        )
        return result.scalar_one_or_none()
    
    async def find_by_region_code_prefix(
        self,
        db: AsyncSession,
        *,
        region_code_prefix: str,
        exact_length: Optional[int] = None
    ) -> Optional[State]:
        """
        지역코드 접두사로 지역 정보 조회 (부분 매칭)
        
        법정동 코드가 정확히 매칭되지 않을 때, 상위 레벨 지역을 찾기 위해 사용합니다.
        
        Args:
            db: 데이터베이스 세션
            region_code_prefix: 지역코드 접두사 (예: '29170' = 시군구 코드)
            exact_length: 정확한 길이 (예: 5면 시군구 레벨만 찾음)
        
        Returns:
            State 객체 또는 None
        """
        query = select(State).where(State.is_deleted == False)
        
        if exact_length:
            # 정확한 길이로 시작하는 코드 찾기
            query = query.where(
                State.region_code.like(f"{region_code_prefix}%")
            ).where(
                db.func.length(State.region_code) == exact_length
            )
        else:
            # 접두사로 시작하는 코드 찾기 (가장 짧은 것 우선 = 가장 상위 레벨)
            query = query.where(
                State.region_code.like(f"{region_code_prefix}%")
            ).order_by(
                db.func.length(State.region_code).asc()
            )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_city_name(
        self,
        db: AsyncSession,
        *,
        city_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[State]:
        """
        시도명으로 지역 목록 조회
        
        Args:
            db: 데이터베이스 세션
            city_name: 시도명 (예: 서울특별시)
            skip: 건너뛸 레코드 수
            limit: 가져올 레코드 수
        
        Returns:
            State 객체 목록
        """
        result = await db.execute(
            select(State)
            .where(State.city_name == city_name)
            .where(State.is_deleted == False)
            .offset(skip)
            .limit(limit)
            .order_by(State.region_name)
        )
        return list(result.scalars().all())
    
    async def create_or_skip(
        self,
        db: AsyncSession,
        *,
        obj_in: StateCreate
    ) -> tuple[Optional[State], bool]:
        """
        지역 정보 생성 또는 건너뛰기
        
        이미 존재하는 region_code면 건너뛰고, 없으면 생성합니다.
        
        Args:
            db: 데이터베이스 세션
            obj_in: 생성할 지역 정보
        
        Returns:
            (State 객체 또는 None, 생성 여부)
            - (State, True): 새로 생성됨
            - (State, False): 이미 존재하여 건너뜀
            - (None, False): 오류 발생
        """
        try:
            # 중복 확인
            existing = await self.get_by_region_code(db, region_code=obj_in.region_code)
            if existing:
                return existing, False
            
            # 새로 생성
            db_obj = State(**obj_in.model_dump())
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj, True
        except Exception as e:
            # 오류 발생 시 롤백하여 트랜잭션을 정리
            try:
                await db.rollback()
            except:
                pass  # 롤백 실패는 무시 (이미 롤백된 경우 등)
            raise e
    
    async def search_locations(
        self,
        db: AsyncSession,
        *,
        query: str,
        location_type: Optional[str] = None,
        limit: int = 20
    ) -> List[State]:
        """
        지역 검색 (시/군/구/동)
        
        region_name 또는 city_name에 검색어가 포함되는 지역을 검색합니다.
        
        Args:
            db: 데이터베이스 세션
            query: 검색어 (최소 1글자)
            location_type: 지역 유형 필터 (sigungu: 시군구, dong: 동/리/면, None: 전체)
            limit: 반환할 결과 개수 (기본 20개)
        
        Returns:
            State 객체 목록
            
        Note:
            - 대소문자 구분 없이 검색 (ILIKE 사용)
            - 삭제되지 않은 지역만 검색
            - location_type 판단 기준:
              * sigungu: region_name에 "구", "시", "군" 포함 (단, "동"은 제외)
              * dong: region_name에 "동", "리", "면" 포함
            - 정렬: city_name 오름차순, region_name 오름차순
        """
        # 기본 쿼리: 삭제되지 않은 지역, 검색어 포함
        stmt = (
            select(State)
            .where(State.is_deleted == False)
            .where(
                or_(
                    State.region_name.ilike(f"%{query}%"),
                    State.city_name.ilike(f"%{query}%")
                )
            )
        )
        
        # 지역 유형 필터링
        if location_type == "sigungu":
            # 시군구만: "구", "시", "군" 포함하고 "동", "리", "면"은 제외
            stmt = stmt.where(
                (State.region_name.ilike("%구%") | 
                 State.region_name.ilike("%시%") | 
                 State.region_name.ilike("%군%"))
            ).where(
                ~State.region_name.ilike("%동%")
            ).where(
                ~State.region_name.ilike("%리%")
            ).where(
                ~State.region_name.ilike("%면%")
            )
        elif location_type == "dong":
            # 동/리/면만
            stmt = stmt.where(
                State.region_name.ilike("%동%") |
                State.region_name.ilike("%리%") |
                State.region_name.ilike("%면%")
            )
        
        # 정렬 및 제한
        stmt = stmt.order_by(
            State.city_name.asc(),
            State.region_name.asc()
        ).limit(limit)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())


# CRUD 인스턴스 생성
state = CRUDState(State)
