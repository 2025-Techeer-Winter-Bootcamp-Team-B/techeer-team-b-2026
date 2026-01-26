# ⚙️ Backend 기술 스택

백엔드에서 사용된 기술들과 선택 이유를 상세히 설명합니다.

---

## 1. FastAPI + Python

### 선택 이유

| 항목 | Django | Flask | FastAPI |
|------|--------|-------|---------|
| 비동기 지원 | 제한적 | 없음 | 네이티브 |
| 타입 힌트 | 선택적 | 선택적 | 필수 |
| 자동 문서화 | DRF 필요 | 별도 설정 | 자동 (Swagger/ReDoc) |
| 성능 (RPS) | ~5,000 | ~10,000 | ~15,000+ |

**FastAPI**를 선택한 이유:
1. **비동기 네이티브**: async/await로 I/O 바운드 작업 최적화
2. **자동 API 문서화**: Swagger UI, ReDoc 자동 생성
3. **Pydantic 통합**: 요청/응답 데이터 자동 검증
4. **높은 성능**: Django 대비 2-3배 빠른 응답 속도

### 적용 사례

```python
# app/api/v1/endpoints/apartments.py
from fastapi import APIRouter, Depends
from app.schemas.apartment import ApartmentResponse

router = APIRouter()

@router.get("/{apt_id}", response_model=ApartmentResponse)
async def get_apartment(
    apt_id: int,
    db: AsyncSession = Depends(get_db)
) -> ApartmentResponse:
    """아파트 상세 정보 조회"""
    apartment = await apartment_service.get_by_id(db, apt_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="아파트를 찾을 수 없습니다")
    return apartment
```

---

## 2. SQLAlchemy + Pydantic

### SQLAlchemy (ORM)

| 항목 | Raw SQL | Django ORM | SQLAlchemy |
|------|---------|------------|------------|
| 유연성 | 최고 | 중간 | 높음 |
| 비동기 지원 | - | 제한적 | 완벽 |
| 복잡한 쿼리 | 쉬움 | 어려움 | 유연함 |
| 마이그레이션 | 직접 | 자동 | Alembic |

**SQLAlchemy 2.0**을 선택한 이유:
1. **AsyncSession**: FastAPI의 비동기 처리와 완벽 호환
2. **ORM + Core**: 필요에 따라 ORM 또는 Raw SQL 선택
3. **관계 로딩**: selectinload, joinedload로 N+1 문제 해결

```python
# app/models/apartment.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class Apartment(Base):
    __tablename__ = "apartments"
    
    apt_id = Column(Integer, primary_key=True)
    apt_name = Column(String(100), nullable=False, index=True)
    region_id = Column(Integer, ForeignKey("regions.region_id"))
    
    region = relationship("Region", back_populates="apartments")
    sales = relationship("Sale", back_populates="apartment")
```

### Pydantic (데이터 검증)

```python
# app/schemas/apartment.py
from pydantic import BaseModel, Field

class ApartmentCreate(BaseModel):
    apt_name: str = Field(..., min_length=1, max_length=100)
    region_id: int = Field(..., gt=0)
    
    class Config:
        from_attributes = True

class ApartmentResponse(ApartmentCreate):
    apt_id: int
    region_name: str
```

---

## 3. orjson (고성능 JSON 직렬화)

### 선택 이유

| 라이브러리 | 직렬화 속도 | 역직렬화 속도 | 특징 |
|-----------|------------|--------------|------|
| json (표준) | 1x | 1x | 기본 |
| ujson | 3x | 2x | 빠름 |
| **orjson** | **5x** | **3x** | **가장 빠름** |

**orjson**을 선택한 이유:
1. **최고 성능**: 표준 json 대비 5배 빠른 직렬화
2. **메모리 효율**: 더 적은 메모리 사용
3. **datetime 지원**: ISO 8601 형식 자동 변환

### 적용 사례

