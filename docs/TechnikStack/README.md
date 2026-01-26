# 🛠️ 기술 스택 (Technik Stack)

SWEETHOME 프로젝트에서 사용된 기술들과 선택 이유를 설명합니다.

## 📊 기술 스택 개요

| 분류 | 기술 | 버전 | 선택 이유 |
|------|------|------|----------|
| **Frontend** | React + Vite | 18.x | 빠른 빌드, HMR 지원 |
| **Mobile** | React Native + Expo | SDK 51 | 코드 재사용, 빠른 개발 |
| **Backend** | FastAPI | 0.109+ | 비동기 지원, 자동 문서화 |
| **Database** | PostgreSQL + PostGIS | 15 | 공간 데이터, 안정성 |
| **Cache** | Redis | 7.x | 고성능 캐싱 |
| **Auth** | Clerk | - | 간편한 인증 구현 |
| **AI** | Google Gemini | 3.0 Flash | 자연어 검색 |
| **Monitoring** | Prometheus + Grafana | - | 실시간 모니터링 |
| **DevOps** | Docker + AWS EC2 | - | 컨테이너화, 클라우드 배포 |

## 📁 상세 문서

- [Frontend.md](./Frontend.md) - 프론트엔드 기술 스택
- [Backend.md](./Backend.md) - 백엔드 기술 스택
- [Database.md](./Database.md) - 데이터베이스 기술 스택
- [DevOps.md](./DevOps.md) - DevOps 및 인프라 기술 스택

## 🎯 기술 선택 원칙

### 1. 생산성 우선
- 빠른 개발 속도를 위한 도구 선택
- 학습 곡선이 완만한 기술 우선

### 2. 성능 중심
- 비동기 처리로 I/O 바운드 최적화
- 캐싱 전략으로 응답 속도 향상

### 3. 확장성 고려
- 마이크로서비스 아키텍처 대비
- 수평 확장 가능한 구조

### 4. 유지보수성
- 타입 안정성 (TypeScript, Pydantic)
- 자동 문서화 (Swagger, ReDoc)
