"""
국토교통부 API 아파트 데이터 수집 스크립트

사용법:
    python scripts/collect_apartments.py

필요한 환경변수:
    - MOLIT_API_KEY: 국토교통부 API 인증키
    - DATABASE_URL: PostgreSQL 연결 URL
"""
import os
import sys
import asyncio
import httpx
from datetime import datetime

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import asyncpg

# .env 파일 로드
load_dotenv()

# 설정
MOLIT_API_KEY = os.getenv("MOLIT_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/realestate")

# asyncpg용 URL 변환 (asyncpg:// → postgresql://)
DB_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

# 국토교통부 API URL (공동주택 단지 목록)
API_BASE_URL = "https://apis.data.go.kr/1613000/AptListService3/getSigunguAptList3"

# 시군구 코드 (서울시 주요 지역 - 테스트용)
SIGUNGU_CODES = {
    "11680": "강남구",
    "11650": "서초구",
    "11710": "송파구",
    "11740": "강동구",
    "11500": "강서구",
    "11440": "마포구",
    "11410": "서대문구",
    "11380": "은평구",
    "11350": "노원구",
    "11305": "강북구",
}


async def fetch_apartments_from_api(sigungu_code: str, page: int = 1):
    """
    국토교통부 API에서 아파트 목록 조회
    """
    params = {
        "serviceKey": MOLIT_API_KEY,
        "sigunguCode": sigungu_code,
        "pageNo": page,
        "numOfRows": 100,
        "type": "json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(API_BASE_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # 응답 구조 확인
            if "response" in data and "body" in data["response"]:
                body = data["response"]["body"]
                items = body.get("items", {})
                
                if items and "item" in items:
                    return items["item"] if isinstance(items["item"], list) else [items["item"]]
            
            return []
            
        except Exception as e:
            print(f"[ERROR] API 호출 실패 ({sigungu_code}): {e}")
            return []


async def insert_apartments(conn, apartments: list, sigungu_code: str, sigungu_name: str):
    """
    아파트 데이터를 DB에 저장
    """
    inserted = 0
    
    for apt in apartments:
        try:
            # 국토교통부 API 응답 필드 매핑
            apt_name = apt.get("kaptName", apt.get("as1", ""))
            address = apt.get("kaptAddr", apt.get("as2", ""))
            dong_name = apt.get("kaptDongNm", apt.get("bjdongName", ""))
            total_units = apt.get("kaptdaCnt", apt.get("kaptTarea", 0))
            build_year = apt.get("kaptUsedate", apt.get("useYear", ""))
            
            # 준공년도 처리 (YYYYMM 형식일 수 있음)
            if build_year and len(str(build_year)) >= 4:
                build_year = int(str(build_year)[:4])
            else:
                build_year = None
            
            # 세대수 처리
            if total_units:
                try:
                    total_units = int(total_units)
                except:
                    total_units = None
            
            if not apt_name:
                continue
            
            # 중복 체크 후 삽입
            await conn.execute("""
                INSERT INTO apartments (apt_name, address, sigungu_code, sigungu_name, dong_name, total_units, build_year)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT DO NOTHING
            """, apt_name, address, sigungu_code, sigungu_name, dong_name, total_units, build_year)
            
            inserted += 1
            
        except Exception as e:
            print(f"  [WARN] 저장 실패: {apt.get('kaptName', 'Unknown')} - {e}")
    
    return inserted


async def main():
    """
    메인 실행 함수
    """
    print("=" * 60)
    print("[INFO] 국토교통부 API 아파트 데이터 수집")
    print("=" * 60)
    
    if not MOLIT_API_KEY:
        print("[ERROR] MOLIT_API_KEY가 설정되지 않았습니다!")
        print("   .env 파일에 MOLIT_API_KEY를 추가하세요.")
        return
    
    print(f"[OK] API KEY: {MOLIT_API_KEY[:10]}...")
    print(f"[OK] DB URL: {DB_URL[:30]}...")
    print()
    
    # DB 연결
    try:
        conn = await asyncpg.connect(DB_URL)
        print("[OK] 데이터베이스 연결 성공!")
    except Exception as e:
        print(f"[ERROR] 데이터베이스 연결 실패: {e}")
        return
    
    total_inserted = 0
    
    # 각 시군구별로 데이터 수집
    for code, name in SIGUNGU_CODES.items():
        print(f"\n[FETCH] {name} ({code}) 데이터 수집 중...")
        
        apartments = await fetch_apartments_from_api(code)
        
        if apartments:
            inserted = await insert_apartments(conn, apartments, code, name)
            total_inserted += inserted
            print(f"   [OK] {len(apartments)}개 조회, {inserted}개 저장")
        else:
            print(f"   [WARN] 데이터 없음")
    
    # DB 연결 종료
    await conn.close()
    
    print()
    print("=" * 60)
    print(f"[DONE] 완료! 총 {total_inserted}개 아파트 데이터 저장")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