```python
# app/main.py
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

app = FastAPI(
    default_response_class=ORJSONResponse,  # 모든 응답에 orjson 적용
)
```

### 성능 측정 결과

```
대시보드 API (500개 데이터 포인트):
- json: 45ms
- orjson: 9ms (5배 향상)
```

---

## 4. Uvicorn (ASGI 서버)

### 선택 이유

| 서버 | 타입 | 성능 | 특징 |
|------|------|------|------|
| Gunicorn | WSGI | 중간 | 동기 처리 |
| Hypercorn | ASGI | 높음 | HTTP/2 지원 |
| **Uvicorn** | ASGI | **최고** | 경량, 빠름 |

**Uvicorn**을 선택한 이유:
1. **ASGI 네이티브**: FastAPI와 완벽 호환
2. **멀티 워커**: CPU 코어 최대 활용
3. **경량**: 빠른 시작, 낮은 메모리 사용

### 적용 사례

```bash
# 프로덕션 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 개발 환경 (자동 리로드)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 5. Clerk (인증)

### 선택 이유

| 서비스 | 자체 구현 | Auth0 | Clerk |
|--------|----------|-------|-------|
| 구현 시간 | 2-4주 | 1주 | 1-2일 |
| UI 컴포넌트 | 직접 개발 | 제공 | 제공 |
| 소셜 로그인 | 직접 통합 | 쉬움 | 매우 쉬움 |
| 웹훅 | 직접 구현 | 제공 | 제공 |

**Clerk**를 선택한 이유:
1. **빠른 구현**: 로그인 UI, 소셜 로그인 자동 처리
2. **웹훅 통합**: 사용자 생성/수정/삭제 자동 동기화
3. **JWT 기반**: 표준 JWT로 백엔드 검증 용이

### 적용 사례

```python
# app/api/v1/deps.py
async def verify_clerk_token(authorization: str) -> dict:
    """Clerk JWT 토큰 검증"""
    token = authorization.replace("Bearer ", "")
    
    # JWKS에서 공개 키 가져오기
    jwks_client = jwt.PyJWKClient(settings.CLERK_JWKS_URL)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    
    # 토큰 검증
    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=settings.CLERK_ISSUER,
    )
    return payload
```

---

## 6. Google Gemini API (AI 검색)

### 선택 이유

| 모델 | 속도 | 비용 | 한국어 지원 |
|------|------|------|------------|
| GPT-4 | 느림 | 높음 | 좋음 |
| Claude | 중간 | 중간 | 좋음 |
| **Gemini Flash** | **빠름** | **저렴** | **우수** |

**Gemini 3.0 Flash**를 선택한 이유:
1. **빠른 응답**: 자연어 검색에 적합한 빠른 응답 속도
2. **비용 효율**: 다른 모델 대비 저렴한 API 비용
3. **한국어 이해**: 한국어 자연어 쿼리 이해도 우수

### 적용 사례

```python
# app/services/ai_search.py
async def parse_natural_language_query(query: str) -> SearchParams:
    """자연어 쿼리를 구조화된 검색 조건으로 변환"""
    prompt = f"""
    다음 부동산 검색 쿼리를 분석하여 JSON으로 변환하세요:
    "{query}"
    
    반환 형식:
    {{
        "location": "지역명",
        "max_price": 가격(억 단위),
        "transaction_type": "sale|jeonse|monthly",
        "min_area": 면적(평)
    }}
    """
    
    response = await gemini_client.generate(prompt)
    return SearchParams(**json.loads(response))
```

---

## 📊 성능 개선 효과

| 지표 | 개선 전 | 개선 후 | 개선율 |
|------|---------|---------|--------|
| API 응답 시간 | 200ms | 50ms | **75%↓** |
| 동시 처리 | 100 RPS | 500 RPS | **5x↑** |
| JSON 직렬화 | 45ms | 9ms | **80%↓** |
| 인증 구현 시간 | 2주 | 2일 | **85%↓** |
