"""
아파트 모델

테이블명: apartments
아파트 기본 정보를 저장합니다.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Integer, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Apartment(Base):
    """
    아파트 테이블
    
    국토교통부 API에서 가져온 아파트 기본 정보를 저장합니다.
    
    컬럼:
        - apt_id: 고유 번호 (자동 생성)
        - apt_name: 아파트명
        - address: 주소
        - sigungu_code: 시군구 코드
        - sigungu_name: 시군구명 (예: 강남구)
        - dong_name: 동명 (예: 역삼동)
        - latitude: 위도
        - longitude: 경도
        - total_units: 총 세대수
        - build_year: 준공년도
        - created_at: 레코드 생성일
        - updated_at: 레코드 수정일
    """
    __tablename__ = "apartments"
    
    # 기본키 (Primary Key)
    apt_id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="아파트 고유 ID"
    )
    
    # 아파트명
    apt_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,  # 검색 성능을 위한 인덱스
        comment="아파트명"
    )
    
    # 주소
    address: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="전체 주소"
    )
    
    # 시군구 코드
    sigungu_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        index=True,
        comment="시군구 코드"
    )
    
    # 시군구명
    sigungu_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="시군구명 (예: 강남구)"
    )
    
    # 동명
    dong_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="동명 (예: 역삼동)"
    )
    
    # 위도
    latitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="위도 (lat)"
    )
    
    # 경도
    longitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="경도 (lng)"
    )
    
    # 총 세대수
    total_units: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="총 세대수"
    )
    
    # 준공년도
    build_year: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="준공년도"
    )
    
    # 생성일 (자동 생성)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="레코드 생성 일시"
    )
    
    # 수정일 (자동 업데이트)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="레코드 수정 일시"
    )
    
    def __repr__(self):
        return f"<Apartment(apt_id={self.apt_id}, apt_name='{self.apt_name}')>"
