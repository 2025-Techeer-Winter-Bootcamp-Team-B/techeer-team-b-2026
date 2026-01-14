"""
최근 검색어 스키마

요청/응답 데이터 검증 및 직렬화를 위한 Pydantic 스키마
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.recent_search import SearchType


class RecentSearchBase(BaseModel):
    """기본 최근 검색어 스키마"""
    query: str = Field(..., description="검색어", max_length=100)
    search_type: SearchType = Field(..., description="검색 유형 (apartment: 아파트, location: 지역)")


class RecentSearchCreate(RecentSearchBase):
    """최근 검색어 생성 스키마"""
    account_id: int = Field(..., description="계정 ID")


class RecentSearchUpdate(BaseModel):
    """최근 검색어 수정 스키마"""
    query: Optional[str] = Field(None, description="검색어", max_length=100)
    search_type: Optional[SearchType] = Field(None, description="검색 유형")


class RecentSearchResponse(RecentSearchBase):
    """최근 검색어 응답 스키마"""
    search_id: int = Field(..., description="검색 기록 ID (PK)")
    account_id: int = Field(..., description="계정 ID (FK)")
    searched_at: datetime = Field(..., description="검색 시간")
    created_at: Optional[datetime] = Field(None, description="생성일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")
    is_deleted: bool = Field(False, description="삭제 여부")
    
    model_config = ConfigDict(from_attributes=True)


class RecentSearchListResponse(BaseModel):
    """최근 검색어 목록 응답 스키마"""
    success: bool = Field(True, description="성공 여부")
    data: dict = Field(..., description="검색 결과 데이터")
    meta: Optional[dict] = Field(None, description="메타 정보")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    "recent_searches": [
                        {
                            "search_id": 1,
                            "query": "래미안",
                            "search_type": "apartment",
                            "searched_at": "2026-01-13T10:30:00Z"
                        }
                    ]
                },
                "meta": {
                    "count": 1
                }
            }
        }
    )
