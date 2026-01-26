# SWEETHOME: 부동산 데이터 분석 서비스 개발기

## 들어가며

"이 아파트 얼마에 팔렸지?" "요즘 전세 시세가 어떻게 되나?"

부동산에 관심 있는 분이라면 한 번쯤 이런 궁금증을 가져보셨을 겁니다. 그래서 시작한 프로젝트가 SWEETHOME입니다.

SWEETHOME은 국토교통부 공공 데이터 API를 활용하여 전국 아파트 매매·전월세 거래 정보를 수집하고, 사용자에게 직관적인 대시보드와 검색 기능을 제공하는 서비스입니다.

## 핵심 기능

1. 실시간 거래 데이터 조회: 전국 아파트 매매·전월세 실거래가 검색
2. 대시보드: 지역별 거래량 추이, 평균 가격 변동 시각화
3. 통계 분석: RVOL(상대 거래량), 4분면 분석으로 시장 흐름 파악
4. AI 검색: 자연어로 아파트 검색 (예: "강남역 근처 3억 이하 전세")
5. 뉴스 크롤링: 부동산 관련 최신 뉴스 자동 수집
6. 즐겨찾기 & 알림: 관심 아파트 등록 및 거래 알림


# 기술 스택

## Frontend

### Vite + React + TypeScript

Vite는 React를 지원하는 빌드 툴로써, 번들링과 esbuild 시스템을 조합하여 빠른 빌드 속도를 보여줍니다. Create React App 대비 개발 서버 시작이 10배 이상 빨랐고, HMR(Hot Module Replacement)도 즉각적으로 반영되어 개발 생산성이 크게 향상되었습니다.

React는 컴포넌트 기반 UI 라이브러리로, 함수형 컴포넌트와 Hooks, Router DOM을 지원합니다. 대시보드, 검색 결과, 아파트 상세 페이지 등 다양한 화면을 컴포넌트 단위로 분리하여 재사용성을 높였습니다.

또한 TypeScript를 사용하여 프로젝트의 타입 안정성을 더하였습니다. API 응답 타입을 미리 정의해두어 런타임 에러를 줄이고, IDE의 자동완성 기능을 최대한 활용할 수 있었습니다.

### React Native + Expo

모바일 앱 개발을 위해 React Native와 Expo를 사용하였습니다. 웹에서 사용한 React 지식을 그대로 활용할 수 있어 학습 비용을 줄였고, Expo의 관리형 워크플로우를 통해 네이티브 빌드 설정 없이 빠르게 앱을 개발할 수 있었습니다. 하나의 코드베이스로 iOS와 Android 앱을 동시에 배포하였습니다.

### Tailwind CSS

Tailwind CSS는 유틸리티 우선 CSS 프레임워크로, 클래스명으로 즉시 스타일링이 가능하고 반응형 디자인에 탁월하여 채택하였습니다. 별도의 CSS 파일을 작성하지 않고도 컴포넌트 내에서 스타일을 정의할 수 있어 개발 속도가 빨라졌습니다. 대시보드의 차트 레이아웃, 검색 결과 카드, 모바일 반응형 디자인 등에 활용하였습니다.

### React Query + Axios

백엔드와의 효과적인 API 연동을 위하여 Axios 라이브러리로 HTTP 통신하였고, 이때의 데이터를 자동으로 패칭, 캐싱, 동기화할 수 있게 하는 TanStack React Query를 사용하여 서버 상태 관리를 더욱 쉽게 하였습니다.

대시보드 데이터, 검색 결과, 아파트 상세 정보 등을 React Query로 관리하여 로딩 상태, 에러 처리, 캐시 무효화를 선언적으로 처리하였습니다. staleTime과 cacheTime을 적절히 설정하여 불필요한 API 호출을 줄였습니다.

### React Context

React에 내장된 상태 관리 라이브러리로, Provider를 통해 상태를 전역으로 전달하고 관심사에 따른 Context 분리를 통해서 간편한 상태 관리를 할 수 있도록 하였습니다. 인증 상태(AuthContext), 테마 설정(ThemeContext), 즐겨찾기 목록(FavoriteContext) 등을 Context로 분리하여 관리하였습니다.


## Backend

### FastAPI + Python

FastAPI는 Python 기반의 비동기 웹 프레임워크로, async/await를 네이티브로 지원하여 I/O 바운드 작업에 유리합니다. 아파트 검색, 통계 조회, 외부 API 호출 등 대부분의 작업이 I/O 바운드이므로 FastAPI의 비동기 처리가 성능에 큰 도움이 되었습니다.

Swagger UI와 ReDoc을 자동으로 생성해주어 API 문서화에 별도 노력이 필요 없었고, Pydantic과의 통합으로 요청/응답 데이터의 타입 검증을 런타임에 자동으로 수행합니다. Django 대비 2-3배 빠른 응답 속도를 보여주었습니다.

