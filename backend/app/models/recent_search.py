"""
최근 검색어 모델

테이블명: recent_searches
사용자의 최근 검색 기록을 저장합니다.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base


class SearchType(str, enum.Enum):
    """검색 유형"""
    APARTMENT = "apartment"  # 아파트 검색
    LOCATION = "location"    # 지역 검색


class RecentSearch(Base):
    """
    최근 검색어 테이블
    
    사용자가 검색한 기록을 저장합니다.
    아파트 검색과 지역 검색을 모두 포함합니다.
    
    컬럼:
        - search_id: 고유 번호 (자동 생성, PK)
        - account_id: 계정 ID (FK)
        - query: 검색어
        - search_type: 검색 유형 (apartment 또는 location)
        - searched_at: 검색 시간
        - created_at: 생성일
        - updated_at: 수정일
        - is_deleted: 소프트 삭제 여부
    """
    __tablename__ = "recent_searches"
    
    # 기본키 (Primary Key)
    search_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="PK"
    )
    
    # 계정 ID (외래키)
    account_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("accounts.account_id"),
        nullable=False,
        index=True,
        comment="FK"
    )
    
    # 검색어
    query: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="검색어"
    )
    
    # 검색 유형
    search_type: Mapped[SearchType] = mapped_column(
        SQLEnum(SearchType),
        nullable=False,
        comment="검색 유형 (apartment: 아파트, location: 지역)"
    )
    
    # 검색 시간 (사용자가 검색한 시간)
    searched_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="검색 시간"
    )
    
    # 생성일
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        default=datetime.utcnow,
        comment="레코드 생성 일시"
    )
    
    # 수정일
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="레코드 수정 일시"
    )
    
    # 소프트 삭제 여부
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="소프트 삭제"
    )
    
    # ===== 관계 (Relationships) =====
    # 이 검색 기록이 속한 계정
    account = relationship("Account", back_populates="recent_searches")
    
    def __repr__(self):
        return f"<RecentSearch(search_id={self.search_id}, account_id={self.account_id}, query='{self.query}', search_type='{self.search_type}')>"
