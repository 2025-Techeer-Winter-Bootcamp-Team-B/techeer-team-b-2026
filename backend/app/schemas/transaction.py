"""
실거래가 정보 스키마

외부 API (국토교통부 실거래가 API) 요청/응답 스키마
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from datetime import date


# ============ 외부 API 요청 스키마 ============

class TransactionRequestSchema(BaseModel):
    """
    외부 API (실거래가 정보) 요청 스키마
    
    국토교통부 실거래가 API 요청 파라미터를 정의합니다.
    """
    service_key: str = Field(
        ...,
        alias="serviceKey",  # 실제 API 파라미터: serviceKey
        max_length=100,
        description="공공데이터포털에서 발급받은 인증키 (URL Encode 필요)"
    )
    page_no: Optional[int] = Field(
        1,
        alias="pageNo",  # 실제 API 파라미터: pageNo
        ge=1,
        le=9999,
        description="페이지번호 (기본값: 1, 최대: 9999)"
    )
    num_of_rows: Optional[int] = Field(
        10,
        alias="numOfRows",  # 실제 API 파라미터: numOfRows
        ge=1,
        le=9999,
        description="한 페이지 결과 수 (기본값: 10, 최대: 9999)"
    )
    lawd_cd: str = Field(
        ...,
        min_length=5,
        max_length=5,
        description="행정표준코드관리시스템의 법정동코드 10자리 중 앞 5자리"
    )
    deal_ymd: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="실거래 자료의 계약년월 (YYYYMM 형식 6자리)"
    )
    
    @field_validator('lawd_cd')
    @classmethod
    def validate_lawd_cd(cls, v: str) -> str:
        """법정동코드는 5자리 숫자만 허용"""
        if not v.isdigit():
            raise ValueError('lawd_cd는 5자리 숫자여야 합니다')
        return v
    
    @field_validator('deal_ymd')
    @classmethod
    def validate_deal_ymd(cls, v: str) -> str:
        """계약년월은 6자리 숫자만 허용 (YYYYMM 형식)"""
        if not v.isdigit():
            raise ValueError('deal_ymd는 6자리 숫자(YYYYMM 형식)여야 합니다')
        if len(v) == 6:
            year = int(v[:4])
            month = int(v[4:6])
            if year < 2000 or year > 2100:
                raise ValueError('년도는 2000-2100 사이여야 합니다')
            if month < 1 or month > 12:
                raise ValueError('월은 1-12 사이여야 합니다')
        return v
    
    model_config = ConfigDict(
        populate_by_name=True,  # 필드명(snake_case)과 alias(camelCase) 모두 허용
        json_schema_extra={
            "example": {
                "serviceKey": "YOUR_SERVICE_KEY_ENCODED",  # 실제 API 파라미터 이름
                "pageNo": 1,
                "numOfRows": 10,
                "lawd_cd": "11110",
                "deal_ymd": "202407"
            }
        }
    )


# ============ 외부 API 응답 스키마 ============

#api 호출 성공 실패 여부 확인
class TransactionResponseHeader(BaseModel):
    """응답 헤더 스키마"""
    resultCode: str = Field(..., max_length=3, description="결과코드 (예: 000)")
    resultMsg: str = Field(..., max_length=100, description="결과메시지 (예: OK)")
    
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )


class TransactionItemSchema(BaseModel):
    """
    실거래가 정보 항목 스키마
    
    외부 API 응답의 개별 거래 항목을 정의합니다.
    실제 API 응답의 키 이름과 정확히 일치합니다.
    
    참고: API 문서의 필수/선택 필드 구분에 따라 작성되었습니다.
    """
    # ============ 필수 필드 (Required = 1) ============
    dealYear: str = Field(..., description="계약년도 (예: 2024)")
    dealMonth: str = Field(..., description="계약월 (예: 7)")
    dealDay: str = Field(..., description="계약일 (예: 23)")
    dealAmount: str = Field(..., description="거래금액(만원) (예: 12,000)")
    aptSeq: str = Field(..., description="단지 일련번호 (예: 11110-2339)")
    umdNm: str = Field(..., max_length=60, description="법정동 (예: 17500)")
    aptNm: str = Field(..., max_length=100, description="단지명 (예: 종로중흥S클래스)")
    
    # ============ 선택 필드 (Required = 0) ============
    # 거래 상세 정보
    jibun: Optional[str] = Field(None, description="지번 (예: 202-3)")
    excluUseAr: Optional[str] = Field(None, description="전용면적 (예: 17,811)")
    floor: Optional[str] = Field(None, description="층 (예: 10)")
    buildYear: Optional[str] = Field(None, description="건축년도 (예: 2013)")
    cdealType: Optional[str] = Field(None, max_length=1, description="해제여부")
    cdealDay: Optional[str] = Field(None, max_length=8, description="해제사유발생일 (YYYYMMDD)")
    dealingGbn: Optional[str] = Field(None, description="거래유형 (예: 중개거래)")
    estateAgentSggNm: Optional[str] = Field(None, description="중개사소재지 (예: 서울 종로구)")
    rgstDate: Optional[str] = Field(None, max_length=8, description="등기일자 (YYYYMMDD)")
    aptDong: Optional[str] = Field(None, description="아파트 동명")
    slerGbn: Optional[str] = Field(None, description="매도자 (예: 개인)")
    buyerGbn: Optional[str] = Field(None, description="매수자 (예: 개인)")
    landLeaseholdGbn: Optional[str] = Field(None, description="토지임대부 아파트 여부 (예: N)")
    
    # 주소 관련 필드 (법정동)
    sggCd: Optional[str] = Field(None, max_length=5, description="법정동시군구코드 (예: 11110)")
    umdCd: Optional[str] = Field(None, max_length=5, description="법정동읍면동코드 (예: 숭인동)")
    landCd: Optional[str] = Field(None, max_length=1, description="법정동지번코드 (예: 1)")
    bonbun: Optional[str] = Field(None, max_length=4, description="법정동본번코드 (예: 0202)")
    bubun: Optional[str] = Field(None, max_length=4, description="법정동부번코드 (예: 0003)")
    
    # 주소 관련 필드 (도로명)
    roadNm: Optional[str] = Field(None, max_length=100, description="도로명 (예: 종로66길)")
    roadNmSggCd: Optional[str] = Field(None, max_length=5, description="도로명시군구코드 (예: 11110)")
    roadNmCd: Optional[str] = Field(None, max_length=7, description="도로명코드 (예: 4100372)")
    roadNmSeq: Optional[str] = Field(None, max_length=2, description="도로명일련번호코드 (예: 01)")
    roadNmbCd: Optional[str] = Field(None, max_length=1, description="도로명지상지하코드 (예: 0)")
    roadNmBonbun: Optional[str] = Field(None, max_length=5, description="도로명건물본번호코드 (예: 00028)")
    roadNmBubun: Optional[str] = Field(None, max_length=5, description="도로명건물부번호코드 (예: 00000)")
    
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"  # 외부 API가 추가 필드를 보낼 수 있음
    )

# 페이지 정보, 거래항목 목록
class TransactionResponseBody(BaseModel):
    """응답 본문 스키마"""
    numOfRows: int = Field(..., description="한 페이지 결과 수 (예: 10)")
    pageNo: int = Field(..., description="페이지 번호 (예: 1)")
    totalCount: int = Field(..., description="전체 결과 수 (예: 40)")
    items: Optional[dict] = Field(None, description="거래 항목 목록")
    
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

# 외부 api 전체 응답 구조 감쌈
class TransactionResponseSchema(BaseModel):
    """
    외부 API (실거래가 정보) 응답 스키마
    
    국토교통부 실거래가 API 응답 구조를 정의합니다.
    
    일반적인 응답 구조:
    {
      "response": {
        "header": {
          "resultCode": "000",
          "resultMsg": "OK"
        },
        "body": {
          "items": {
            "item": [
              {
                "dealYear": "2024",
                "dealMonth": "7",
                ...
              }
            ]
          },
          "numOfRows": 10,
          "pageNo": 1,
          "totalCount": 40
        }
      }
    }
    """
    response: Optional[dict] = Field(None, description="API 응답 데이터")
    header: Optional[TransactionResponseHeader] = Field(None, description="응답 헤더")
    body: Optional[TransactionResponseBody] = Field(None, description="응답 본문")
    
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"  # 외부 API가 추가 필드를 보낼 수 있음
    )
    
    def get_items(self) -> list[TransactionItemSchema]:
        """
        응답에서 거래 항목 목록을 추출하는 헬퍼 메서드
        
        Returns:
            TransactionItemSchema 객체 목록
        """
        items_list = []
        
        # response.body.items.item 경로로 접근
        if self.response and isinstance(self.response, dict):
            body = self.response.get("body", {})
            if isinstance(body, dict):
                items = body.get("items", {})
                if isinstance(items, dict):
                    item_list = items.get("item", [])
                    if isinstance(item_list, list):
                        for item_dict in item_list:
                            try:
                                items_list.append(TransactionItemSchema(**item_dict))
                            except Exception as e:
                                # 파싱 실패한 항목은 로깅하고 건너뜀
                                continue
                    elif item_list:  # 단일 항목인 경우
                        try:
                            items_list.append(TransactionItemSchema(**item_list))
                        except Exception:
                            pass
        
        # body.items.item 경로로도 시도 (직접 접근)
        if not items_list and self.body and isinstance(self.body, dict):
            items = self.body.get("items", {})
            if isinstance(items, dict):
                item_list = items.get("item", [])
                if isinstance(item_list, list):
                    for item_dict in item_list:
                        try:
                            items_list.append(TransactionItemSchema(**item_dict))
                        except Exception:
                            continue
                elif item_list:
                    try:
                        items_list.append(TransactionItemSchema(**item_list))
                    except Exception:
                        pass
        
        return items_list
    
    def get_header(self) -> Optional[TransactionResponseHeader]:
        """응답 헤더를 반환하는 헬퍼 메서드"""
        if self.header:
            return self.header
        
        if self.response and isinstance(self.response, dict):
            header_data = self.response.get("header", {})
            if header_data:
                try:
                    return TransactionResponseHeader(**header_data)
                except Exception:
                    pass
        
        return None
    
    def get_body(self) -> Optional[TransactionResponseBody]:
        """응답 본문을 반환하는 헬퍼 메서드"""
        if self.body:
            return self.body
        
        if self.response and isinstance(self.response, dict):
            body_data = self.response.get("body", {})
            if body_data:
                try:
                    return TransactionResponseBody(**body_data)
                except Exception:
                    pass
        
        return None


# ============ DB 저장용 스키마 ============
# 이 스키마들은 외부 API 응답을 파싱해서 DB에 저장할 때 사용합니다.
# DB 모델(app.models.sale.Sale, app.models.rent.Rent) 구조에 맞게 작성되었습니다.

class SaleCreate(BaseModel):
    """
    매매 거래 정보 생성 스키마 (DB 저장용)
    
    app.models.sale.Sale 모델 구조에 맞춰 작성되었습니다.
    PK(trans_id), 자동 생성 필드(created_at, updated_at, is_deleted)는 제외됩니다.
    """
    apt_id: int = Field(..., description="아파트 ID (FK, 필수)")
    build_year: Optional[str] = Field(None, max_length=255, description="건축년도")
    trans_type: str = Field(..., max_length=10, description="거래 유형 (필수)")
    trans_price: Optional[int] = Field(None, description="거래가격 (만원 단위)")
    exclusive_area: float = Field(..., description="전용면적 (㎡, 필수)")
    floor: int = Field(..., description="층 (필수)")
    building_num: Optional[str] = Field(None, max_length=10, description="건물번호")
    contract_date: Optional[date] = Field(None, description="계약일")
    is_canceled: bool = Field(False, description="취소 여부 (기본값: False)")
    cancel_date: Optional[date] = Field(None, description="취소일")
    created_at: Optional[date] = Field(None, description="생성담당")
    updated_at: Optional[date] = Field(None, description="수정담당")
    is_deleted: Optional[date] = Field(None, description="삭제여부")
    
    model_config = ConfigDict(from_attributes=True)


class SaleCollectionResponse(BaseModel):
    """매매 거래 데이터 수집 응답 스키마"""
    success: bool = Field(..., description="수집 성공 여부")
    total_fetched: int = Field(..., description="API에서 가져온 총 레코드 수")
    total_saved: int = Field(..., description="데이터베이스에 저장된 레코드 수")
    skipped: int = Field(..., description="중복으로 건너뛴 레코드 수")
    not_found_apartment: int = Field(0, description="아파트를 찾을 수 없어 건너뛴 거래 수")
    errors: list[str] = Field(default_factory=list, description="오류 메시지 목록")
    message: str = Field(..., description="결과 메시지")