### SQLAlchemy + Pydantic

SQLAlchemy는 Python ORM으로, 데이터베이스 테이블을 Python 클래스로 매핑하여 SQL 없이도 데이터를 조작할 수 있습니다. 비동기 세션(AsyncSession)을 사용하여 FastAPI의 비동기 처리와 호환되도록 구성하였습니다.

Pydantic은 데이터 검증 라이브러리로, API의 요청/응답 스키마를 정의하는 데 사용하였습니다. 아파트 검색 필터, 통계 조회 파라미터, 사용자 정보 등의 스키마를 정의하여 잘못된 데이터가 들어오면 자동으로 에러를 반환합니다.

### orjson

기본 json 모듈 대신 orjson을 사용하여 JSON 직렬화 속도를 약 5배 향상시켰습니다. 대시보드 API는 수백 개의 데이터 포인트를 반환하는데, orjson을 적용하여 응답 생성 시간을 크게 단축하였습니다. FastAPI의 default_response_class를 ORJSONResponse로 설정하여 모든 API에 적용하였습니다.

### Uvicorn

Uvicorn은 ASGI 서버로, FastAPI 애플리케이션을 실행하는 데 사용하였습니다. 멀티 워커 모드로 실행하여 CPU 코어를 최대한 활용하고, 동시 요청 처리 능력을 높였습니다.


## Database

### PostgreSQL 15 + PostGIS

PostgreSQL은 안정성과 확장성이 뛰어난 관계형 데이터베이스입니다. 아파트 정보, 거래 내역, 사용자 데이터 등을 저장하는 메인 데이터베이스로 사용하였습니다.

PostGIS는 PostgreSQL의 공간 데이터 확장으로, 위치 기반 검색을 위해 도입하였습니다. 아파트의 위도/경도를 geometry 타입으로 저장하고, ST_DWithin 함수로 "강남역에서 도보 10분 이내" 같은 반경 검색을 구현하였습니다. ST_X, ST_Y 함수로 좌표를 추출하여 지도에 마커를 표시합니다.

### pg_trgm

PostgreSQL의 pg_trgm 확장을 사용하여 유사도 기반 검색을 구현하였습니다. 사용자가 "래미안"이라고 검색하면 "래미안강남", "래미안서초" 등 유사한 이름의 아파트를 찾아줍니다. GIN 인덱스를 생성하여 검색 속도를 최적화하였습니다.

### Redis

Redis는 인메모리 캐시로, 자주 조회되는 데이터를 캐싱하여 응답 속도를 높이는 데 사용하였습니다. 대시보드 통계, 검색 결과, 아파트 상세 정보 등을 Redis에 캐싱하여 데이터베이스 부하를 줄였습니다.

서버 시작 시 홈 화면에 필요한 데이터를 미리 캐싱하는 캐시 예열(Cache Warmup) 기능을 구현하여 Cold Start 문제를 해결하였습니다. TTL은 데이터 특성에 따라 30분에서 12시간까지 다르게 설정하였습니다.


## Auth

### Clerk + JWT

Clerk는 사용자 인증을 쉽게 구현할 수 있게 해주는 서비스입니다. 회원가입/로그인 UI, 소셜 로그인(Google, GitHub 등), 비밀번호 재설정, 이메일 인증을 자동으로 처리해줍니다.

사용자가 Clerk UI로 로그인하면 JWT 토큰이 발급되고, 프론트엔드가 API 요청 시 Authorization 헤더에 토큰을 포함합니다. 백엔드에서는 Clerk 공개키로 토큰을 검증하고 사용자 정보를 조회합니다.

Clerk 웹훅을 설정하여 사용자가 생성/수정/삭제될 때 백엔드 DB와 동기화하도록 구현하였습니다. 이를 통해 Clerk의 사용자 정보와 내부 DB의 사용자 정보를 일치시켰습니다.


## AI

### Google Gemini API

Gemini API를 사용하여 자연어 검색 기능을 구현하였습니다. "강남역 근처 3억 이하 전세"라는 자연어 쿼리를 분석하여 location, max_price, transaction_type 등 구조화된 검색 조건으로 변환합니다.

타임아웃을 30초로 설정하고, API 호출 실패 시 사용자에게 친절한 에러 메시지를 반환하도록 처리하였습니다. Gemini 3.0 Flash 모델을 사용하여 빠른 응답 속도를 확보하였습니다.


## External API

### 국토교통부 공공 데이터 API

전국 아파트 매매·전월세 실거래가 데이터를 수집하는 데 사용하였습니다. 월별로 거래 데이터를 조회하여 DB에 저장하고, 새로운 거래가 등록되면 업데이트합니다.

