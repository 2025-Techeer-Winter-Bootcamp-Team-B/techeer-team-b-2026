"""
데이터 수집 서비스

국토교통부 API에서 지역 데이터를 가져와서 데이터베이스에 저장하는 비즈니스 로직
"""
import logging
import asyncio
import sys
from typing import List, Dict, Any, Optional
from urllib.parse import quote
import httpx

from sqlalchemy.ext.asyncio import AsyncSession

# 모든 모델을 import하여 SQLAlchemy 관계 설정이 제대로 작동하도록 함
from app.models import (  # noqa: F401
    Account,
    State,
    Apartment,
    ApartDetail,
    Sale,
    Rent,
    HouseScore,
    FavoriteLocation,
    FavoriteApartment,
    MyProperty,
)

from app.core.config import settings
from app.crud.state import state as state_crud
from app.crud.apartment import apartment as apartment_crud
from app.crud.apart_detail import apart_detail as apart_detail_crud
from app.crud.transaction import sale as sale_crud
from app.schemas.state import StateCreate, StateCollectionResponse
from app.schemas.apartment import ApartmentCreate, ApartmentCollectionResponse
from app.schemas.apart_detail import ApartDetailCreate, ApartDetailCollectionResponse
from app.schemas.transaction import (
    TransactionRequestSchema,
    TransactionResponseSchema,
    TransactionItemSchema,
    SaleCreate,
    SaleCollectionResponse
)

# 로거 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 핸들러가 없으면 추가
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False  # 부모 로거로 전파하지 않음

# 국토부 표준지역코드 API 엔드포인트
MOLIT_REGION_API_URL = "https://apis.data.go.kr/1741000/StanReginCd/getStanReginCdList"

# 국토부 아파트 목록 API 엔드포인트
MOLIT_APARTMENT_LIST_API_URL = "https://apis.data.go.kr/1613000/AptListService3/getTotalAptList3"

# 국토부 아파트 기본정보 API 엔드포인트
MOLIT_APARTMENT_BASIC_API_URL = "https://apis.data.go.kr/1613000/AptBasisInfoServiceV4/getAphusBassInfoV4"

# 국토부 아파트 상세정보 API 엔드포인트
MOLIT_APARTMENT_DETAIL_API_URL = "https://apis.data.go.kr/1613000/AptBasisInfoServiceV4/getAphusDtlInfoV4"

# 국토부 실거래가 API 엔드포인트 (아파트 매매)
MOLIT_APARTMENT_SALE_API_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"

# 시도 목록 (17개)
CITY_NAMES = [
    "강원특별자치도",
    "경기도",
    "경상남도",
    "경상북도",
    "광주광역시",
    "대구광역시",
    "대전광역시",
    "부산광역시",
    "서울특별시",
    "세종특별자치시",
    "울산광역시",
    "인천광역시",
    "전라남도",
    "전북특별자치도",
    "제주특별자치도",
    "충청남도",
    "충청북도"
]


