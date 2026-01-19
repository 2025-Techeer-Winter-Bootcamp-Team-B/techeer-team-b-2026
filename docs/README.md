# 프로젝트 문서 모음

이 폴더에는 프로젝트의 모든 문서가 카테고리별로 정리되어 있습니다.

## 문서 구조

### 📁 Backend
백엔드 개발 관련 문서
- 프로젝트 구조 및 개발 가이드
- 데이터베이스 스키마 및 초기화
- 인증 플로우
- 앱 구조 설명 (app/, core/, crud/, models/, schemas/, services/, utils/, scripts/)
- 매칭 분석 관련 문서

### 📁 Frontend
프론트엔드 개발 관련 문서
- Android Studio 설정
- 환경 설정 가이드
- 앱 실행 및 서버 재시작 가이드
- WebView 환경 확인
- 가이드라인 및 속성 정보

### 📁 Mobile
모바일 개발 관련 문서
- 디버깅 체크리스트
- 포트 확인 가이드

### 📁 Setup
환경 설정 관련 문서
- 전체 환경 변수 설정 가이드
- Clerk 인증 설정
- Docker 설정
- 환경 변수 상세 설명

### 📁 Deployment
배포 관련 문서
- Vercel 배포 가이드
- 일반 배포 가이드

### 📁 Monitoring
모니터링 관련 문서
- Prometheus & Grafana 설정
- Grafana 대시보드 가이드
- 캐시 프리로드 분석 및 요약

### 📁 Troubleshooting
문제 해결 관련 문서
- 버그 수정 요약
- 지역 상세 버그 분석
- 500 에러 디버깅
- 빠른 수정 가이드

### 📁 API
API 개발 관련 문서
- 아파트 API 가이드
- API 개발 방법
- API 라우터 가이드
- 아파트 에러 플로우

## 빠른 시작

### 개발자
1. [프로젝트 구조](./backend/01_project_structure.md) 확인
2. [개발 가이드](./backend/02_development_guide.md) 읽기
3. [환경 설정](./setup/01_environment_setup.md) 완료

### API 개발자
1. [API 개발 가이드](./api/02_api_development.md) 확인
2. [API 라우터 가이드](./api/03_api_router_guide.md) 참고
3. [아파트 API 가이드](./api/01_apartment_api_guide.md) 확인

### 배포 담당자
1. [Docker 설정](./setup/04_docker_setup.md) 확인
2. [배포 가이드](./deployment/02_deployment_guide.md) 참고
3. [모니터링 설정](./monitoring/01_monitoring_setup.md) 확인

### 문제 해결
1. [버그 수정 요약](./troubleshooting/01_fixes_summary.md) 확인
2. [빠른 수정 가이드](./troubleshooting/05_quick_fix.md) 참고
3. 관련 카테고리별 문서 확인