API 응답의 아파트명과 DB에 저장된 아파트명이 미묘하게 다른 문제(띄어쓰기, 특수문자, 약어 차이)를 해결하기 위해 3단계 매칭 알고리즘을 설계하였습니다.

### Kakao Maps API

아파트 위치를 지도에 표시하고, 주소를 좌표로 변환(지오코딩)하는 데 사용하였습니다. 검색 결과를 지도에 마커로 표시하고, 클러스터링을 적용하여 많은 마커가 있을 때도 깔끔하게 보이도록 하였습니다.


## DevOps

### Docker + Docker Compose

Docker를 활용하여 애플리케이션을 패키징함으로써 개발자가 로컬 환경에서 실행하는 애플리케이션과 실제 배포 환경에서 실행되는 애플리케이션의 차이를 줄이고, 배포 안정성을 높였습니다.

Docker Compose로 FastAPI, PostgreSQL, Redis, Prometheus, Grafana 등 다양한 서비스를 하나의 환경에 구성하여 설정 과정을 단순화했습니다. docker-compose up 한 번으로 전체 개발 환경을 실행할 수 있습니다.

### Nginx

Nginx를 리버스 프록시로 사용하여 SSL 종료, 로드 밸런싱, 정적 파일 서빙을 처리하였습니다. 캐싱 헤더를 설정하여 클라이언트 캐시를 활용하고, Gzip 압축을 적용하여 응답 크기를 줄였습니다.

### AWS EC2

백엔드 서버를 EC2 인스턴스에 배포하였습니다. t4g.micro 인스턴스를 사용하여 비용을 최소화하면서도 안정적인 서비스를 제공하였습니다.

### Vercel

프론트엔드(React 웹)를 Vercel에 배포하였습니다. GitHub 저장소와 연동하여 main 브랜치에 푸시하면 자동으로 빌드 및 배포됩니다. CDN을 통해 전 세계에서 빠른 로딩 속도를 제공합니다.

### GitHub Actions (CI/CD)

지속적인 통합(CI)과 지속적인 배포(CD) 파이프라인을 구축하여 테스트, 빌드, 배포를 자동화합니다. PR이 올라오면 자동으로 린트와 테스트를 실행하고, main 브랜치에 머지되면 EC2에 자동 배포됩니다.


## Monitoring

### Prometheus + Grafana

서비스 안정성을 유지하고 리소스 사용량을 실시간으로 추적하기 위해 Prometheus와 Grafana를 사용하여 메트릭 모니터링 시스템을 구축하였습니다.

FastAPI에 prometheus-fastapi-instrumentator를 적용하여 HTTP 요청 수, 응답 시간, 에러율 등을 자동으로 수집합니다. Grafana 대시보드에서 초당 요청 수(RPS), p50/p95/p99 응답 시간, 5xx 에러 비율, API 카테고리별 요청 수를 시각화하였습니다.

### 성능 모니터링 미들웨어

느린 요청을 감지하고 로깅하는 커스텀 미들웨어를 구현하였습니다. 5초 이상 걸리는 요청은 경고 로그를 남기고, 60초를 초과하면 타임아웃 에러를 반환합니다. 응답 헤더에 X-Response-Time을 추가하여 디버깅에 활용합니다.


# 문제 해결 및 최적화

## 검색 성능 최적화

### 문제

처음에는 단순한 LIKE 검색으로 구현했습니다.

```sql
SELECT * FROM apartments 
WHERE apt_name LIKE '%래미안%'
ORDER BY apt_name;
```

아파트가 10만 건이 넘어가니 검색이 2-3초씩 걸렸습니다. LIKE '%검색어%'는 인덱스를 타지 않기 때문입니다.

### 해결: 2단계 검색

1단계로 PREFIX 검색(인덱스 활용)을 먼저 시도하고, 결과가 부족하면 2단계로 pg_trgm 유사도 검색을 수행합니다.

```python
async def search_apartments(self, db: AsyncSession, query: str, limit: int = 10):
    # 1단계: 빠른 PREFIX 검색
    fast_results = await self._fast_like_search(db, query, limit)
    
    if len(fast_results) >= limit:
        return fast_results[:limit]
    
    # 2단계: 유사도 검색 (1단계 결과 부족 시)
    found_apt_ids = {r["apt_id"] for r in fast_results}
    remaining_limit = limit - len(fast_results)
    
    similarity_results = await self._similarity_search(
        db, query, remaining_limit, exclude_apt_ids=found_apt_ids
    )
    
    return fast_results + similarity_results
```

검색 속도가 2-3초에서 50-100ms로 개선되었습니다.


## Cold Start 문제 해결

### 문제

서버를 재시작하면 첫 번째 대시보드 요청이 3-5초나 걸렸습니다. 복잡한 통계 쿼리를 실행하느라 시간이 오래 걸린 것입니다.

