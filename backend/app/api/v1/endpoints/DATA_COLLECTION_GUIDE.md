# 📥 데이터 수집 가이드

## 🎯 데이터 수집 순서 (필수)

데이터 수집은 **반드시 아래 순서대로** 진행해야 합니다:

```
1️⃣ 지역 데이터 수집 (필수)
   ↓
2️⃣ 아파트 목록 수집 (필수)
   ↓
3️⃣ 아파트 상세 정보 수집 (선택)
```

---

## 📋 각 데이터 수집 상세 설명

### 1️⃣ 지역 데이터 수집 (필수 - 가장 먼저!)

**엔드포인트:** `POST /api/v1/data-collection/regions`

**저장 테이블:** `states`

**수집 내용:**
- 17개 시도(서울특별시, 부산광역시 등)의 모든 지역 데이터
- 시도, 시군구, 동 단위의 지역 코드 및 이름
- `region_code` (10자리): 시도코드 2자리 + 시군구코드 3자리 + 동코드 5자리

**왜 먼저 해야 하나요?**
- 아파트 목록 수집 시 `region_id`를 참조하기 때문입니다
- 아파트의 법정동 코드(`bjd_code`)를 `states` 테이블의 `region_code`와 매칭하여 `region_id`를 찾습니다

**예상 소요 시간:** 약 5-10분 (17개 시도 × 여러 페이지)

---

### 2️⃣ 아파트 목록 수집 (필수 - 1번 이후!)

**엔드포인트:** `POST /api/v1/data-collection/apartments/list`

**저장 테이블:** `apartments`

**수집 내용:**
- 전국 모든 아파트 단지의 기본 정보
- 아파트명, 단지코드(`kapt_code`), 법정동 코드(`bjd_code`)
- `region_id` (FK): `states` 테이블 참조

**의존성:**
- ✅ **1번(지역 데이터 수집)을 먼저 완료해야 합니다!**
- 아파트의 법정동 코드로 `states` 테이블에서 `region_id`를 찾습니다
- 지역 데이터가 없으면 아파트를 저장할 수 없습니다

**매칭 로직:**
1. 전체 법정동 코드(10자리)로 찾기
2. 시군구 코드(5자리 + '00000')로 찾기
3. 시도 코드(2자리 + '00000000')로 찾기

**예상 소요 시간:** 약 10-20분 (수천 개의 아파트)

---

### 3️⃣ 아파트 상세 정보 수집 (선택 - 2번 이후!)

**엔드포인트:** `POST /api/v1/data-collection/apartments/detail`

**저장 테이블:** `apart_details`

**수집 내용:**
- 아파트 단지의 상세 정보
- 주소(도로명, 지번), 건물 정보, 시설 정보 등
- `apt_id` (FK): `apartments` 테이블 참조

**의존성:**
- ✅ **2번(아파트 목록 수집)을 먼저 완료해야 합니다!**
- `apartments` 테이블에 있는 아파트의 상세 정보만 수집합니다
- 1대1 관계이므로 각 아파트당 1개의 상세 정보만 저장됩니다

**예상 소요 시간:** 매우 오래 걸림 (각 아파트마다 API 호출)

---

## ⚠️ 주의사항

### 1. 순서를 지켜야 하는 이유

```
❌ 잘못된 순서:
   아파트 목록 수집 → 지역 데이터 수집
   → 아파트 저장 시 region_id를 찾을 수 없어서 대부분 저장 실패!

✅ 올바른 순서:
   지역 데이터 수집 → 아파트 목록 수집
   → 아파트 저장 시 region_id를 정상적으로 찾아서 저장 성공!
```

### 2. API 호출 제한

- 국토교통부 API는 호출 제한이 있을 수 있습니다
- 한 번에 너무 많은 요청을 보내지 마세요
- 코드에 자동 딜레이(0.2초)가 포함되어 있습니다

### 3. 중복 데이터 처리

- 모든 수집 API는 중복 데이터를 자동으로 건너뜁니다
- 같은 데이터를 여러 번 수집해도 안전합니다
- 하지만 불필요한 API 호출은 피하는 것이 좋습니다

---

## 🚀 실행 방법

### Swagger UI에서 실행

1. `http://localhost:8000/docs` 접속
2. `📥 Data Collection (데이터 수집)` 태그 찾기
3. 순서대로 실행:
   - `POST /api/v1/data-collection/regions` → Execute
   - `POST /api/v1/data-collection/apartments/list` → Execute
   - `POST /api/v1/data-collection/apartments/detail` → Execute (선택)

### cURL로 실행

```bash
# 1. 지역 데이터 수집
curl -X POST "http://localhost:8000/api/v1/data-collection/regions"

# 2. 아파트 목록 수집
curl -X POST "http://localhost:8000/api/v1/data-collection/apartments/list"

# 3. 아파트 상세 정보 수집 (선택)
curl -X POST "http://localhost:8000/api/v1/data-collection/apartments/detail"
```

---

## 📊 데이터베이스 구조

```
states (지역)
  ├─ region_id (PK)
  ├─ region_code (10자리)
  ├─ region_name
  └─ city_name

apartments (아파트 목록)
  ├─ apt_id (PK)
  ├─ region_id (FK → states.region_id) ⚠️ 의존성!
  ├─ apt_name
  ├─ kapt_code
  └─ is_available

apart_details (아파트 상세)
  ├─ apt_detail_id (PK)
  ├─ apt_id (FK → apartments.apt_id) ⚠️ 의존성!
  ├─ road_address
  ├─ jibun_address
  └─ ... (기타 상세 정보)
```

---

## ✅ 체크리스트

데이터 수집 전 확인사항:

- [ ] `.env` 파일에 `MOLIT_API_KEY`가 설정되어 있나요?
- [ ] Docker 백엔드가 실행 중인가요?
- [ ] 데이터베이스가 정상적으로 연결되어 있나요?

데이터 수집 순서:

- [ ] 1단계: 지역 데이터 수집 완료
- [ ] 2단계: 아파트 목록 수집 완료
- [ ] 3단계: 아파트 상세 정보 수집 완료 (선택)

---

## 🔍 문제 해결

### "법정동 코드에 해당하는 지역을 찾을 수 없습니다" 오류

**원인:** 지역 데이터가 아직 수집되지 않았거나, 해당 법정동 코드가 지역 데이터에 없습니다.

**해결:**
1. 지역 데이터 수집을 먼저 실행했는지 확인
2. 단계적 매칭 로직이 작동하므로 대부분의 경우 해결됩니다
3. 그래도 오류가 발생하면 해당 법정동 코드가 지역 데이터에 없는 것입니다

### "API 키 미설정" 오류

**원인:** `.env` 파일에 `MOLIT_API_KEY`가 없거나 잘못되었습니다.

**해결:**
1. `.env` 파일 확인
2. `MOLIT_API_KEY=your_key_here` 형식으로 설정
3. Docker 백엔드 재시작: `docker-compose restart backend`

---

## 📝 요약

| 순서 | API | 테이블 | 의존성 | 필수 여부 |
|------|-----|--------|--------|----------|
| 1 | `/regions` | `states` | 없음 | ✅ 필수 |
| 2 | `/apartments/list` | `apartments` | `states` | ✅ 필수 |
| 3 | `/apartments/detail` | `apart_details` | `apartments` | 선택 |

**핵심:** 지역 데이터 → 아파트 목록 → 아파트 상세 순서로 수집하세요!
