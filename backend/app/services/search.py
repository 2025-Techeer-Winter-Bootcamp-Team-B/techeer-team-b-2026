"""
검색 서비스

아파트 검색 비즈니스 로직을 담당하는 서비스 레이어
"""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.apartment import apartment as apartment_crud
from app.models.apartment import Apartment


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


# 서비스 인스턴스 생성
search_service = SearchService()