### 해결: 캐시 예열

서버 시작 시 홈 화면에 필요한 데이터를 미리 캐싱하도록 했습니다.

```python
@app.on_event("startup")
async def startup_event():
    await get_redis_client()
    asyncio.create_task(preload_all_statistics())
```

캐싱 대상은 홈 화면에서 가장 많이 호출되는 API들입니다. TTL은 12시간으로 설정하여 부동산 데이터 업데이트 주기에 맞추었습니다.


## Connection Pool 문제

### 문제

동시 요청이 많아지면 "connection pool exhausted" 에러가 발생했습니다. 기본 설정(pool_size=5)으로는 부족했습니다.

### 해결

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # 5에서 20으로
    max_overflow=40,       # 10에서 40으로
    pool_timeout=30,
    pool_recycle=1800,     # 30분마다 연결 재활용
    pool_pre_ping=True,    # 연결 유효성 사전 확인
)
```

pool_pre_ping=True는 PostgreSQL이 일정 시간 동안 사용되지 않은 연결을 끊어버리는 문제를 해결합니다.


## 통계 쿼리 최적화

### 문제

월별 거래량 통계를 계산하는 쿼리가 매번 수십만 건의 거래 데이터를 집계해야 해서 3-5초씩 걸렸습니다.

### 해결: Materialized View

```sql
CREATE MATERIALIZED VIEW mv_monthly_transaction_stats AS
SELECT 
    DATE_TRUNC('month', contract_date) AS month,
    region_id,
    transaction_type,
    COUNT(*) AS transaction_count,
    AVG(trans_price) AS avg_price
FROM (
    SELECT contract_date, trans_price, 'sale' AS transaction_type, apt_id
    FROM sales WHERE is_canceled = FALSE AND is_deleted = FALSE
    UNION ALL
    SELECT deal_date, deposit_price, 'rent' AS transaction_type, apt_id
    FROM rents WHERE is_deleted = FALSE
) transactions
JOIN apartments ON transactions.apt_id = apartments.apt_id
GROUP BY month, region_id, transaction_type;

CREATE INDEX idx_mv_monthly_stats_month ON mv_monthly_transaction_stats(month);
CREATE INDEX idx_mv_monthly_stats_region ON mv_monthly_transaction_stats(region_id);
```

주기적으로 REFRESH MATERIALIZED VIEW CONCURRENTLY를 실행하여 데이터를 갱신합니다. 통계 쿼리 속도가 3-5초에서 100-200ms로 개선되었습니다.


## 아파트 매칭 알고리즘

### 문제

국토교통부 API 응답의 아파트명과 DB에 저장된 아파트명이 미묘하게 다릅니다.

```
API 응답: "래미안 강남 파크스위트"
DB 저장: "래미안강남파크스위트"
```

### 해결: 3단계 매칭

1단계 Hierarchical Blocking: 같은 시군구 코드 내에서만 후보 검색

2단계 Veto 검사: 지번 주소가 완전히 다르거나 준공년도가 5년 이상 차이나면 즉시 탈락

3단계 스코어링: 아파트명 유사도(가중치 0.5), 지번 주소 일치(가중치 0.3), 준공년도 일치(가중치 0.2)로 점수 계산

이 알고리즘으로 매칭 정확도가 95% 이상으로 향상되었습니다.


## 통계 서비스

### RVOL (상대 거래량)

현재 거래량을 과거 평균과 비교하여 시장 활성화 정도를 측정합니다.

```python
rvol = current_volume / average_volume

if rvol > 1.5:
    signal = "거래 급증"
elif rvol > 1.0:
    signal = "거래 활발"
elif rvol > 0.7:
    signal = "보통"
else:
    signal = "거래 위축"
```

### 4분면 분석

매매 변화율과 전세 변화율을 기준으로 시장을 분류합니다.

1분면: 매매 상승, 전세 하락 → 매수 전환
2분면: 매매 하락, 전세 상승 → 임대 선호
3분면: 둘 다 하락 → 시장 위축
4분면: 둘 다 상승 → 활성화


## 마치며

SWEETHOME을 개발하면서 가장 많이 배운 것은 "성능 최적화는 측정에서 시작한다"는 점입니다. Prometheus/Grafana로 정확히 어느 API가 몇 초 걸리는지 측정하고, 병목을 찾아 하나씩 해결해 나갔습니다.

처음에는 단순한 CRUD API로 시작했지만, 사용자가 늘어나고 데이터가 쌓이면서 하나씩 병목이 드러났습니다. 그때마다 캐싱, 인덱스, 비동기 처리 등의 기법을 적용하며 문제를 해결해 나갔습니다.

향후 계획:
1. Kubernetes 마이그레이션
2. WebSocket을 활용한 실시간 거래 알림
3. 사용자 검색 이력 기반 아파트 추천
