"""
아파트명 검색 API 엔드포인트

담당자: 박찬영
담당 기능:
- 아파트명 검색 (GET /search/apartments) - P0
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.v1.deps import get_db
from app.models.apartment import Apartment

router = APIRouter()


@router.get(
    "/apartments",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="아파트명 검색 (자동완성)",
    description="아파트명으로 검색합니다. 검색창에 2글자 이상 입력 시 자동완성 결과를 반환합니다."
)
async def search_apartments(
    q: str = Query(
        ..., 
        min_length=2, 
        description="검색어 (2글자 이상)",
        example="래미안"
    ),
    limit: int = Query(
        10, 
        ge=1, 
        le=50, 
        description="결과 개수 (기본 10개, 최대 50개)"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    ## 아파트명 검색 API
    
    검색창에 입력한 글자를 포함하는 아파트 목록을 반환합니다.
    
    ### Query Parameters
    - **q**: 검색어 (최소 2글자)
    - **limit**: 반환할 결과 개수 (기본 10개, 최대 50개)
    
    ### Response
    - 성공: 아파트 목록 (이름, 주소, 위치 정보)
    - 실패: 422 (검색어가 2글자 미만)
    """
    # TODO: SearchService.search_apartments() 구현 후 서비스 레이어로 이동
    
    # 1. DB에서 아파트명 검색 (ILIKE: 대소문자 구분 없이 검색)
    result = await db.execute(
        select(Apartment)
        .where(Apartment.apt_name.ilike(f"%{q}%"))
        .order_by(Apartment.apt_name)
        .limit(limit)
    )
    apartments = result.scalars().all()
    
    # 2. 응답 데이터 구성
    results = [
        {
            "apt_id": apt.apt_id,
            "apt_name": apt.apt_name,
            "address": apt.address,
            "sigungu_name": apt.sigungu_name,
            "dong_name": apt.dong_name,
            "location": {
                "lat": apt.latitude,
                "lng": apt.longitude
            } if apt.latitude and apt.longitude else None
        }
        for apt in apartments
    ]
    
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
