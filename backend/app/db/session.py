"""
데이터베이스 세션 관리

비동기 SQLAlchemy 세션을 생성하고 관리합니다.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings

# SQLAlchemy 엔진 로거 레벨을 WARNING으로 설정 (INFO 레벨의 SQL 쿼리 로그 방지)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# 비동기 엔진 생성
# 연결 풀 설정 추가: 시간이 지나도 연결이 유지되도록 설정
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # echo는 False로 설정하고, 필요시 로거 레벨로 제어
    future=True,
    pool_size=10,  # 연결 풀 크기
    max_overflow=20,  # 추가 연결 허용
    pool_pre_ping=True,  # 연결이 끊어졌는지 확인 후 재연결
    pool_recycle=3600,  # 1시간마다 연결 재생성 (타임아웃 방지)
    connect_args={
        "server_settings": {
            "application_name": "realestate_backend",
        },
        "command_timeout": 60,  # 쿼리 타임아웃 60초
    }
)

# 비동기 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)
