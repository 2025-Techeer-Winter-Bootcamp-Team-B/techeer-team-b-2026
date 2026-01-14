"""
검색 서비스

아파트 검색 및 지역 검색 비즈니스 로직을 담당하는 서비스 레이어
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.apartment import apartment as apartment_crud
from app.crud.state import state as state_crud
from app.crud.recent_search import recent_search as recent_search_crud
from app.models.apartment import Apartment
from app.models.recent_search import SearchType


class SearchService:
    """
    검색 서비스 클래스
    
    아파트 검색 관련 비즈니스 로직을 처리합니다.
    """
    
    async def search_apartments(
        self,
        db: AsyncSession,
        *,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        아파트명으로 검색
        
        검색어를 포함하는 아파트 목록을 반환합니다.
        DB에서 조회한 후 응답 형식에 맞게 변환합니다.
        
        Args:
            db: 데이터베이스 세션
            query: 검색어 (최소 2글자)
            limit: 반환할 결과 개수 (기본 10개, 최대 50개)
        
        Returns:
            검색 결과 목록 (dict 리스트)
        
        Note:
            - 대소문자 구분 없이 검색 (ILIKE 사용)
            - 삭제되지 않은 아파트만 검색
            - 아파트명 오름차순 정렬
        """
        # CRUD 레이어를 통해 DB에서 검색
        apartments = await apartment_crud.search_by_name(
            db,
            query=query,
            limit=limit
        )
        
        # 응답 형식에 맞게 데이터 변환
        # ERD 설계 (.agent/data.sql)에 따라 APARTMENTS 테이블에는 기본 정보만 있음
        # - apt_id, region_id, apt_name, kapt_code, is_available, created_at, updated_at, is_deleted
        # 상세 정보(주소, 좌표 등)는 APART_DETAILS 테이블에 있음
        results = []
        for apt in apartments:
            result_item = {
                "apt_id": apt.apt_id,
                "apt_name": apt.apt_name,
            }
            
            # kapt_code 추가 (있는 경우)
            if hasattr(apt, 'kapt_code') and apt.kapt_code:
                result_item["kapt_code"] = apt.kapt_code
            
            # region_id 추가 (있는 경우)
            if hasattr(apt, 'region_id'):
                result_item["region_id"] = apt.region_id
            
            # 상세 정보는 APART_DETAILS 테이블에 있으므로, 필요시 JOIN하여 가져올 수 있음
            # 현재는 기본 정보만 반환 (시스템 다이어그램 구조대로)
            # 주소와 위치 정보는 APART_DETAILS 테이블에서 가져와야 함
            result_item["address"] = None
            result_item["location"] = None
            
            results.append(result_item)
        
        return results
    
    async def search_locations(
        self,
        db: AsyncSession,
        *,
        query: str,
        location_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        지역 검색 (시/군/구/동)
        
        검색어를 포함하는 지역 목록을 반환합니다.
        DB에서 조회한 후 응답 형식에 맞게 변환합니다.
        
        Args:
            db: 데이터베이스 세션
            query: 검색어 (최소 1글자)
            location_type: 지역 유형 필터 (sigungu: 시군구, dong: 동/리/면, None: 전체)
            limit: 반환할 결과 개수 (기본 20개)
        
        Returns:
            검색 결과 목록 (dict 리스트)
        
        Note:
            - 대소문자 구분 없이 검색 (ILIKE 사용)
            - 삭제되지 않은 지역만 검색
            - 정렬: 시도명, 지역명 오름차순
        """
        # CRUD 레이어를 통해 DB에서 검색
        states = await state_crud.search_locations(
            db,
            query=query,
            location_type=location_type,
            limit=limit
        )
        
        # 응답 형식에 맞게 데이터 변환
        results = []
        for state in states:
            # 지역 유형 판단
            # region_name에 "동", "리", "면"이 포함되면 "dong", 아니면 "sigungu"
            if any(keyword in state.region_name for keyword in ["동", "리", "면"]):
                loc_type = "dong"
            else:
                loc_type = "sigungu"
            
            # 전체 지역명 생성 (예: "서울특별시 강남구")
            full_name = f"{state.city_name} {state.region_name}"
            
            result_item = {
                "region_id": state.region_id,
                "region_name": state.region_name,
                "region_code": state.region_code,
                "city_name": state.city_name,
                "full_name": full_name,
                "location_type": loc_type
            }
            
            results.append(result_item)
        
        return results
    
    async def get_recent_searches(
        self,
        db: AsyncSession,
        *,
        account_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        최근 검색어 조회
        
        사용자가 최근에 검색한 기록을 시간순(최신순)으로 반환합니다.
        
        Args:
            db: 데이터베이스 세션
            account_id: 계정 ID
            limit: 반환할 최대 개수 (기본 10개, 최대 50개)
        
        Returns:
            검색 기록 목록 (dict 리스트)
        
        Note:
            - 최신순으로 정렬
            - 삭제되지 않은 검색 기록만 조회
        """
        # CRUD 레이어를 통해 DB에서 조회
        searches = await recent_search_crud.get_by_user(
            db,
            account_id=account_id,
            limit=limit
        )
        
        # 응답 형식에 맞게 데이터 변환
        results = []
        for search in searches:
            result_item = {
                "id": search.search_id,
                "query": search.query,
                "type": search.search_type.value,  # Enum을 문자열로 변환
                "searched_at": search.searched_at.isoformat() if search.searched_at else None
            }
            results.append(result_item)
        
        return results
    
    async def delete_recent_search(
        self,
        db: AsyncSession,
        *,
        search_id: int,
        account_id: int
    ) -> bool:
        """
        최근 검색어 삭제
        
        사용자의 특정 검색 기록을 삭제합니다.
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
        # CRUD 레이어를 통해 삭제
        return await recent_search_crud.delete_by_id(
            db,
            search_id=search_id,
            account_id=account_id
        )
    
    async def save_search(
        self,
        db: AsyncSession,
        *,
        account_id: int,
        query: str,
        search_type: SearchType
    ) -> Dict[str, Any]:
        """
        검색 기록 저장
        
        사용자가 검색한 기록을 저장합니다.
        중복된 검색어가 최근에 검색되었다면, 기존 레코드를 업데이트합니다.
        
        Args:
            db: 데이터베이스 세션
            account_id: 계정 ID
            query: 검색어
            search_type: 검색 유형 (apartment 또는 location)
        
        Returns:
            저장된 검색 기록 정보
        """
        # CRUD 레이어를 통해 저장
        search_record = await recent_search_crud.create_search(
            db,
            account_id=account_id,
            query=query,
            search_type=search_type
        )
        
        return {
            "search_id": search_record.search_id,
            "query": search_record.query,
            "search_type": search_record.search_type.value,
            "searched_at": search_record.searched_at.isoformat() if search_record.searched_at else None
        }


# 서비스 인스턴스 생성
search_service = SearchService()
