# Grafana 대시보드 프로비저닝

이 폴더의 JSON 파일들은 Grafana 시작 시 자동으로 로드됩니다.

## 설치된 대시보드

다음 공식 Grafana 대시보드 템플릿이 설치되어 있습니다:

### 1. FastAPI Observability
- **파일**: `fastapi/fastapi-observability.json`
- **템플릿 ID**: [22676](https://grafana.com/grafana/dashboards/22676-fastapi-observability/)
- **설명**: FastAPI 애플리케이션의 HTTP 메트릭, 응답 시간, 요청 수 등을 시각화
- **필요 메트릭**: `prometheus-fastapi-instrumentator`로 수집된 메트릭

### 2. PostgreSQL Exporter
- **파일**: `postgresql/postgresql-exporter.json`
- **템플릿 ID**: [12485](https://grafana.com/grafana/dashboards/12485-postgresql-exporter/)
- **설명**: PostgreSQL 데이터베이스의 성능 메트릭, 연결 수, 쿼리 통계 등을 시각화
- **필요 메트릭**: `postgres_exporter`로 수집된 메트릭

### 3. Redis Dashboard
- **파일**: `redis/redis-dashboard.json`
- **템플릿 ID**: [763](https://grafana.com/grafana/dashboards/763-redis-dashboard-for-prometheus-redis-exporter-1-x/)
- **설명**: Redis 캐시의 메모리 사용량, 명령 통계, 연결 수 등을 시각화
- **필요 메트릭**: `redis_exporter`로 수집된 메트릭

### 4. API 성능 모니터링 (검색 & 실시간 처리)
- **파일**: `api-performance/api-performance-dashboard.json`
- **설명**: 검색 API 및 실시간 처리 속도가 중요한 엔드포인트들의 성능 모니터링 대시보드
- **주요 메트릭**:
  - 검색 API 요청률, 응답 시간 (P50/P95/P99), 에러율, 성공률
  - 주요 엔드포인트별 응답 시간 (대시보드, 아파트 상세, AI 검색, 통계)
  - 시스템 리소스 (CPU, 메모리)
  - 데이터베이스 성능 (연결 수, 쿼리 응답 시간)
  - Redis 메모리 사용량
  - 엔드포인트별 요청 분포
- **필요 메트릭**: `prometheus-fastapi-instrumentator`, `postgres_exporter`, `redis_exporter`로 수집된 메트릭

## 동작 방식

1. Grafana 컨테이너가 시작될 때 `/etc/grafana/provisioning/dashboards/dashboards.yml` 설정을 읽습니다
2. 설정에 따라 `/var/lib/grafana/dashboards` 경로의 JSON 파일들을 스캔합니다
3. 각 JSON 파일을 자동으로 대시보드로 import합니다
4. 모든 대시보드는 `DS_PROMETHEUS` 변수를 통해 Prometheus 데이터소스에 연결됩니다

## 파일 형식

대시보드 JSON 파일은 **직접 dashboard 객체** 형식이어야 합니다 (`dashboard` 래퍼 없이):

```json
{
  "id": null,
  "uid": null,
  "title": "대시보드 이름",
  "tags": ["tag1", "tag2"],
  "schemaVersion": 16,
  "panels": [...],
  ...
}
```

**주의**: `{"dashboard": {...}}` 형식은 지원되지 않습니다. 최상위 레벨에 직접 dashboard 속성들이 와야 합니다.

## 대시보드 추가 방법

1. 이 폴더에 새로운 JSON 파일을 추가합니다
2. 파일 형식이 올바른지 확인합니다 (`id: null`, `uid: null` 필수)
3. Grafana를 재시작하거나 대기합니다 (updateIntervalSeconds: 10초)

## 주의사항

- `id`와 `uid`는 `null`로 설정해야 자동으로 생성됩니다
- `version`은 `0`으로 시작하는 것이 좋습니다
- 파일을 수정하면 10초 내에 자동으로 업데이트됩니다
- 모든 대시보드는 `DS_PROMETHEUS` 변수를 사용하며, Grafana가 자동으로 "Prometheus" 데이터소스와 매칭합니다

## 사용 방법

1. Docker Compose로 서비스를 시작합니다:
   ```bash
   docker-compose up -d grafana prometheus
   ```

2. Grafana에 접속합니다 (기본: http://localhost:3000)

3. 로그인 후 대시보드 메뉴에서 다음 대시보드들을 확인할 수 있습니다:
   - FastAPI Observability
   - PostgreSQL Exporter
   - Redis Dashboard for Prometheus Redis Exporter 1.x
   - 🔍 API 성능 모니터링 (검색 & 실시간 처리)

4. 각 대시보드가 제대로 작동하려면 해당 exporter가 Prometheus에 메트릭을 제공해야 합니다.