class DataCollectionService:
    """
    데이터 수집 서비스 클래스
    
    국토교통부 API에서 지역 데이터를 가져와서 데이터베이스에 저장합니다.
    """
    
    def __init__(self):
        """서비스 초기화"""
        if not settings.MOLIT_API_KEY:
            raise ValueError("MOLIT_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        self.api_key = settings.MOLIT_API_KEY

    async def fetch_with_retry(self, url: str, params: Dict[str, Any], retries: int = 3) -> Dict[str, Any]:
        """
        API 호출 재시도 로직 (지수 백오프)
        """
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()
            except httpx.TimeoutException:
                if attempt == retries - 1:
                    logger.warning(f"⏰ [Timeout] API 호출 시간 초과 ({url}) - {retries}회 시도 실패")
                    raise
                await asyncio.sleep(0.5 * (2 ** attempt))
            except Exception as e:
                if attempt == retries - 1:
                    logger.warning(f"❌ [API Error] {e} ({url})")
                    raise
                await asyncio.sleep(0.5 * (2 ** attempt))
        return {}

    async def fetch_region_data(
        self,
        city_name: str,
        page_no: int = 1,
        num_of_rows: int = 1000
    ) -> Dict[str, Any]:
        """
        국토부 API에서 지역 데이터 가져오기
        """
        encoded_city_name = quote(city_name)
        params = {
            "serviceKey": self.api_key,
            "pageNo": str(page_no),
            "numOfRows": str(num_of_rows),
            "type": "json",
            "locatadd_nm": city_name
        }
        return await self.fetch_with_retry(MOLIT_REGION_API_URL, params)
    
    def parse_region_data(
        self,
        api_response: Dict[str, Any],
        city_name: str
    ) -> tuple[List[Dict[str, str]], int, int]:
        """
        API 응답 데이터 파싱 (모든 지역 단위 수집)
        """
        regions = []
        total_count = 0
        original_count = 0
        
        try:
            stan_regin_cd = api_response.get("StanReginCd", [])
            if not stan_regin_cd or len(stan_regin_cd) < 2:
                return [], 0, 0
            
            head_data = stan_regin_cd[0].get("head", [])
            for head_item in head_data:
                if isinstance(head_item, dict) and "totalCount" in head_item:
                    total_count = int(head_item["totalCount"])
                    break
            
            row_data = stan_regin_cd[1].get("row", [])
            if not isinstance(row_data, list):
                row_data = [row_data] if row_data else []
            
            original_count = len(row_data)
            
            for item in row_data:
                region_cd = str(item.get("region_cd", "")).strip()
                locatadd_nm = str(item.get("locatadd_nm", "")).strip()
                locallow_nm = str(item.get("locallow_nm", "")).strip()
                
                if not region_cd:
                    continue
                
                parsed_city = self._extract_city_name_from_address(locatadd_nm) or city_name
                
                if not locallow_nm:
                    parts = locatadd_nm.split()
                    if len(parts) >= 2:
                        if parts[0] == parsed_city:
                            locallow_nm = " ".join(parts[1:])
                        else:
                            locallow_nm = " ".join(parts)
                    else:
                        locallow_nm = locatadd_nm
                
                regions.append({
                    "region_code": region_cd,
                    "region_name": locallow_nm,
                    "city_name": parsed_city
                })
            
            return regions, total_count, original_count
            
        except Exception as e:
            logger.error(f"❌ 데이터 파싱 실패: {e}")
            return [], 0, 0
    
    def _extract_city_name_from_address(self, locatadd_nm: str) -> str:
        if not locatadd_nm: return ""
        for city in CITY_NAMES:
            if locatadd_nm.startswith(city): return city
        return ""
    
    def _extract_city_name_from_code(self, region_code: str) -> str:
        if len(region_code) < 2: return ""
        sido_code = region_code[:2]
        sido_map = {
            "11": "서울특별시", "26": "부산광역시", "27": "대구광역시", "28": "인천광역시", 
            "29": "광주광역시", "30": "대전광역시", "31": "울산광역시", "36": "세종특별자치시", 
            "41": "경기도", "42": "강원특별자치도", "43": "충청북도", "44": "충청남도", 
            "45": "전북특별자치도", "46": "전라남도", "47": "경상북도", "48": "경상남도", 
            "50": "제주특별자치도"
        }
        return sido_map.get(sido_code, "")

    async def _process_city_region(
        self,
        city_name: str,
        semaphore: asyncio.Semaphore
    ) -> Dict[str, Any]:
        """단일 시도 지역 데이터 수집 (병렬용)"""
        async with semaphore:
            result = {"city": city_name, "data": [], "errors": []}
            try:
                num_of_rows = 1000
                first_response = await self.fetch_region_data(city_name, 1, num_of_rows)
                first_regions, total_count, _ = self.parse_region_data(first_response, city_name)
                
                result["data"].extend(first_regions)
                
                if total_count > num_of_rows:
                    total_pages = (total_count // num_of_rows) + 1
                    logger.info(f"   🔍 {city_name}: 총 {total_count}개, {total_pages}페이지 병렬 수집")
                    
                    inner_semaphore = asyncio.Semaphore(5)
                    async def fetch_page(p):
                        async with inner_semaphore:
                            res = await self.fetch_region_data(city_name, p, num_of_rows)
                            regions, _, _ = self.parse_region_data(res, city_name)
                            return regions

                    tasks = [fetch_page(p) for p in range(2, total_pages + 1)]
                    pages_results = await asyncio.gather(*tasks)
                    
                    for regions in pages_results:
                        result["data"].extend(regions)
                
                logger.info(f"   📦 {city_name} 수집 완료: {len(result['data'])}개 데이터 확보")
                return result
            except Exception as e:
                logger.error(f"❌ {city_name} 수집 실패: {e}")
                result["errors"].append(str(e))
                return result
    
    async def collect_all_regions(
        self,
        db: AsyncSession
    ) -> StateCollectionResponse:
        """모든 시도의 지역 데이터 수집 (병렬 수집 -> 순차 저장)"""
        total_fetched = 0
        total_saved = 0
        skipped = 0
        errors = []
        
        try:
            logger.info("=" * 60)
            logger.info("🚀 [안정형] 지역 데이터 수집 시작")
            logger.info("=" * 60)
            
            CONCURRENT_LIMIT = 5
            semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)
            
            tasks = [self._process_city_region(city, semaphore) for city in CITY_NAMES]
            logger.info("📡 17개 시도 데이터 병렬 수집 중...")
            results = await asyncio.gather(*tasks)
            
            logger.info("💾 수집된 데이터 저장 시작...")
            for res in results:
                city_name = res["city"]
                city_data = res["data"]
                
                total_fetched += len(city_data)
                if res["errors"]: errors.extend(res["errors"])
                if not city_data: continue
                
                logger.info(f"   💾 {city_name}: {len(city_data)}개 저장 중...")
                city_saved = 0
                city_skipped = 0
                
                for region_data in city_data:
                    try:
                        state_create = StateCreate(**region_data)
                        _, is_created = await state_crud.create_or_skip(db, obj_in=state_create)
                        if is_created: city_saved += 1
                        else: city_skipped += 1
                    except Exception: pass
                
                total_saved += city_saved
                skipped += city_skipped
                logger.info(f"      ✅ {city_name} 저장 완료 (저장: {city_saved}, 건너뜀: {city_skipped})")
            
            logger.info("=" * 60)
            logger.info(f"🎉 지역 데이터 수집 완료! (저장: {total_saved})")
            
            return StateCollectionResponse(
                success=True,
                total_fetched=total_fetched,
                total_saved=total_saved,
                skipped=skipped,
                errors=errors,
                message=f"수집 완료: {total_saved}개 저장"
            )
        except Exception as e:
            logger.error(f"❌ 지역 데이터 수집 실패: {e}", exc_info=True)
            return StateCollectionResponse(success=False, errors=[str(e)], message=f"수집 실패: {str(e)}")

    async def fetch_apartment_data(
        self,
        page_no: int = 1,
        num_of_rows: int = 1000
    ) -> Dict[str, Any]:
        """국토부 API에서 아파트 목록 데이터 가져오기"""
        params = {"serviceKey": self.api_key, "pageNo": str(page_no), "numOfRows": str(num_of_rows)}
        return await self.fetch_with_retry(MOLIT_APARTMENT_LIST_API_URL, params)
    
    def parse_apartment_data(
        self,
        api_response: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], int, int]:
        """아파트 목록 API 응답 파싱"""
        try:
            body = api_response.get("response", {}).get("body", {})
            items = body.get("items", [])
            total_count = int(body.get("totalCount", 0))
            
            if not isinstance(items, list): items = [items] if items else []
            
            original_count = len(items)
            apartments = []
            
            for item in items:
                if not item: continue
                kapt_code = item.get("kaptCode", "").strip()
                kapt_name = item.get("kaptName", "").strip()
                bjd_code = item.get("bjdCode", "").strip()
                
                if not kapt_code or not kapt_name or not bjd_code: continue
                
                apartments.append({
                    "kapt_code": kapt_code,
                    "apt_name": kapt_name,
                    "bjd_code": bjd_code,
                    "as1": item.get("as1"),
                    "as2": item.get("as2"),
                    "as3": item.get("as3"),
                    "as4": item.get("as4")
                })
            return apartments, total_count, original_count
        except Exception as e:
            logger.error(f"❌ 파싱 오류: {e}")
            return [], 0, 0
    
    async def _fetch_and_process_apartment_page(
        self,
        page_no: int,
        num_of_rows: int,
        semaphore: asyncio.Semaphore
    ) -> Dict[str, Any]:
        """단일 페이지 아파트 목록 수집 및 처리 (DB 접근 제거)"""
        async with semaphore:
            try:
                api_response = await self.fetch_apartment_data(page_no, num_of_rows)
                apartments, _, _ = self.parse_apartment_data(api_response)
                return {"success": True, "page_no": page_no, "data": apartments, "errors": []}
            except Exception as e:
                return {"success": False, "page_no": page_no, "error": str(e)}

    async def collect_all_apartments(
        self,
        db: AsyncSession
    ) -> ApartmentCollectionResponse:
        """모든 아파트 목록 수집 (초고속 병렬 처리 모드)"""
        total_fetched = 0
        total_saved = 0
        skipped = 0
        errors = []
        
        try:
            logger.info("=" * 80)
            logger.info("🏢 [최고성능] 아파트 목록 수집 시작")
            logger.info("=" * 80)
            
            logger.info("🚀 Region 데이터 메모리 캐싱 중...")
            from sqlalchemy import select
            from app.models.state import State
            region_result = await db.execute(select(State.region_code, State.region_id))
            region_map = {row[0]: row[1] for row in region_result.fetchall()}
            logger.info(f"   ✅ {len(region_map)}개 지역 코드 캐싱 완료")
            
            num_of_rows = 1000
            first_response = await self.fetch_apartment_data(1, num_of_rows)
            _, total_count, _ = self.parse_apartment_data(first_response)
            
            if total_count == 0: return ApartmentCollectionResponse(success=True, message="수집할 데이터가 없습니다.")
            
            total_pages = (total_count // num_of_rows) + 1
            logger.info(f"📊 총 {total_count}개 아파트, {total_pages}페이지 예상")
            
            CONCURRENT_LIMIT = 30
            semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)
            pages = list(range(1, total_pages + 1))
            chunk_size = 50
            
            for i in range(0, len(pages), chunk_size):
                chunk_pages = pages[i : i + chunk_size]
                logger.info(f"⚡ 페이지 {chunk_pages[0]} ~ {chunk_pages[-1]} 초고속 수집 중...")
                
                tasks = [self._fetch_and_process_apartment_page(p, num_of_rows, semaphore) for p in chunk_pages]
                results = await asyncio.gather(*tasks)
                
                apartments_to_save = []
                for res in results:
                    if res["success"]:
                        for apt_data in res["data"]:
                            try:
                                kapt_code = apt_data.get('kapt_code')
                                apt_name = apt_data.get('apt_name')
                                bjd_code = apt_data.get('bjd_code')
                                region_id = region_map.get(bjd_code)
                                if not region_id: continue
                                
                                apartments_to_save.append(ApartmentCreate(
                                    region_id=region_id, apt_name=apt_name, kapt_code=kapt_code, is_available=None
                                ))
                            except Exception: pass
                        if res.get("errors"): errors.extend(res["errors"])
                    else: errors.append(f"페이지 {res['page_no']} 실패: {res.get('error')}")
                
                total_fetched += len(apartments_to_save)
                
                if apartments_to_save:
                    try:
                        saved_count = 0
                        skipped_count = 0
                        for apt_create in apartments_to_save:
                            _, created = await apartment_crud.create_or_skip(db, obj_in=apt_create)
                            if created: saved_count += 1
                            else: skipped_count += 1
                        total_saved += saved_count
                        skipped += skipped_count
                        logger.info(f"   💾 배치 처리 완료: {saved_count}개 저장, {skipped_count}개 중복 (누적: {total_saved})")
                    except Exception as e:
                        logger.error(f"❌ 배치 저장 실패: {e}")
                
                await asyncio.sleep(0.2)
            
            logger.info("=" * 80)
            logger.info(f"✅ 아파트 목록 수집 완료 (총 {total_saved}개)")
            return ApartmentCollectionResponse(success=True, total_fetched=total_fetched, total_saved=total_saved, skipped=skipped, errors=errors[:100], message=f"초고속 수집 완료: {total_saved}개 저장")
        except Exception as e:
            logger.error(f"❌ 수집 실패: {e}", exc_info=True)
            return ApartmentCollectionResponse(success=False, errors=[str(e)], message=f"수집 실패: {str(e)}")

    async def fetch_apartment_basic_info(self, kapt_code: str) -> Dict[str, Any]:
        params = {"serviceKey": self.api_key, "kaptCode": kapt_code}
        return await self.fetch_with_retry(MOLIT_APARTMENT_BASIC_API_URL, params)
    
    async def fetch_apartment_detail_info(self, kapt_code: str) -> Dict[str, Any]:
        params = {"serviceKey": self.api_key, "kaptCode": kapt_code}
        return await self.fetch_with_retry(MOLIT_APARTMENT_DETAIL_API_URL, params)
    
    def parse_date(self, date_str: Optional[str]) -> Optional[str]:
        if not date_str or len(date_str) != 8: return None
        try: return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        except Exception: return None
    
    def parse_int(self, value: Any) -> Optional[int]:
        if value is None or value == "": return None
        try:
            if isinstance(value, str):
                value = value.strip()
                if not value: return None
            return int(value)
        except (ValueError, TypeError): return None
    
    def parse_apartment_details(
        self,
        basic_info: Dict[str, Any],
        detail_info: Dict[str, Any],
        apt_id: int
    ) -> Optional[ApartDetailCreate]:
        try:
            basic_item = basic_info.get("response", {}).get("body", {}).get("item", {})
            if not basic_item:
                logger.warning(f"   ⚠️ [파싱 실패] apt_id={apt_id}: 기본정보 API 응답에 item이 없습니다.")
                return None
            
            detail_item = detail_info.get("response", {}).get("body", {}).get("item", {})
            if not detail_item:
                logger.warning(f"   ⚠️ [파싱 실패] apt_id={apt_id}: 상세정보 API 응답에 item이 없습니다.")
                return None
            
            doro_juso = basic_item.get("doroJuso", "").strip() if basic_item.get("doroJuso") else ""
            kapt_addr = basic_item.get("kaptAddr", "").strip() if basic_item.get("kaptAddr") else ""
            
            if not doro_juso and not kapt_addr:
                logger.warning(f"   ⚠️ [파싱 실패] apt_id={apt_id}: 도로명 주소와 지번 주소가 모두 없습니다.")
                return None
            if not doro_juso: doro_juso = kapt_addr
            if not kapt_addr: kapt_addr = doro_juso
            
            zipcode = basic_item.get("zipcode", "").strip() if basic_item.get("zipcode") else None
            if zipcode and len(zipcode) > 5: zipcode = zipcode[:5]
            
            use_approval_date_str = self.parse_date(basic_item.get("kaptUsedate"))
            use_approval_date = None
            if use_approval_date_str:
                try: use_approval_date = datetime.strptime(use_approval_date_str, "%Y-%m-%d").date()
                except Exception: pass
            
            total_household_cnt = self.parse_int(basic_item.get("kaptdaCnt"))
            if total_household_cnt is None:
                logger.warning(f"   ⚠️ [파싱 실패] apt_id={apt_id}: 총 세대 수(kaptdaCnt)가 없습니다.")
                return None
            
            manage_type = detail_item.get("codeMgr", "").strip()
            if not manage_type: manage_type = basic_item.get("codeMgrNm", "").strip()
            if not manage_type: manage_type = None
            if manage_type and len(manage_type) > 20: manage_type = manage_type[:20]
            
            subway_line = detail_item.get("subwayLine", "").strip() if detail_item.get("subwayLine") else None
            if subway_line and len(subway_line) > 100: subway_line = subway_line[:100]
            
            subway_station = detail_item.get("subwayStation", "").strip() if detail_item.get("subwayStation") else None
            if subway_station and len(subway_station) > 100: subway_station = subway_station[:100]
            
            subway_time = detail_item.get("kaptdWtimesub", "").strip() if detail_item.get("kaptdWtimesub") else None
            if subway_time and len(subway_time) > 100: subway_time = subway_time[:100]
            
            builder_name = basic_item.get("kaptBcompany", "").strip() if basic_item.get("kaptBcompany") else None
            if builder_name and len(builder_name) > 100: builder_name = builder_name[:100]
            
            developer_name = basic_item.get("kaptAcompany", "").strip() if basic_item.get("kaptAcompany") else None
            if developer_name and len(developer_name) > 100: developer_name = developer_name[:100]

            education_facility = detail_item.get("educationFacility", "").strip() if detail_item.get("educationFacility") else None
            if education_facility and len(education_facility) > 200:
                education_facility = education_facility[:200]
            
            try:
                return ApartDetailCreate(
                    apt_id=apt_id,
                    road_address=doro_juso,
                    jibun_address=kapt_addr,
                    zip_code=zipcode,
                    code_sale_nm=basic_item.get("codeSaleNm", "").strip() if basic_item.get("codeSaleNm") else None,
                    code_heat_nm=basic_item.get("codeHeatNm", "").strip() if basic_item.get("codeHeatNm") else None,
                    total_household_cnt=total_household_cnt,
                    total_building_cnt=self.parse_int(basic_item.get("kaptDongCnt")),
                    highest_floor=self.parse_int(basic_item.get("kaptTopFloor")),
                    use_approval_date=use_approval_date,
                    total_parking_cnt=self.parse_int(detail_item.get("kaptdPcntu")),
                    builder_name=builder_name,
                    developer_name=developer_name,
                    manage_type=manage_type,
                    hallway_type=basic_item.get("codeHallNm", "").strip() if basic_item.get("codeHallNm") else None,
                    subway_time=subway_time,
                    subway_line=subway_line,
                    subway_station=subway_station,
                    educationFacility=education_facility,
                    geometry=None
                )
            except Exception as e:
                logger.error(f"   ❌ [파싱 오류] apt_id={apt_id}: 객체 생성 중 에러 - {e}")
                return None
        except Exception as e:
            logger.error(f"   ❌ [파싱 오류] apt_id={apt_id}: 알 수 없는 에러 - {e}")
            return None
    
    async def _process_single_apartment(
        self,
        db: AsyncSession,
        apartment: Any,
        semaphore: asyncio.Semaphore
    ) -> Dict[str, Any]:
        """단일 아파트 상세 정보 수집 및 저장 (병렬 처리용)"""
        async with semaphore:
            apt_name = apartment.apt_name
            kapt_code = apartment.kapt_code
            apt_id = apartment.apt_id
            
            start_time = asyncio.get_event_loop().time()
            
            try:
                try:
                    basic_task = self.fetch_apartment_basic_info(kapt_code)
                    detail_task = self.fetch_apartment_detail_info(kapt_code)
                    
                    basic_info, detail_info = await asyncio.wait_for(
                        asyncio.gather(basic_task, detail_task),
                        timeout=15.0
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"🐢 [지연 감지] {apt_name} ({kapt_code}) API 응답 15초 초과 - 건너뜀")
                    return {"success": False, "error": "API Timeout (15s)", "apt_name": apt_name}

                detail_create = self.parse_apartment_details(basic_info, detail_info, apt_id)
                
                if not detail_create:
                    return {"success": False, "error": "데이터 파싱 실패 (필수값 누락)", "apt_name": apt_name}
                
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > 5.0:
                    logger.info(f"⚠️ [Slow] {apt_name} 처리 {elapsed:.2f}초 소요")

                return {"success": True, "data": detail_create, "apt_name": apt_name}

            except Exception as e:
                return {"success": False, "error": str(e), "apt_name": apt_name}

    async def collect_apartment_details(
        self,
        db: AsyncSession,
        limit: Optional[int] = None
    ) -> ApartDetailCollectionResponse:
        """아파트 상세 정보 수집 (고성능 병렬 처리 버전)"""
        total_processed = 0
        total_saved = 0
        skipped = 0
        errors = []
        CONCURRENT_LIMIT = 20
        semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)
        BATCH_SIZE = 50
        
        try:
            logger.info("🚀 [고성능 모드] 아파트 상세 정보 수집 시작")
            loop_limit = limit if limit else 1000000
            
            while total_processed < loop_limit:
                fetch_limit = min(BATCH_SIZE, loop_limit - total_processed)
                if fetch_limit <= 0: break
                
                targets = await apartment_crud.get_multi_missing_details(db, limit=fetch_limit)
                
                if not targets:
                    logger.info("✨ 더 이상 수집할 아파트가 없습니다.")
                    break
                
                tasks = [self._process_single_apartment(db, apt, semaphore) for apt in targets]
                results = await asyncio.gather(*tasks)
                
                valid_data_list = []
                for res in results:
                    if res["success"]: valid_data_list.append(res["data"])
                    else: errors.append(f"{res['apt_name']}: {res['error']}")
                
                if valid_data_list:
                    try:
                        for detail_data in valid_data_list:
                            db_obj = ApartDetail(**detail_data.model_dump())
                            db.add(db_obj)
                        await db.commit()
                        total_saved += len(valid_data_list)
                        
                        failed_count = len(results) - len(valid_data_list)
                        if failed_count > 0:
                            logger.info(f"   💾 배치 저장 완료: {len(valid_data_list)}개 (실패/누락: {failed_count}개)")
                        else:
                            logger.info(f"   💾 배치 저장 완료: {len(valid_data_list)}개 (전체 성공)")
                            
                    except Exception as commit_e:
                        await db.rollback()
                        logger.error(f"❌ 배치 커밋 실패: {commit_e}")
                        errors.append(f"배치 커밋 실패: {str(commit_e)}")
                
                total_processed += len(targets)
                await asyncio.sleep(1)

            logger.info("=" * 60)
            logger.info(f"🎉 수집 완료 (총 {total_saved}개 저장)")
            return ApartDetailCollectionResponse(
                success=True,
                total_processed=total_processed,
                total_saved=total_saved,
                skipped=skipped,
                errors=errors[:100],
                message=f"고속 수집 완료: {total_saved}개 저장됨"
            )

        except Exception as e:
            logger.error(f"❌ 아파트 상세 정보 수집 실패: {e}", exc_info=True)
            # 예외 발생 시 남은 데이터 커밋 시도
            try:
                remaining_count = total_saved - last_commit_count
                if remaining_count > 0:
                    logger.warning(f"   ⚠️ 예외 발생 전 남은 {remaining_count}개 데이터 커밋 시도...")
                    try:
                        await db.commit()
                        logger.info(f"   ✅ 예외 발생 전 데이터 커밋 완료")
                    except Exception as commit_error:
                        logger.error(f"   ❌ 예외 발생 전 데이터 커밋 실패: {str(commit_error)}")
                        await db.rollback()
            except Exception:
                pass  # 이미 예외가 발생한 상태이므로 무시
            
            return ApartDetailCollectionResponse(
                success=False,
                total_processed=total_processed,
                total_saved=total_saved,
                skipped=skipped,
                errors=errors + [str(e)],
                message=f"수집 실패: {str(e)}"
            )


    async def fetch_sale_transaction_data(
        self,
        lawd_cd: str,
        deal_ymd: str,
        page_no: int = 1,
        num_of_rows: int = 1000
    ) -> Dict[str, Any]:
        """
        국토부 API에서 아파트 매매 거래 데이터 가져오기
        
        Args:
            lawd_cd: 법정동코드 (5자리, 예: "11110")
            deal_ymd: 계약년월 (YYYYMM 형식, 예: "202407")
            page_no: 페이지 번호 (기본값: 1)
            num_of_rows: 한 페이지 결과 수 (기본값: 1000)
        
        Returns:
            API 응답 데이터 (dict)
        
        Raises:
            httpx.HTTPError: API 호출 실패 시
        """
        # URL 인코딩된 API 키
        encoded_key = quote(self.api_key)
        
        # API 요청 파라미터
        params = {
            "serviceKey": encoded_key,
            "pageNo": str(page_no),
            "numOfRows": str(num_of_rows),
            "LAWD_CD": lawd_cd,  # 법정동코드
            "DEAL_YMD": deal_ymd  # 계약년월
        }
        
        logger.info(f"📡 실거래가 API 호출: 법정동코드={lawd_cd}, 계약년월={deal_ymd}, 페이지={page_no}")

        # API 호출
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(MOLIT_APARTMENT_SALE_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if page_no == 1:
                logger.debug(f"   🔍 API 응답 구조 확인: {list(data.keys()) if isinstance(data, dict) else '리스트'}")
            
            return data
    
    def parse_sale_transaction_data(
        self,
        api_response: Dict[str, Any]
    ) -> tuple[List[TransactionItemSchema], int]:
        """
        실거래가 API 응답 파싱
        
        Args:
            api_response: API 응답 데이터
        
        Returns:
            (파싱된 거래 항목 목록, 전체 개수)
        """
        try:
            # TransactionResponseSchema로 파싱
            response_schema = TransactionResponseSchema(response=api_response)
            
            # 헤더 확인
            header = response_schema.get_header()
            if header and header.resultCode != "00":
                logger.warning(f"⚠️ API 응답 오류: {header.resultMsg}")
                return [], 0
            
            # 거래 항목 추출
            items = response_schema.get_items()
            
            # 본문에서 전체 개수 확인
            body = response_schema.get_body()
            total_count = body.totalCount if body else len(items)
            
            logger.info(f"✅ 파싱 완료: {len(items)}개 거래 항목 (전체 {total_count}개 중)")
            
            return items, total_count
            
        except Exception as e:
            logger.error(f"❌ 데이터 파싱 실패: {e}")
            logger.debug(f"API 응답: {api_response}")
            import traceback
            logger.debug(traceback.format_exc())
            return [], 0
    
    #api 응답을 DB에 맞춰서 변환
    def convert_to_sale_create(
        self,
        item: TransactionItemSchema,
        apt_id: int
    ) -> Optional[SaleCreate]:
        """
        TransactionItemSchema를 SaleCreate로 변환
        
        Args:
            item: 외부 API에서 받은 거래 항목
            apt_id: 아파트 ID
        
        Returns:
            SaleCreate 객체 또는 None (변환 실패 시)
        """
        try:
            # 계약일 생성 (dealYear, dealMonth, dealDay)
            contract_date = None
            try:
                if item.dealYear and item.dealMonth and item.dealDay:
                    contract_date = date(
                        int(item.dealYear),
                        int(item.dealMonth),
                        int(item.dealDay)
                    )
            except (ValueError, TypeError):
                logger.warning(f"계약일 파싱 실패: {item.dealYear}-{item.dealMonth}-{item.dealDay}")
            
            # 거래가격 저장
            trans_price = None
            if item.dealAmount:
                try:
                    # 쉼표 제거 후 문자열 정리
                    amount_str = item.dealAmount.replace(",", "").strip()
                    if amount_str and amount_str != "":
                        # 만원 단위 그대로 저장
                        # 예: "12,000" 만원 → 12000 (만원 단위)
                        amount_float = float(amount_str)
                        trans_price = int(amount_float)
                        
                        # 저장 결과 로깅 (디버깅용)
                        logger.debug(
                            f"거래가격 저장: "
                            f"원본='{item.dealAmount}' 만원 → "
                            f"저장={trans_price:,} 만원"
                        )
                    else:
                        logger.warning(f"거래가격이 빈 문자열입니다: '{item.dealAmount}'")
                except (ValueError, TypeError) as e:
                    logger.error(
                        f"거래가격 파싱 실패: 원본='{item.dealAmount}', "
                        f"오류 타입={type(e).__name__}, 메시지={str(e)}"
                    )
            else:
                logger.debug("거래가격 정보가 없습니다 (dealAmount가 None 또는 빈 값)")
            
            # 전용면적 변환 (제곱미터)
            exclusive_area = 0.0
            if item.excluUseAr:
                try:
                    # 쉼표 제거 후 float 변환
                    area_str = item.excluUseAr.replace(",", "").strip()
                    if area_str:
                        exclusive_area = float(area_str)
                except (ValueError, TypeError):
                    logger.warning(f"전용면적 파싱 실패: {item.excluUseAr}")
                    # 필수 필드이므로 기본값 사용 불가 - None 반환
                    return None
            
            # 층 변환
            floor = 0
            if item.floor:
                try:
                    floor = int(item.floor)
                except (ValueError, TypeError):
                    logger.warning(f"층 파싱 실패: {item.floor}")
            
            # 취소 여부 및 취소일
            is_canceled = item.cdealType == "Y" if item.cdealType else False
            cancel_date = None
            if item.cdealDay and len(item.cdealDay) == 8:
                try:
                    cancel_date = date(
                        int(item.cdealDay[:4]),
                        int(item.cdealDay[4:6]),
                        int(item.cdealDay[6:8])
                    )
                except (ValueError, TypeError):
                    pass
            
            # 거래 유형 (dealingGbn이 있으면 사용, 없으면 기본값)
            trans_type = item.dealingGbn if item.dealingGbn else "매매"
            if len(trans_type) > 10:
                trans_type = trans_type[:10]
            
            # SaleCreate 객체 생성
            sale_create = SaleCreate(
                apt_id=apt_id,
                build_year=item.buildYear if item.buildYear else None,
                trans_type=trans_type,
                trans_price=trans_price,
                exclusive_area=exclusive_area,
                floor=floor,
                building_num=item.aptDong if item.aptDong else None,
                contract_date=contract_date,
                is_canceled=is_canceled,
                cancel_date=cancel_date
            )
            
            return sale_create
            
        except Exception as e:
            logger.error(f"❌ SaleCreate 변환 실패: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    async def collect_sale_transactions(
        self,
        db: AsyncSession,
        *,
        lawd_cd: str,
        deal_ymd: str
    ) -> SaleCollectionResponse:
        """
        특정 법정동코드와 계약년월의 매매 거래 데이터 수집 및 저장
        
        Args:
            db: 데이터베이스 세션
            lawd_cd: 법정동코드 (5자리, 예: "11110")
            deal_ymd: 계약년월 (YYYYMM 형식, 예: "202407")
        
        Returns:
            SaleCollectionResponse: 수집 결과 통계
        """
        total_fetched = 0
        total_saved = 0
        skipped = 0
        not_found_apartment = 0
        errors = []
        
        try:
            logger.info("=" * 80)
            logger.info(f"💰 매매 거래 데이터 수집 시작: 법정동코드={lawd_cd}, 계약년월={deal_ymd}")
            logger.info("=" * 80)
            
            page_no = 1
            has_more = True
            num_of_rows = 1000  # 페이지당 요청할 레코드 수
            
            while has_more:
                # 1. API 데이터 가져오기
                try:
                    api_response = await self.fetch_sale_transaction_data(
                        lawd_cd=lawd_cd,
                        deal_ymd=deal_ymd,
                        page_no=page_no,
                        num_of_rows=num_of_rows
                    )
                except httpx.HTTPError as e:
                    error_msg = f"API 호출 실패 (페이지 {page_no}): {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"❌ {error_msg}")
                    break
                except Exception as e:
                    error_msg = f"API 호출 중 오류 (페이지 {page_no}): {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"❌ {error_msg}")
                    break
                
                # 2. 데이터 파싱
                items, total_count = self.parse_sale_transaction_data(api_response)
                
                # 원본 데이터가 없으면 종료
                if len(items) == 0:
                    logger.info(f"   ℹ️  페이지 {page_no}: 데이터 없음 (종료)")
                    has_more = False
                    break
                
                total_fetched += len(items)
                logger.info(f"   📄 페이지 {page_no}: {len(items)}개 거래 항목 (누적: {total_fetched}개)")
                
                # 3. 각 거래 항목 처리
                for item_idx, item in enumerate(items, 1):
                    try:
                        # 3-1. aptSeq로 아파트 찾기
                        # aptSeq 형식: "11110-2339" (법정동코드-단지코드)
                        # kapt_code로 매칭 시도
                        apt_id = None
                        
                        # aptSeq에서 kapt_code 추출 시도
                        if item.aptSeq and "-" in item.aptSeq:
                            # "11110-2339" 형식에서 뒷부분 추출
                            parts = item.aptSeq.split("-")
                            if len(parts) >= 2:
                                # 뒷부분을 kapt_code로 사용
                                potential_kapt_code = parts[-1]
                                apartment = await apartment_crud.get_by_kapt_code(
                                    db,
                                    kapt_code=potential_kapt_code
                                )
                                if apartment:
                                    apt_id = apartment.apt_id
                        
                        # aptSeq로 찾지 못했으면 aptNm으로 찾기 시도
                        if not apt_id and item.aptNm:
                            # aptNm으로 아파트 검색 (정확히 일치하는 것만)
                            from sqlalchemy import select
                            from app.models.apartment import Apartment
                            result = await db.execute(
                                select(Apartment)
                                .where(Apartment.apt_name == item.aptNm)
                                .where(Apartment.is_deleted == False)
                                .limit(1)
                            )
                            apartment = result.scalar_one_or_none()
                            if apartment:
                                apt_id = apartment.apt_id
                        
                        # 아파트를 찾지 못한 경우
                        if not apt_id:
                            not_found_apartment += 1
                            logger.warning(
                                f"   ⚠️ [{item_idx}/{len(items)}] 아파트를 찾을 수 없음: "
                                f"aptSeq={item.aptSeq}, aptNm={item.aptNm} "
                                f"(건너뜀: {not_found_apartment}개)"
                            )
                            continue
                        
                        # 3-2. SaleCreate로 변환
                        sale_create = self.convert_to_sale_create(item, apt_id)
                        if not sale_create:
                            error_msg = f"SaleCreate 변환 실패: aptSeq={item.aptSeq}"
                            errors.append(error_msg)
                            logger.warning(f"   ⚠️ [{item_idx}/{len(items)}] {error_msg}")
                            continue
                        
                        # 3-3. 중복 체크 및 저장
                        db_obj, is_created = await sale_crud.create_or_skip(
                            db,
                            obj_in=sale_create
                        )
                        
                        if is_created:
                            total_saved += 1
                            logger.info(
                                f"   ✅ [{item_idx}/{len(items)}] 저장 완료: "
                                f"{item.aptNm} {sale_create.trans_price}원 "
                                f"(전체 저장: {total_saved}개)"
                            )
                        else:
                            skipped += 1
                            logger.info(
                                f"   ⏭️  [{item_idx}/{len(items)}] 건너뜀 (중복): "
                                f"{item.aptNm} (전체 건너뜀: {skipped}개)"
                            )
                            
                    except Exception as e:
                        error_msg = f"거래 항목 처리 실패 (aptSeq={item.aptSeq if item else 'Unknown'}): {str(e)}"
                        errors.append(error_msg)
                        logger.warning(f"   ⚠️ [{item_idx}/{len(items)}] {error_msg}")
                        import traceback
                        logger.debug(traceback.format_exc())
                
                # 4. 다음 페이지 확인
                body = TransactionResponseSchema(response=api_response).get_body()
                if body:
                    # 현재 페이지의 항목 수가 요청한 수보다 적으면 마지막 페이지
                    if len(items) < num_of_rows:
                        logger.info(f"   ✅ 마지막 페이지로 판단 (수집 {len(items)}개 < 요청 {num_of_rows}개)")
                        has_more = False
                    else:
                        # 전체 개수 확인
                        if body.totalCount <= total_fetched:
                            logger.info(f"   ✅ 마지막 페이지로 판단 (전체 {body.totalCount}개 중 {total_fetched}개 수집)")
                            has_more = False
                        else:
                            logger.info(f"   ⏭️  다음 페이지로... (전체 {body.totalCount}개 중 {total_fetched}개 수집, 다음 페이지: {page_no + 1})")
                            page_no += 1
                else:
                    # body를 파싱할 수 없으면 현재 페이지가 마지막으로 간주
                    has_more = False
                
                # API 호출 제한 방지를 위한 딜레이
                await asyncio.sleep(0.2)
            
            logger.info("=" * 80)
            logger.info(f"✅ 매매 거래 데이터 수집 완료")
            logger.info(f"   - 수집: {total_fetched}개")
            logger.info(f"   - 저장: {total_saved}개")
            logger.info(f"   - 건너뜀 (중복): {skipped}개")
            logger.info(f"   - 건너뜀 (아파트 없음): {not_found_apartment}개")
            if errors:
                logger.warning(f"   - 오류: {len(errors)}개")
            logger.info("=" * 80)
            
            return SaleCollectionResponse(
                success=len(errors) == 0,
                total_fetched=total_fetched,
                total_saved=total_saved,
                skipped=skipped,
                not_found_apartment=not_found_apartment,
                errors=errors,
                message=f"수집 완료: {total_saved}개 저장, {skipped}개 중복 건너뜀, {not_found_apartment}개 아파트 없음"
            )
            
        except Exception as e:
            logger.error(f"❌ 매매 거래 데이터 수집 실패: {e}", exc_info=True)
            return SaleCollectionResponse(
                success=False,
                total_fetched=total_fetched,
                total_saved=total_saved,
                skipped=skipped,
                not_found_apartment=not_found_apartment,
                errors=errors + [str(e)],
                message=f"수집 실패: {str(e)}"
            )


# 서비스 인스턴스 생성
data_collection_service = DataCollectionService()