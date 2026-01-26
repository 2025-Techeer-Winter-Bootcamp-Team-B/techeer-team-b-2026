"""
일일 통계 모델

테이블명: daily_statistics
일일 거래 통계를 저장하는 테이블입니다.
"""
from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, DateTime, Integer, ForeignKey, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DailyStatistics(Base):
    """
    일일 거래 통계 테이블
    
    매일 전날 거래 통계를 계산하여 저장합니다.
    
    컬럼:
        - stat_date: 통계 날짜 (PK)
        - region_id: 지역 ID (PK, FK, nullable - NULL이면 전국)
        - transaction_type: 거래 유형 (PK, sale 또는 rent)
        - transaction_count: 거래 건수
        - avg_price: 평균 가격
        - total_amount: 총 거래액
        - avg_area: 평균 면적
        - created_at: 생성일
        - updated_at: 수정일
    """
    __tablename__ = "daily_statistics"
    
    # 복합 기본키
    stat_date: Mapped[date] = mapped_column(
        Date,
        primary_key=True,
        comment="통계 날짜"
    )
    
    # 지역 ID (nullable - NULL이면 전국)
    region_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("states.region_id"),
        primary_key=True,
        nullable=True,
        comment="지역 ID (NULL이면 전국)"
    )
    
    # 거래 유형
    transaction_type: Mapped[str] = mapped_column(
        String(10),
        primary_key=True,
        nullable=False,
        comment="거래 유형 (sale, rent)"
    )
    
    # 거래 건수
    transaction_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="거래 건수"
    )
    
    # 평균 가격
    avg_price: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="평균 가격"
    )
    
    # 총 거래액
    total_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="총 거래액"
    )
    
    # 평균 면적
    avg_area: Mapped[Optional[float]] = mapped_column(
        Numeric(7, 2),
        nullable=True,
        comment="평균 면적"
    )
    
    # 생성일
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="레코드 생성 일시"
    )
    
    # 수정일
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="레코드 수정 일시"
    )
    
    # ===== 관계 (Relationships) =====
    # 이 통계가 속한 지역
    region = relationship("State", foreign_keys=[region_id])
    
    def __repr__(self):
        return f"<DailyStatistics(stat_date={self.stat_date}, region_id={self.region_id}, transaction_type='{self.transaction_type}', transaction_count={self.transaction_count})>"
