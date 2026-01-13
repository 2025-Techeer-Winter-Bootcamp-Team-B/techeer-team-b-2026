# 로깅과 __init__ 메서드 설명

## 📝 logger.info는 뭐하는 거야?

### 로깅(Logging)이란?

**로깅**은 프로그램 실행 중 발생하는 이벤트(정보, 경고, 오류 등)를 기록하는 기능입니다.

### logger.info()의 역할

```python
logger.info("💰 매매 거래 데이터 수집 시작")
```

이 코드는 **정보성 메시지를 로그에 기록**합니다.

### 로깅 레벨

Python의 `logging` 모듈은 여러 레벨을 제공합니다:

| 레벨 | 메서드 | 용도 | 예시 |
|------|--------|------|------|
| **DEBUG** | `logger.debug()` | 개발 중 디버깅 정보 | 변수 값, 상세한 실행 흐름 |
| **INFO** | `logger.info()` | 일반적인 정보 메시지 | 작업 시작/완료, 진행 상황 |
| **WARNING** | `logger.warning()` | 경고 메시지 | 예상치 못한 상황, 하지만 계속 진행 가능 |
| **ERROR** | `logger.error()` | 오류 메시지 | 예외 발생, 작업 실패 |
| **CRITICAL** | `logger.critical()` | 심각한 오류 | 시스템 중단 위험 |

### 실제 사용 예시

```python
# 정보: 작업 시작
logger.info("💰 매매 거래 데이터 수집 시작: 법정동코드=11110, 계약년월=202407")

# 경고: 데이터 파싱 실패했지만 계속 진행
logger.warning("⚠️ 계약일 파싱 실패: 2024-13-32")

# 오류: API 호출 실패
logger.error("❌ API 호출 실패: Connection timeout")
```

### 로그 출력 위치

현재 설정에서는 로그가 **콘솔(터미널)**에 출력됩니다:

```python
# data_collection.py 상단
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)  # 콘솔에 출력
```

실행 시 다음과 같이 출력됩니다:
```
2026-01-11 14:30:25 | INFO | app.services.data_collection | 💰 매매 거래 데이터 수집 시작
```

### 왜 로깅을 사용하나요?

1. **디버깅**: 프로그램이 어떻게 실행되는지 추적
2. **모니터링**: 프로덕션 환경에서 문제 파악
3. **이력 관리**: 언제 무엇이 발생했는지 기록
4. **성능 분석**: 작업 소요 시간 측정

---

## 🔧 __init__은 뭐하는 거야?

### __init__ 메서드란?

`__init__`은 **클래스 인스턴스가 생성될 때 자동으로 실행되는 메서드**입니다.

### 실행 시점

```python
class DataCollectionService:
    def __init__(self):
        """서비스 초기화"""
        if not settings.MOLIT_API_KEY:
            raise ValueError("MOLIT_API_KEY가 설정되지 않았습니다.")
        self.api_key = settings.MOLIT_API_KEY  # 인스턴스 변수 설정
```

**실행 시점**: 클래스 인스턴스가 **생성될 때 한 번만** 실행됩니다.

### 실제 사용 예시

```python
# 파일 맨 아래 (data_collection.py)
data_collection_service = DataCollectionService()  # ← 여기서 __init__ 실행됨!

# 이후 모든 메서드 호출 시에는 __init__이 다시 실행되지 않음
await data_collection_service.collect_sale_transactions(...)  # __init__ 실행 안 됨
await data_collection_service.collect_all_regions(...)  # __init__ 실행 안 됨
```

### 실행 순서

```
1. 프로그램 시작
   ↓
2. data_collection.py 파일 로드
   ↓
3. DataCollectionService 클래스 정의
   ↓
4. data_collection_service = DataCollectionService()  ← __init__ 실행!
   - settings.MOLIT_API_KEY 확인
   - self.api_key 설정
   ↓
5. 이후 메서드 호출 시
   - collect_sale_transactions() 호출 → __init__ 실행 안 됨
   - collect_all_regions() 호출 → __init__ 실행 안 됨
   - 모든 메서드에서 self.api_key 사용 가능
```

### 모든 함수에 적용되는가?

**아니요!** `__init__`은:
- ✅ **인스턴스 생성 시 한 번만** 실행
- ❌ **각 메서드 호출마다 실행되지 않음**

하지만 `__init__`에서 설정한 **인스턴스 변수**(`self.api_key`)는:
- ✅ **모든 메서드에서 사용 가능**
- ✅ **인스턴스가 존재하는 동안 유지됨**

### 예시 코드

```python
class DataCollectionService:
    def __init__(self):
        print("1. __init__ 실행됨!")  # 인스턴스 생성 시 한 번만 출력
        self.api_key = "my-api-key"
    
    async def method1(self):
        print("2. method1 실행됨")
        print(f"   API 키: {self.api_key}")  # __init__에서 설정한 값 사용
    
    async def method2(self):
        print("3. method2 실행됨")
        print(f"   API 키: {self.api_key}")  # 같은 값 사용

# 사용
service = DataCollectionService()  # 출력: "1. __init__ 실행됨!"
await service.method1()  # 출력: "2. method1 실행됨", "API 키: my-api-key"
await service.method2()  # 출력: "3. method2 실행됨", "API 키: my-api-key"
# __init__은 더 이상 실행되지 않음!
```

### 왜 이렇게 설계했나요?

1. **효율성**: API 키 확인을 매번 할 필요 없음
2. **일관성**: 모든 메서드가 같은 설정을 사용
3. **초기화**: 인스턴스 생성 시 필요한 설정을 한 번에 처리

---

## 📚 요약

### logger.info()
- **역할**: 정보성 메시지를 로그에 기록
- **실행 시점**: 메서드가 호출될 때마다
- **용도**: 프로그램 실행 흐름 추적, 디버깅, 모니터링

### __init__()
- **역할**: 클래스 인스턴스 초기화
- **실행 시점**: 인스턴스 생성 시 **한 번만**
- **용도**: 인스턴스 변수 설정, 초기 검증

### 차이점

| 항목 | logger.info() | __init__() |
|------|---------------|------------|
| 실행 빈도 | 메서드 호출마다 | 인스턴스 생성 시 한 번만 |
| 목적 | 로그 기록 | 인스턴스 초기화 |
| 위치 | 메서드 내부 | 클래스 정의 내부 |
