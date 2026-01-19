# 모니터링 환경 구축 가이드

## 📊 개요
Prometheus + Grafana를 사용한 백엔드 모니터링 환경 구축 완료

## 🚀 구성 요소

### 1. Prometheus
- **역할**: 메트릭 수집 및 저장
- **포트**: 9090 (기본값, 환경변수 `PROMETHEUS_PORT`로 변경 가능)
- **데이터 보관**: 30일
- **스크랩 주기**: 15초

### 2. Grafana
- **역할**: 메트릭 시각화
- **포트**: 3001 (기본값, 환경변수 `GRAFANA_PORT`로 변경 가능)
- **기본 계정**: 
  - 사용자명: `admin` (환경변수 `GRAFANA_USER`로 변경 가능)
  - 비밀번호: `admin` (환경변수 `GRAFANA_PASSWORD`로 변경 가능)

### 3. FastAPI Backend
- **메트릭 엔드포인트**: `/metrics`
- **수집 메트릭**:
  - HTTP 요청 수 (RPS)
  - HTTP 응답 시간 (p50, p95)
  - HTTP 상태 코드 분포
  - 활성 연결 수
  - 에러율

## 📁 파일 구조

```
backend/
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml          # Prometheus 설정 파일
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/
│       │   │   └── prometheus.yml  # Grafana 데이터소스 프로비저닝
│       │   └── dashboards/
│       │       └── dashboards.yml  # Grafana 대시보드 프로비저닝
│       └── dashboards/
│           └── fastapi-backend.json # FastAPI 대시보드
```

## 🛠️ 실행 방법

### 1. 환경 변수 설정 (선택사항)
`.env` 파일에 다음 변수들을 추가할 수 있습니다:

```env
# Prometheus 포트 (기본값: 9090)
PROMETHEUS_PORT=9090

# Grafana 포트 (기본값: 3001)
GRAFANA_PORT=3001

# Grafana 관리자 계정 (기본값: admin/admin)
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin
```

### 2. 서비스 시작
```bash
# 전체 서비스 시작
docker-compose up -d

# 또는 특정 서비스만 시작
docker-compose up -d prometheus grafana
```

### 3. 접속
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001
- **FastAPI 메트릭**: http://localhost:8000/metrics

## 📈 Grafana 대시보드

### FastAPI Backend 메트릭 대시보드
자동으로 로드되는 대시보드로 다음 메트릭들을 시각화합니다:

1. **HTTP 요청 수 (Requests per Second)**: 초당 HTTP 요청 수
2. **HTTP 응답 시간 (Response Time)**: p50, p95 응답 시간
3. **HTTP 상태 코드 분포**: 상태 코드별 요청 분포
4. **활성 연결 수**: 현재 처리 중인 요청 수
5. **에러율**: 5xx 에러 비율

## 🔍 Prometheus 쿼리 예제

### 요청 수
```
rate(http_requests_total[5m])
```

### 응답 시간 (p95)
```
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### 에러율
```
rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100
```

## 🔧 커스터마이징

### Prometheus 설정 변경
`backend/monitoring/prometheus/prometheus.yml` 파일을 수정한 후:

```bash
# Prometheus 재시작
docker-compose restart prometheus
```

### Grafana 대시보드 수정
1. Grafana 웹 UI에서 대시보드 편집
2. 또는 `backend/monitoring/grafana/dashboards/fastapi-backend.json` 파일 직접 수정

## 📚 참고 자료
- [Prometheus 공식 문서](https://prometheus.io/docs/)
- [Grafana 공식 문서](https://grafana.com/docs/)
- [prometheus-fastapi-instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)
