"""
인구 이동 모델

테이블명: population_movements
지역별 인구 이동 데이터를 저장합니다 (KOSIS 통계청 데이터).
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Integer, CHAR, ForeignKey, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PopulationMovement(Base):
    """
    인구 이동 테이블
    
    지역별 인구 이동 데이터를 저장합니다 (KOSIS 통계청 데이터).
    
    컬럼:
        - movement_id: 고유 번호 (자동 생성, PK)
        - region_id: 지역 ID (FK)
        - base_ym: 기준 년월 (YYYYMM)
        - in_migration: 전입 인구 수
        - out_migration: 전출 인구 수
        - net_migration: 순이동 인구 수 (전입 - 전출)
        - movement_type: 이동 유형 (TOTAL=전체, DOMESTIC=국내이동)
        - data_source: 데이터 출처
        - created_at: 생성일
        - updated_at: 수정일
        - is_deleted: 소프트 삭제 여부
    """
    __tablename__ = "population_movements"
    
    # 기본키 (Primary Key)
    movement_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="PK"
    )
    
    # 지역 ID (외래키)
    region_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("states.region_id"),
        nullable=False,
        comment="FK"
    )
    
    # 기준 년월 (YYYYMM)
    base_ym: Mapped[str] = mapped_column(
        CHAR(6),
        nullable=False,
        comment="기준 년월 (YYYYMM)"
    )
    
    # 전입 인구 수
    in_migration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="전입 인구 수 (명)"
    )
    
    # 전출 인구 수
    out_migration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="전출 인구 수 (명)"
    )
    
    # 순이동 인구 수 (전입 - 전출)
    net_migration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="순이동 인구 수 (전입 - 전출, 명)"
    )
    
    # 이동 유형
    movement_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="TOTAL",
        comment="이동 유형: TOTAL=전체, DOMESTIC=국내이동"
    )
    
    # 데이터 출처
    data_source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="KOSIS",
        comment="데이터 출처"
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
    
    # 소프트 삭제 여부
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="소프트 삭제"
    )
    
    # ===== 관계 (Relationships) =====
    # 이 이동 데이터가 속한 지역
    region = relationship("State", back_populates="population_movements")
    
    # ===== 인덱스 =====
    __table_args__ = (
        Index("idx_population_movements_region_ym", "region_id", "base_ym"),
        Index("idx_population_movements_base_ym", "base_ym"),
    )
    
    def __repr__(self):
        return f"<PopulationMovement(movement_id={self.movement_id}, region_id={self.region_id}, base_ym='{self.base_ym}', net_migration={self.net_migration})>"
