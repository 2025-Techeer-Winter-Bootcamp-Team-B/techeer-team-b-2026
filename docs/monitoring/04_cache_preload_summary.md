# 서버 시작 시 홈 화면 캐싱 기능 구현 요약

## ✅ 구현 완료

서버 시작 시 홈 화면 지표들을 TTL 12시간으로 미리 캐싱하는 기능을 구현했습니다.

## 📋 구현 내용

### 1. 캐싱 함수 구현
- **위치**: `backend/app/api/v1/endpoints/dashboard.py`의 `preload_home_cache()` 함수
- **기능**: 서버 시작 시 홈 화면 API 데이터를 미리 캐싱

### 2. 자동 실행 설정
- **위치**: `backend/app/main.py`의 `startup_event()` 함수
- **방식**: 백그라운드 태스크로 비동기 실행 (서버 시작 블로킹 없음)

### 3. 캐싱 대상
다음 4개의 API 응답을 캐싱합니다:
1. `/api/v1/dashboard/summary?transaction_type=sale&months=6`
2. `/api/v1/dashboard/summary?transaction_type=jeonse&months=6`
3. `/api/v1/dashboard/rankings?transaction_type=sale`
4. `/api/v1/dashboard/rankings?transaction_type=jeonse`

### 4. TTL 설정
- **서버 시작 시 캐싱**: 12시간 (43200초)
- **일반 API 호출 시**: 30분 (1800초) - 기존 유지

## 🎯 장점

1. **Cold Start 문제 해결**: 서버 재시작 직후 첫 요청도 빠르게 응답
2. **사용자 경험 향상**: 홈 화면 로딩 시간 단축
3. **서버 부하 분산**: 시작 시 미리 준비하여 트래픽 급증에 대비
4. **비동기 실행**: 서버 시작 시간에 영향 없음

## 🔍 동작 방식

1. 서버 시작 시 `startup_event()` 실행
2. Redis 연결 초기화 완료 후
3. `preload_home_cache()` 함수를 백그라운드 태스크로 실행
4. 각 API 데이터를 조회하고 Redis에 캐싱 (TTL: 12시간)
5. 캐싱 완료 후 로그 기록

## 📊 로그 예시

```
🚀 [Preload Cache] 홈 화면 캐싱 시작
✅ [Preload Cache] dashboard/summary (sale, 6개월) - 캐싱 완료 (TTL: 43200초)
✅ [Preload Cache] dashboard/summary (jeonse, 6개월) - 캐싱 완료 (TTL: 43200초)
✅ [Preload Cache] dashboard/rankings (sale) - 캐싱 완료 (TTL: 43200초)
✅ [Preload Cache] dashboard/rankings (jeonse) - 캐싱 완료 (TTL: 43200초)
✅ [Preload Cache] 홈 화면 캐싱 완료 - 성공: 4개, 실패: 0개
```

## ⚠️ 주의사항

1. **에러 처리**: 캐싱 실패 시에도 서버 시작은 정상 진행
2. **중복 캐싱 방지**: 이미 캐시가 있으면 스킵
3. **데이터 없음 처리**: 데이터가 없으면 캐싱하지 않음

## 🔧 설정 변경

### TTL 변경
`backend/app/api/v1/endpoints/dashboard.py`의 `preload_home_cache()` 함수에서:

```python
PRELOAD_TTL = 43200  # 12시간 (초 단위)
```

### 캐싱 대상 추가/제거
같은 함수의 `cache_tasks` 리스트를 수정:

```python
cache_tasks = [
    ("dashboard/summary", {"transaction_type": "sale", "months": 6}),
    # 추가할 항목...
]
```

## 📚 관련 문서
- [서버 시작 시 캐싱 기능 상세 분석](./preload_cache_analysis.md)
