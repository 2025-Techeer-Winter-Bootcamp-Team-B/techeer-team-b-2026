# 거래 데이터 수집 Service 가이드

> 마지막 업데이트: 2026-01-11

## 📋 개요

아파트 매매 거래 데이터 수집 및 적재 API를 위한 Service 레이어 구성 가이드입니다.

## 🎯 Service 파일 위치 결정

### ✅ 권장: `data_collection.py`에 추가

**이유:**
- 기존 패턴과 일관성 유지
  - 지역 데이터 수집 → `data_collection.py`
  - 아파트 목록 수집 → `data_collection.py`
  - 아파트 상세 정보 수집 → `data_collection.py`
  - **거래 데이터 수집 → `data_collection.py`** ✅
- 모든 데이터 수집 기능이 한 곳에 모여 있어 관리가 쉬움
- `DataCollectionService` 클래스 하나로 모든 수집 기능 관리

### ❌ 비권장: 별도 파일 생성

**이유:**
- `transaction_collection.py` 같은 별도 파일을 만들면:
  - 코드 분산으로 인한 관리 복잡도 증가
  - 기존 패턴과 불일치
  - 중복 코드 가능성 (API 키 관리, 로깅 등)

## 📁 현재 구조

```
backend/app/services/
├── data_collection.py      ← 여기에 거래 수집 메서드 추가 ✅
├── apartment.py            ← 아파트 관련 비즈니스 로직
├── auth.py                 ← 인증 관련 로직
└── how.md                  ← 서비스 가이드
```

## ✅ CRUD 검토 결과

### `crud/transaction.py` 현재 상태

#### ✅ 잘 구현된 부분

1. **기본 CRUD 상속**
   ```python
   class CRUDSale(CRUDBase[Sale, SaleCreate, dict]):
   ```
   - `CRUDBase`를 올바르게 상속
   - 기본 `get`, `create`, `update`, `delete` 메서드 사용 가능

2. **중복 체크 메서드** ✅
   ```python
   async def check_duplicate(...) -> Optional[Sale]
   ```
   - 같은 아파트, 같은 날짜, 같은 가격/면적/층인 거래 체크
   - 데이터 수집 시 필수 기능

3. **create_or_skip 메서드** ✅
   ```python
   async def create_or_skip(...) -> tuple[Optional[Sale], bool]
   ```
   - 중복이면 건너뛰고, 없으면 생성
   - `(객체, 생성여부)` 튜플 반환으로 명확한 피드백

4. **조회 메서드들**
   - `get_by_apartment()` - 아파트별 조회
   - `get_by_date_range()` - 날짜 범위 조회
   - `get_by_price_range()` - 가격 범위 조회
   - `get_active_transactions()` - 활성 거래만 조회

#### ⚠️ 개선 가능한 부분

1. **모델 import 누락 가능성**
   ```python
   # 모든 모델을 import하여 SQLAlchemy 관계 설정이 제대로 작동하도록 함
   from app.models import (  # noqa: F401
       Account,
       State,
       Apartment,
       Sale,  # ← 이게 있는지 확인 필요
       Rent,
       ...
   )
   ```
   - 다른 CRUD 파일들처럼 모델 import 섹션 추가 권장

2. **Rent CRUD 미구현**
   - 현재 `Sale`만 구현되어 있음
   - 전월세 거래도 필요하면 `CRUDRent` 추가 필요

## 🔧 Service 레이어 구현 가이드

### 1. `data_collection.py`에 추가하는 방법

#### Step 1: Import 추가

```python
# 기존 import에 추가
from app.crud.transaction import sale as sale_crud
from app.schemas.transaction import (
    TransactionRequestSchema,
    TransactionResponseSchema,
    TransactionItemSchema,
    SaleCreate,
    SaleCollectionResponse
)
```

#### Step 2: API URL 상수 추가

```python
# 파일 상단의 상수 섹션에 추가
# 국토부 실거래가 API 엔드포인트 (아파트 매매)
MOLIT_APARTMENT_SALE_API_URL = "https://apis.data.go.kr/1613000/AptTradeDevService/getAphusTradeDev"
```

#### Step 3: 메서드 추가

`DataCollectionService` 클래스 안에 다음 메서드들을 추가:

1. **`fetch_sale_transaction_data()`** - 외부 API 호출
2. **`parse_sale_transaction_data()`** - API 응답 파싱
3. **`convert_to_sale_create()`** - 데이터 변환
4. **`collect_sale_transactions()`** - 전체 수집 로직

