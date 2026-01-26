# 🚀 DevOps 기술 스택

DevOps 및 인프라에서 사용된 기술들과 선택 이유를 상세히 설명합니다.

---

## 1. Docker + Docker Compose

### 선택 이유

| 항목 | 직접 설치 | 가상머신 | Docker |
|------|----------|----------|--------|
| 환경 일관성 | 낮음 | 중간 | **높음** |
| 리소스 사용 | 최소 | 많음 | **적음** |
| 시작 시간 | 즉시 | 분 단위 | **초 단위** |
| 이식성 | 낮음 | 중간 | **높음** |

**Docker**를 선택한 이유:
1. **환경 일관성**: 개발/테스트/프로덕션 환경 동일
2. **빠른 배포**: 이미지 기반으로 빠른 배포
3. **격리**: 서비스 간 독립적인 환경

### 적용 사례

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY app/ ./app/

# 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://...
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgis/postgis:15-3.3
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=sweethome
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD}

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    volumes:
      - ./monitoring/grafana:/etc/grafana/provisioning
    ports:
      - "3001:3000"
```

---

## 2. Nginx (리버스 프록시)

### 선택 이유

| 항목 | Apache | Nginx | Caddy |
|------|--------|-------|-------|
| 성능 | 중간 | **높음** | 높음 |
| 메모리 | 많음 | **적음** | 적음 |
| 설정 난이도 | 중간 | 중간 | 쉬움 |
| 기능 | 다양 | **다양** | 기본 |

**Nginx**를 선택한 이유:
1. **고성능**: 이벤트 기반으로 높은 동시 처리 능력
2. **리버스 프록시**: 로드 밸런싱, SSL 종료 처리
3. **정적 파일 서빙**: 빠른 정적 파일 제공
4. **캐싱**: 클라이언트 캐시 헤더 설정

### 적용 사례

```nginx
# nginx-backend.conf
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name api.sweethome.com;

    # Gzip 압축
    gzip on;
    gzip_types application/json text/plain;
    gzip_min_length 1000;

    # 캐싱 헤더
    location ~* \.(js|css|png|jpg|jpeg|gif|ico)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # API 프록시
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # 타임아웃 설정
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

---

## 3. AWS EC2

### 선택 이유

| 서비스 | AWS EC2 | AWS Lambda | Vercel |
|--------|---------|------------|--------|
| 유연성 | **최고** | 제한적 | 제한적 |
| 비용 | 중간 | 사용량 | 고정 |
| 상시 실행 | **가능** | Cold Start | 가능 |
| Docker | **지원** | 제한적 | 미지원 |

**AWS EC2**를 선택한 이유:
1. **유연성**: 필요한 소프트웨어 자유롭게 설치
2. **Docker 지원**: Docker Compose로 전체 스택 실행
3. **비용 효율**: t4g.micro로 저비용 운영

### 인스턴스 구성

```
인스턴스: t4g.micro (ARM)
OS: Ubuntu 22.04
Docker: 24.x
Docker Compose: 2.x

스토리지:
- EBS 30GB (gp3)

네트워크:
- Elastic IP (고정 IP)
- Security Group (80, 443, 8000)
```

---

## 4. Vercel (프론트엔드 배포)

### 선택 이유

| 서비스 | 직접 호스팅 | Netlify | Vercel |
|--------|------------|---------|--------|
| 빌드 속도 | 느림 | 빠름 | **가장 빠름** |
| CDN | 별도 설정 | 자동 | **자동** |
| 프리뷰 | 직접 구현 | 자동 | **자동** |
| React 최적화 | 없음 | 기본 | **최적화** |

**Vercel**을 선택한 이유:
1. **Zero Config**: Git 연동만으로 자동 배포
2. **글로벌 CDN**: 전 세계 엣지 서버로 빠른 로딩
3. **프리뷰 배포**: PR마다 자동 프리뷰 URL 생성
4. **분석**: 웹 바이탈 모니터링 내장

### 배포 설정

```json
// vercel.json
{
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://api.sweethome.com/api/:path*" }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" }
      ]
    }
  ]
}
```

---

## 5. GitHub Actions (CI/CD)

### 선택 이유

| 서비스 | Jenkins | GitLab CI | GitHub Actions |
|--------|---------|-----------|----------------|
| 호스팅 | 자체 | 자체/클라우드 | **클라우드** |
| 설정 | 복잡 | 중간 | **간단** |
| GitHub 통합 | 플러그인 | 없음 | **네이티브** |
| 무료 한도 | 없음 | 400분/월 | **2000분/월** |

**GitHub Actions**를 선택한 이유:
1. **GitHub 네이티브**: PR 체크, 자동 머지 등 완벽 통합
2. **무료 한도**: 퍼블릭 레포 무제한, 프라이빗 2000분/월
3. **마켓플레이스**: 다양한 재사용 가능한 액션

### 적용 사례

```yaml
# .github/workflows/deploy.yml
name: Deploy to EC2

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to EC2
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ubuntu
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd /home/ubuntu/sweethome
            git pull origin main
            docker-compose up -d --build
```

---

## 6. Prometheus + Grafana (모니터링)

### 선택 이유

| 솔루션 | 자체 로깅 | ELK Stack | Prometheus+Grafana |
|--------|----------|-----------|-------------------|
| 리소스 | 최소 | 많음 | **적음** |
| 시계열 | 직접 | 지원 | **특화** |
| 알림 | 직접 | 지원 | **지원** |
| 시각화 | 없음 | Kibana | **Grafana** |

**Prometheus + Grafana**를 선택한 이유:
1. **시계열 특화**: 메트릭 수집 및 저장에 최적화
2. **경량**: ELK 대비 적은 리소스 사용
3. **FastAPI 통합**: prometheus-fastapi-instrumentator로 쉬운 통합
4. **강력한 시각화**: Grafana 대시보드로 실시간 모니터링

### 수집 메트릭

```python
# app/main.py
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

| 메트릭 | 설명 |
|--------|------|
| http_requests_total | 총 HTTP 요청 수 |
| http_request_duration_seconds | HTTP 응답 시간 |
| http_requests_in_progress | 진행 중인 요청 수 |

### Grafana 대시보드

```
대시보드 패널:
1. 초당 요청 수 (RPS)
2. 응답 시간 (p50, p95, p99)
3. HTTP 상태 코드 분포
4. 에러율 (5xx / 전체)
5. 활성 연결 수
```

---

## 📊 인프라 구성도

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        ▼                                           ▼
┌───────────────┐                           ┌───────────────┐
│    Vercel     │                           │   AWS EC2     │
│  (Frontend)   │                           │  (Backend)    │
│               │                           │               │
│  React SPA    │ ──────── API ───────────▶ │   Nginx       │
│  + CDN        │                           │     │         │
└───────────────┘                           │     ▼         │
                                            │  FastAPI      │
                                            │     │         │
                                            │     ├──▶ Redis│
                                            │     │         │
                                            │     └──▶ PostgreSQL
                                            │               │
                                            │  Prometheus   │
                                            │  Grafana      │
                                            └───────────────┘
```

---

## 📊 비용 효율

| 서비스 | 월 비용 | 설명 |
|--------|---------|------|
| AWS EC2 t4g.micro | ~$10 | 무료 티어 이후 |
| AWS EBS 30GB | ~$3 | gp3 스토리지 |
| Vercel | $0 | 무료 플랜 |
| GitHub Actions | $0 | 무료 한도 내 |
| **총계** | **~$13/월** | |
