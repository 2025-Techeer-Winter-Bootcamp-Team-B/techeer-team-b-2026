"""
검색 관련 API 엔드포인트

담당자: 박찬영
담당 기능:
- 최근 검색어 조회 (GET /search/recent) - P1
- 최근 검색어 삭제 (DELETE /search/recent/{id}) - P1

참고:
- 아파트명 검색: search_apart.py 참고
- 지역 검색: search_region.py 참고

레이어드 아키텍처:
- API Layer (이 파일): 요청/응답 처리
- Service Layer (services/search.py): 비즈니스 로직
- CRUD Layer: DB 작업
- Model Layer: 데이터 모델
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.v1.deps import get_db, get_current_user
from app.models.account import Account
from app.models.apartment import Apartment
from app.models.apart_detail import ApartDetail
from app.models.state import State
from app.services.search import search_service

router = APIRouter()


@router.get(
    "/apartments",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    tags=["🔍 Search (검색)"],
    summary="아파트명 검색",
    description="아파트명으로 검색합니다. 검색창에 글자를 입력할 때마다(2글자 이상) 자동완성 결과를 반환합니다.",
    responses={
        200: {"description": "검색 성공"},
        400: {"description": "검색어가 2글자 미만인 경우"},
        422: {"description": "입력값 검증 실패"}
    }
)
async def search_apartments(
    q: str = Query(..., min_length=2, description="검색어 (2글자 이상)"),
    limit: int = Query(10, ge=1, le=50, description="결과 개수 (최대 50개)"),
    db: AsyncSession = Depends(get_db)
):
    """
    아파트명 검색 API - 자동완성
    
    검색창에 입력한 글자로 시작하거나 포함하는 아파트 목록을 반환합니다.
    
    Args:
        q: 검색어 (최소 2글자)
        limit: 반환할 결과 개수 (기본 10개, 최대 50개)
        db: 데이터베이스 세션
    
    Returns:
        {
            "success": true,
            "data": {
                "results": [
                    {
                        "apt_id": int,
                        "apt_name": str,
                        "address": str,
                        "sigungu_name": str,
                        "location": {"lat": float, "lng": float}
                    }
                ]
            },
            "meta": {
                "query": str,
                "count": int
            }
        }
    """
    # 아파트명 검색 쿼리
    stmt = (
        select(
            Apartment.apt_id,
            Apartment.apt_name,
            ApartDetail.road_address,
            ApartDetail.jibun_address,
            State.city_name,
            State.region_name,
            func.ST_X(ApartDetail.geometry).label('lng'),
            func.ST_Y(ApartDetail.geometry).label('lat')
        )
        .join(ApartDetail, Apartment.apt_id == ApartDetail.apt_id)
        .join(State, Apartment.region_id == State.region_id)
        .where(Apartment.apt_name.like(f"%{q}%"))
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    apartments = result.all()
    
    results = []
    for apt in apartments:
        # 주소 조합 (도로명 우선, 없으면 지번)
        address = apt.road_address if apt.road_address else apt.jibun_address
        
        # 시군구 이름 조합 (예: 서울특별시 강남구)
        sigungu_full = f"{apt.city_name} {apt.region_name}"
        
        results.append({
            "apt_id": apt.apt_id,
            "apt_name": apt.apt_name,
            "address": address,
            "sigungu_name": sigungu_full,
            "location": {
                "lat": apt.lat if apt.lat else 0.0,
                "lng": apt.lng if apt.lng else 0.0
            },
            # 프론트엔드 호환성을 위해 추가 필드 (가격 등은 현재 DB에 없으므로 더미/추후 조인)
            "price": "시세 정보 없음"  
        })
    
    return {
        "success": True,
        "data": {
            "results": results
        },
        "meta": {
            "query": q,
            "count": len(results)
        }
    }


@router.get(
    "/recent",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    tags=["🔍 Search (검색)"],
    summary="최근 검색어 조회",
    description="로그인한 사용자의 최근 검색어 목록을 조회합니다. 검색창을 탭했을 때 이전 검색 기록을 보여줍니다.",
    responses={
        200: {"description": "조회 성공"},
        401: {"description": "로그인이 필요합니다"}
    }
)
async def get_recent_searches(
    limit: int = Query(10, ge=1, le=50, description="최대 개수 (기본 10개, 최대 50개)"),
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    최근 검색어 조회 API
    
    로그인한 사용자가 최근에 검색한 기록을 시간순(최신순)으로 반환합니다.
    아파트 검색과 지역 검색을 모두 포함합니다.
    
    Args:
        limit: 반환할 최대 개수 (기본 10개, 최대 50개)
        current_user: 현재 로그인한 사용자 (의존성 주입)
        db: 데이터베이스 세션
    
    Returns:
        {
            "success": true,
            "data": {
                "recent_searches": [
                    {
                        "id": int,
                        "query": str,
                        "type": str,  # "apartment" 또는 "location"
                        "searched_at": str  # ISO 8601 형식
                    }
                ]
            }
        }
    
    Raises:
        HTTPException: 로그인이 필요한 경우 401 에러
    """
    # Service 레이어를 통해 비즈니스 로직 처리
    # 엔드포인트는 최소한의 로직만 포함하고, 복잡한 처리는 Service에 위임
    results = await search_service.get_recent_searches(
        db=db,
        account_id=current_user.account_id,
        limit=limit
    )
    
    # 공통 응답 형식으로 반환
    # 모든 API는 동일한 형식 ({success, data, meta})을 사용하여 일관성 유지
    return {
        "success": True,
        "data": {
            "recent_searches": results
        },
        "meta": {
            "count": len(results)
        }
    }


@router.delete(
    "/recent/{search_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    tags=["🔍 Search (검색)"],
    summary="최근 검색어 삭제",
    description="특정 최근 검색어를 삭제합니다. 사용자가 검색 기록을 개별적으로 삭제할 때 사용합니다.",
    responses={
        200: {"description": "삭제 성공"},
        401: {"description": "로그인이 필요합니다"},
        404: {"description": "검색어를 찾을 수 없습니다"}
    }
)
async def delete_recent_search(
    search_id: int,
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    최근 검색어 삭제 API
    
    로그인한 사용자의 특정 검색 기록을 삭제합니다.
    본인의 검색 기록만 삭제할 수 있습니다.
    
    Args:
        search_id: 삭제할 검색어 ID
        current_user: 현재 로그인한 사용자 (의존성 주입)
        db: 데이터베이스 세션
    
    Returns:
        {
            "success": true,
            "data": {
                "message": "검색어가 삭제되었습니다."
            }
        }
    
    Raises:
        HTTPException: 
            - 401: 로그인이 필요한 경우
            - 404: 검색어를 찾을 수 없거나 본인의 검색 기록이 아닌 경우
    """
    # Service 레이어를 통해 비즈니스 로직 처리
    # 엔드포인트는 최소한의 로직만 포함하고, 복잡한 처리는 Service에 위임
    try:
        await search_service.delete_recent_search(
            db=db,
            search_id=search_id,
            account_id=current_user.account_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SEARCH_NOT_FOUND",
                "message": str(e)
            }
        )
    
    # 공통 응답 형식으로 반환
    return {
        "success": True,
        "data": {
            "message": "검색어가 삭제되었습니다."
        }
    }