### 2. 구현 패턴 (기존 코드 참고)

#### 패턴 1: API 호출 메서드

```python
async def fetch_sale_transaction_data(
    self,
    lawd_cd: str,
    deal_ymd: str,
    page_no: int = 1,
    num_of_rows: int = 1000
) -> Dict[str, Any]:
    """
    국토부 API에서 아파트 매매 거래 데이터 가져오기
    
    기존 패턴:
    - fetch_region_data() 참고
    - fetch_apartment_data() 참고
    """
    encoded_key = quote(self.api_key)
    params = {
        "serviceKey": encoded_key,
        "pageNo": str(page_no),
        "numOfRows": str(num_of_rows),
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(MOLIT_APARTMENT_SALE_API_URL, params=params)
        response.raise_for_status()
        return response.json()
```

#### 패턴 2: 파싱 메서드

```python
def parse_sale_transaction_data(
    self,
    api_response: Dict[str, Any]
) -> tuple[List[TransactionItemSchema], int]:
    """
    실거래가 API 응답 파싱
    
    기존 패턴:
    - parse_region_data() 참고
    - parse_apartment_data() 참고
    """
    # TransactionResponseSchema로 파싱
    response_schema = TransactionResponseSchema(response=api_response)
    
    # 헤더 확인
    header = response_schema.get_header()
    if header and header.resultCode != "00":
        return [], 0
    
    # 거래 항목 추출
    items = response_schema.get_items()
    body = response_schema.get_body()
    total_count = body.totalCount if body else len(items)
    
    return items, total_count
```

#### 패턴 3: 데이터 변환 메서드

```python
def convert_to_sale_create(
    self,
    item: TransactionItemSchema,
    apt_id: int
) -> Optional[SaleCreate]:
    """
    TransactionItemSchema를 SaleCreate로 변환
    
    변환 로직:
    - dealYear + dealMonth + dealDay → contract_date
    - dealAmount (만원) → trans_price (원) = dealAmount * 10000
    - excluUseAr → exclusive_area
    - floor (str) → floor (int)
    - cdealType → is_canceled
    - cdealDay → cancel_date
    """
    # ... 변환 로직
    return SaleCreate(...)
```

#### 패턴 4: 전체 수집 메서드

```python
async def collect_sale_transactions(
    self,
    db: AsyncSession,
    *,
    lawd_cd: str,
    deal_ymd: str
) -> SaleCollectionResponse:
    """
    특정 법정동코드와 계약년월의 매매 거래 데이터 수집 및 저장
    
    기존 패턴:
    - collect_all_regions() 참고
    - collect_all_apartments() 참고
    
    처리 흐름:
    1. 페이지네이션하여 모든 데이터 수집
    2. 각 거래 항목 처리:
       a. aptSeq 또는 aptNm으로 아파트 찾기
       b. TransactionItemSchema → SaleCreate 변환
       c. 중복 체크 (sale_crud.check_duplicate)
       d. 저장 (sale_crud.create_or_skip)
    3. 통계 수집 및 반환
    """
    total_fetched = 0
    total_saved = 0
    skipped = 0
    not_found_apartment = 0
    errors = []
    
    page_no = 1
    has_more = True
    
    while has_more:
        # 1. API 호출
        api_response = await self.fetch_sale_transaction_data(...)
        
        # 2. 파싱
        items, total_count = self.parse_sale_transaction_data(api_response)
        
        # 3. 각 항목 처리
        for item in items:
            # 아파트 찾기
            apt_id = await self._find_apartment_by_item(db, item)
            if not apt_id:
                not_found_apartment += 1
                continue
            
            # 변환
            sale_create = self.convert_to_sale_create(item, apt_id)
            if not sale_create:
                continue
            
            # 중복 체크 및 저장
            db_obj, is_created = await sale_crud.create_or_skip(
                db,
                obj_in=sale_create
            )
            
            if is_created:
                total_saved += 1
            else:
                skipped += 1
        
        # 다음 페이지 확인
        if len(items) < num_of_rows:
            has_more = False
        else:
            page_no += 1
        
        await asyncio.sleep(0.2)  # API 호출 제한 방지
    
    return SaleCollectionResponse(...)
```

### 3. 아파트 찾기 헬퍼 메서드

