# Grafana 대시보드 가이드

## 개요
FastAPI 백엔드의 메트릭을 시각화하는 Grafana 대시보드 설정 가이드입니다.

## 대시보드 구성

### 주요 패널

#### 1. 전체 메트릭
- **전체 HTTP 요청 수 (RPS)**: 초당 요청 수 추이
- **HTTP 응답 시간**: p50, p95, p99 응답 시간
- **HTTP 상태 코드 분포**: 상태 코드별 요청 분포 (2xx, 4xx, 5xx)

#### 2. API 카테고리별 분석
- **API 카테고리별 요청 수**: 주요 API 그룹별 요청 수
  - `/api/v1/auth/*` - 인증
  - `/api/v1/apartments/*` - 아파트 정보
  - `/api/v1/search/*` - 검색
  - `/api/v1/dashboard/*` - 대시보드
  - `/api/v1/favorites/*` - 즐겨찾기
  - `/api/v1/my-properties/*` - 내 집
  - `/api/v1/ai/*` - AI 기능
  - `/api/v1/news/*` - 뉴스
  - `/api/v1/statistics/*` - 통계
  - 등등...

- **API 카테고리별 평균 응답 시간**: 카테고리별 p95 응답 시간

#### 3. 상위 엔드포인트 분석
- **상위 10개 엔드포인트 (요청 수)**: 가장 많이 호출되는 엔드포인트
- **상위 10개 엔드포인트 (응답 시간)**: 가장 느린 엔드포인트

#### 4. 통계 패널
- **활성 연결 수**: 현재 처리 중인 요청 수
- **에러율 (5xx)**: 서버 에러 비율
- **성공률 (2xx)**: 성공한 요청 비율
- **4xx 에러율**: 클라이언트 에러 비율
- **총 요청 수 (누적)**: 지난 1시간 동안의 총 요청 수
- **평균 응답 시간**: 전체 평균 응답 시간
- **평균 TPS**: 초당 평균 트랜잭션 수

#### 5. 분포 차트
- **HTTP 메서드별 분포**: GET, POST, PUT, DELETE 등의 비율
- **API 카테고리별 요청 수 (파이 차트)**: 카테고리별 요청 비율

## Prometheus 메트릭

FastAPI는 `prometheus-fastapi-instrumentator`를 통해 다음 메트릭을 자동으로 수집합니다:

- `http_requests_total`: HTTP 요청 수 (레이블: method, path, status_code)
- `http_request_duration_seconds`: HTTP 응답 시간 히스토그램
- `http_requests_in_progress`: 현재 처리 중인 요청 수

## 주요 쿼리 예시

### 전체 요청 수
```promql
sum(rate(http_requests_total[5m]))
```

### 응답 시간 (p95)
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### 특정 엔드포인트 요청 수
```promql
sum(rate(http_requests_total{path="/api/v1/dashboard/summary"}[5m]))
```

### 에러율 계산
```promql
sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100
```

### API 카테고리별 요청 수
```promql
sum by (path) (rate(http_requests_total{path=~"/api/v1/(auth|apartments|dashboard).*"}[5m]))
```

## 커스터마이징

### 패널 추가
1. Grafana 웹 UI에서 대시보드 편집
2. "Add panel" 클릭
3. PromQL 쿼리 입력
4. 시각화 타입 선택

### 알림 설정
1. 대시보드 패널에서 "Alert" 탭 선택
2. 조건 설정 (예: 에러율 > 5%)
3. 알림 채널 설정 (이메일, Slack 등)

## 참고
- [Prometheus 쿼리 가이드](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana 대시보드 문서](https://grafana.com/docs/grafana/latest/dashboards/)
