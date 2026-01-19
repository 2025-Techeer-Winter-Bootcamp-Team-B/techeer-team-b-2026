# Grafana 대시보드 접근 가이드

## 일반 대시보드 접근 방법

Grafana에 로그인 후 다음 URL로 직접 접근할 수 있습니다:

### Redis 대시보드
```
http://localhost:${GRAFANA_PORT}/d/redis-dashboard
```

### PostgreSQL 대시보드
```
http://localhost:${GRAFANA_PORT}/d/postgresql-exporter
```

### FastAPI 대시보드
```
http://localhost:${GRAFANA_PORT}/d/fastapi-observability
```

## Public Dashboard 사용 방법 (선택사항)

Public Dashboard를 사용하려면:

1. Grafana 웹 UI에 로그인
2. 원하는 대시보드 열기
3. 우측 상단의 **Share** 버튼 클릭
4. **Public dashboard** 탭 선택
5. **Create public dashboard** 버튼 클릭
6. 생성된 Public Dashboard URL 복사하여 사용

Public Dashboard URL 형식:
```
http://localhost:${GRAFANA_PORT}/public-dashboards/{access-token}
```

## 참고 사항

- Public Dashboard는 인증 없이 접근할 수 있습니다
- 일반 대시보드는 Grafana 로그인이 필요합니다
- Public Dashboard는 읽기 전용입니다