```python
async def _find_apartment_by_item(
    self,
    db: AsyncSession,
    item: TransactionItemSchema
) -> Optional[int]:
    """
    거래 항목에서 아파트 찾기
    
    우선순위:
    1. aptSeq에서 kapt_code 추출 → get_by_kapt_code()
    2. aptNm으로 검색 → 정확히 일치하는 아파트
    """
    # 1순위: aptSeq에서 kapt_code 추출
    if item.aptSeq and "-" in item.aptSeq:
        parts = item.aptSeq.split("-")
        if len(parts) >= 2:
            potential_kapt_code = parts[-1]
            apartment = await apartment_crud.get_by_kapt_code(
                db,
                kapt_code=potential_kapt_code
            )
            if apartment:
                return apartment.apt_id
    
    # 2순위: aptNm으로 검색
    if item.aptNm:
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
            return apartment.apt_id
    
    return None
```

## 📝 CRUD 체크리스트

### ✅ 필수 메서드

- [x] `check_duplicate()` - 중복 거래 체크
- [x] `create_or_skip()` - 중복이면 건너뛰고, 없으면 생성
- [x] `get_by_apartment()` - 아파트별 조회
- [x] `get_by_date_range()` - 날짜 범위 조회

### ✅ 권장 메서드

- [x] `get_by_price_range()` - 가격 범위 조회
- [x] `get_active_transactions()` - 활성 거래만 조회

### ⚠️ 개선 사항

1. **모델 import 추가** (선택)
   ```python
   # crud/transaction.py 상단에 추가
   from app.models import (  # noqa: F401
       Account,
       State,
       Apartment,
       Sale,
       Rent,
       ...
   )
   ```

2. **Rent CRUD 추가** (필요 시)
   ```python
   class CRUDRent(CRUDBase[Rent, RentCreate, dict]):
       # 전월세 거래 CRUD 구현
   ```

## 🎯 최종 권장사항

### Service 파일 구조

```
✅ 권장: data_collection.py에 추가
   - 기존 패턴과 일관성
   - 모든 데이터 수집 기능이 한 곳에
   - 관리 용이

❌ 비권장: transaction_collection.py 별도 생성
   - 코드 분산
   - 패턴 불일치
```

### 구현 순서

1. ✅ **CRUD 완료** - `crud/transaction.py`는 이미 잘 구현됨
2. ✅ **Service 메서드 추가** - `data_collection.py`에 추가
3. ✅ **Endpoint 추가** - `endpoints/data_collection.py`에 추가
4. ✅ **Response Schema 추가** - `schemas/transaction.py`에 `SaleCollectionResponse` 추가

## 📚 참고 파일

- **기존 패턴**: `backend/app/services/data_collection.py`
  - `collect_all_regions()` - 지역 데이터 수집
  - `collect_all_apartments()` - 아파트 목록 수집
  - `collect_apartment_details()` - 아파트 상세 정보 수집
  
- **CRUD 패턴**: `backend/app/crud/state.py`
  - `create_or_skip()` - 중복 체크 및 생성 패턴

- **엔드포인트 패턴**: `backend/app/api/v1/endpoints/data_collection.py`
  - 기존 수집 API 엔드포인트들 참고

## ✅ 검증 체크리스트

### CRUD 검증

- [x] `check_duplicate()` 메서드 존재
- [x] `create_or_skip()` 메서드 존재
- [x] 반환 타입이 `tuple[Optional[Sale], bool]` 형식
- [x] 중복 체크 로직이 적절함 (apt_id, contract_date, 가격/면적/층)
- [x] 에러 처리 (rollback) 포함

### Service 검증

- [x] `data_collection.py`에 메서드 추가됨
- [x] API 호출 메서드 구현
- [x] 파싱 메서드 구현
- [x] 데이터 변환 메서드 구현
- [x] 전체 수집 메서드 구현
- [x] 아파트 찾기 로직 구현
- [x] 페이지네이션 처리
- [x] 에러 처리 및 로깅

### Endpoint 검증

- [x] 엔드포인트 추가됨
- [x] 파라미터 검증
- [x] 에러 처리
- [x] Response Schema 매핑

## 🚀 다음 단계

1. **테스트**: 실제 API 호출 테스트
2. **아파트 매칭 개선**: `aptSeq`와 `kapt_code` 매핑 로직 최적화
3. **에러 처리 강화**: 특정 에러 상황별 처리 로직 추가
4. **로깅 개선**: 더 상세한 진행 상황 로깅
